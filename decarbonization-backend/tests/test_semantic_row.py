
import asyncio
import logging
from app.services.semantic_adapter_service import semantic_adapter
from app.schemas.emissions import StandardizedEmissionEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_normalize_row():
    logger.info("Starting Semantic Row Normalization Test...")

    # Test Case 1: Dirty Diesel
    row1 = {
        "Fuel": "Red Diesel",
        "Qty": "1,000.5 gal",
        "Date": "2023-10-05"
    }
    logger.info(f"Testing Row 1: {row1}")
    result1 = await semantic_adapter.normalize_row(row1)
    
    if result1:
        logger.info(f"Result 1: {result1.dict()}")
        assert isinstance(result1, StandardizedEmissionEvent)
        assert result1.activity_type == "diesel"
        assert result1.activity_unit == "gallons"
        assert result1.activity_value == 1000.5
        print("✅ Test Case 1 Passed: Red Diesel -> diesel, 1,000.5 gal -> 1000.5 gallons")
    else:
        print("❌ Test Case 1 Failed: Returned None")

    # Test Case 2: Natural Gas with messy unit
    row2 = {
        "Description": "Heating Gas usage for office",
        "Consumption": "500 therms (approx)",
        "When": "Nov 2023"
    }
    logger.info(f"Testing Row 2: {row2}")
    result2 = await semantic_adapter.normalize_row(row2)
    
    if result2:
        logger.info(f"Result 2: {result2.dict()}")
        assert result2.activity_type == "natural_gas"
        assert result2.activity_unit == "therms"
        assert result2.activity_value == 500.0
        print("✅ Test Case 2 Passed: Heating Gas -> natural_gas, 500 therms")
    else:
        print("❌ Test Case 2 Failed: Returned None")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_normalize_row())
