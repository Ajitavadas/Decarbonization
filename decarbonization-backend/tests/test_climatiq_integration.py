import pytest
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from app.services.calculation_service import CalculationService
from app.schemas.emissions import StandardizedEmissionEvent, LocationData, DataQuality
from app.models.models import EmissionFactor

@pytest.mark.asyncio
async def test_hybrid_calculation_prefer_climatiq_newer():
    # Mock DB session
    db = AsyncMock()
    
    # Setup local factor (older: 2022)
    local_factor = EmissionFactor(
        activity_id="elec-123",
        year=2022,
        data_version="1.0",
        factor_value=0.5,
        factor_unit="kg/kwh",
        name="Local Elec",
        source="Local DB",
        is_active=True
    )
    
    # Mock EmissionFactorService
    with patch("app.services.emission_factor_service.EmissionFactorService.get_latest_factor_by_activity_id", new_callable=AsyncMock) as mock_get_local:
        mock_get_local.return_value = local_factor
        
        # Mock ClimatiqService metadata (newer: 2024)
        with patch("app.services.climatiq_service.ClimatiqService.get_activity_id_metadata", new_callable=AsyncMock) as mock_get_meta:
            mock_get_meta.return_value = {
                "id": "climatiq-uuid-newer",
                "year": 2024,
                "data_version": "2.0"
            }
            
            # Mock ClimatiqService estimate
            with patch("app.services.climatiq_service.ClimatiqService.estimate", new_callable=AsyncMock) as mock_estimate:
                mock_estimate.return_value = MagicMock(
                    co2e=0.45,
                    emission_factor={"source": "Climatiq API"}
                )
                
                # Input event
                event = StandardizedEmissionEvent(
                    event_id="test-event",
                    org_id="test-org",
                    timestamp=datetime.now(timezone.utc),
                    activity_type="electricity",
                    activity_value=1.0, # 1 kWh
                    activity_unit="kWh",
                    activity_id="elec-123",
                    location=LocationData(),
                    data_quality=DataQuality(source_type="user_entry", confidence_score=1.0)
                )
                
                result = await CalculationService.calculate_emissions(db, event)
                
                assert result.location_based_co2e_kg == 0.45
                assert result.calculation_method == "climatiq_api_latest"
                assert result.factor_used["climatiq_id"] == "climatiq-uuid-newer"

@pytest.mark.asyncio
async def test_hybrid_calculation_prefer_local_newer():
    # Mock DB session
    db = AsyncMock()
    
    # Setup local factor (newer: 2025)
    local_factor = EmissionFactor(
        activity_id="elec-123",
        year=2025,
        data_version="3.0",
        factor_value=0.3,
        factor_unit="kg/kwh",
        name="Local Elec",
        source="Local DB",
        is_active=True
    )
    
    # Mock EmissionFactorService
    with patch("app.services.emission_factor_service.EmissionFactorService.get_latest_factor_by_activity_id", new_callable=AsyncMock) as mock_get_local:
        mock_get_local.return_value = local_factor
        
        # Mock ClimatiqService metadata (older: 2024)
        with patch("app.services.climatiq_service.ClimatiqService.get_activity_id_metadata", new_callable=AsyncMock) as mock_get_meta:
            mock_get_meta.return_value = {
                "id": "climatiq-uuid-older",
                "year": 2024,
                "data_version": "2.0"
            }
            
            # Input event
            event = StandardizedEmissionEvent(
                event_id="test-event",
                org_id="test-org",
                timestamp=datetime.now(timezone.utc),
                activity_type="electricity",
                activity_value=10.0,
                activity_unit="kWh",
                activity_id="elec-123",
                location=LocationData(),
                data_quality=DataQuality(source_type="user_entry", confidence_score=1.0)
            )
            
            result = await CalculationService.calculate_emissions(db, event)
            
            # 10 kWh * 0.3 factor = 3.0 kg
            assert result.location_based_co2e_kg == 3.0
            assert result.calculation_method == "local_db_latest"
            assert result.factor_used["name"] == "Local Elec"
