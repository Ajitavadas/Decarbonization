import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from pprint import pprint

from app.schemas.emissions import StandardizedEmissionEvent, MarketInstrument, LocationData, DataQuality
from app.services.calculation_service import CalculationService

async def main():
    print("=== Testing Calculation Engine (Agent 3) ===")

    # Test Case 1: Electricity with Location-Based only (Grid Mix)
    event_grid = StandardizedEmissionEvent(
        event_id=uuid4(),
        org_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        activity_type="electricity",
        activity_value=1000,
        activity_unit="kWh",  # Matches mock factor denominator
        location=LocationData(),
        data_quality=DataQuality(source_type="user_entry", confidence_score=1.0)
    )

    print("\n--- Test Case 1: Electricity (Grid Mix) ---")
    result_grid = await CalculationService.calculate_emissions(event_grid)
    pprint(result_grid.model_dump())
    
    # Expected: Location = 500 (1000 * 0.5), Market = 500 (fallback)
    assert result_grid.location_based_co2e_kg == 500.0
    assert result_grid.market_based_co2e_kg == 500.0
    print("✅ Passed")


    # Test Case 2: Electricity with Market Instruments (REC)
    event_rec = StandardizedEmissionEvent(
        event_id=uuid4(),
        org_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        activity_type="electricity",
        activity_value=1000,
        activity_unit="kWh", 
        location=LocationData(),
        data_quality=DataQuality(source_type="user_entry", confidence_score=1.0),
        market_instruments=[MarketInstrument(type="REC", volume_matched=1000)]
    )

    print("\n--- Test Case 2: Electricity (with REC) ---")
    result_rec = await CalculationService.calculate_emissions(event_rec)
    pprint(result_rec.dict())

    # Expected: Location = 500, Market = 0
    assert result_rec.location_based_co2e_kg == 500.0
    assert result_rec.market_based_co2e_kg == 0.0
    print("✅ Passed")
    

    # Test Case 3: Unit Conversion (Therms -> kWh)
    # 1 Therm approx 29.3071 kWh
    # 10 Therms = 293.071 kWh
    # Emissions = 293.071 * 0.5 = 146.5355 kg
    event_therms = StandardizedEmissionEvent(
        event_id=uuid4(),
        org_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        activity_type="natural_gas", 
        activity_value=10,
        activity_unit="therms", 
        location=LocationData(),
        data_quality=DataQuality(source_type="user_entry", confidence_score=1.0)
    )

    print("\n--- Test Case 3: Unit Conversion (Therms -> kWh) ---")
    result_therms = await CalculationService.calculate_emissions(event_therms)
    pprint(result_therms.dict())
    
    # 10 Therms * 29.3071 (conversion) * 0.5 (factor) = 146.5355
    # Allowing small float tolerance
    assert 146.5 < result_therms.location_based_co2e_kg < 146.6
    print("✅ Passed")
    
    print("\n=== All Tests Passed ===")

if __name__ == "__main__":
    asyncio.run(main())
