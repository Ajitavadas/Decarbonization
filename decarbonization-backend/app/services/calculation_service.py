"""
CO2e Calculation Service - CO2e calculation engine
Handles emission factor matching and calculation
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class CalculationService:
    """Service for CO2e calculations (US-2.2)"""
    
    # Unit conversion factors to standard units
    UNIT_CONVERSIONS = {
        # Energy
        "kwh": 1.0,
        "mwh": 1000.0,
        "gwh": 1000000.0,
        "kj": 0.000277778,
        "mj": 0.277778,
        "gj": 277.778,
        "btu": 0.000293071,
        "therm": 29.3071,
        "therms": 29.3071,  # Added plural
        
        # Volume - Liquids
        "liter": 1.0,
        "litre": 1.0,
        "liters": 1.0,  # Added plural
        "l": 1.0,
        "gallon": 3.78541,
        "gal": 3.78541,
        "gallons": 3.78541,  # Added plural
        "m3": 1000.0,
        
        # Mass
        "kg": 1.0,
        "kilogram": 1.0,
        "gram": 0.001,
        "g": 0.001,
        "tonne": 1000.0,
        "tonnes": 1000.0,  # Added plural
        "ton": 907.185,
        "tons": 907.185,  # Added plural
        "lb": 0.453592,
        "pound": 0.453592,
        
        # Distance
        "km": 1.0,
        "kilometer": 1.0,
        "mile": 1.60934,
        "mi": 1.60934,
        "miles": 1.60934, # Added plural
        "meter": 0.001,
        "m": 0.001,
        
        # Special
        "night": 1.0,
        "nights": 1.0,
        "unit": 1.0,
        "passenger-km": 1.0,
    }
    
    @staticmethod
    def calculate_co2e(
        activity_value: float,
        emission_factor: float,
        activity_unit: str = "kwh",
        precision: int = 3
    ) -> Tuple[float, float, Dict]:
        """
        Calculate CO2e emissions with audit trail
        
        Formula: CO2e = activity_value × emission_factor
        
        AC:
        - Accurate to 3 decimal places
        - Audit trail shows source factor
        - Handles edge cases
        
        Returns:
            (co2e_kg, co2e_tonnes, audit_info)
        """
        try:
            # Normalize unit for conversion lookup
            unit_normalized = activity_unit.lower().strip()
            
            # Apply unit conversion if needed
            conversion_factor = CalculationService.UNIT_CONVERSIONS.get(
                unit_normalized, 1.0
            )
            
            # Calculate with Decimal for precision
            activity_decimal = Decimal(str(activity_value)) * Decimal(str(conversion_factor))
            factor_decimal = Decimal(str(emission_factor))
            co2e_kg_decimal = activity_decimal * factor_decimal
            
            # Round to specified precision
            co2e_kg = float(co2e_kg_decimal.quantize(
                Decimal(10) ** -precision,
                rounding=ROUND_HALF_UP
            ))
            co2e_tonnes = round(co2e_kg / 1000, precision + 3)
            
            # Audit trail
            audit_info = {
                "original_activity_value": activity_value,
                "original_activity_unit": activity_unit,
                "conversion_factor": float(conversion_factor),
                "normalized_activity_value": float(activity_decimal),
                "emission_factor": emission_factor,
                "co2e_kg": co2e_kg,
                "co2e_tonnes": co2e_tonnes,
                "calculation_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return co2e_kg, co2e_tonnes, audit_info
            
        except (ValueError, TypeError, ArithmeticError) as e:
            logger.error(f"Calculation error: {str(e)}")
            raise ValueError(f"Invalid calculation inputs: {str(e)}")
    
    @staticmethod
    def batch_calculate(
        transactions: List[Dict],
        precision: int = 3
    ) -> List[Dict]:
        """
        Batch process 1000+ transactions per minute
        
        AC: Process 1,000+ transactions per minute
        """
        results = []
        for tx in transactions:
            try:
                co2e_kg, co2e_tonnes, audit_info = CalculationService.calculate_co2e(
                    activity_value=tx["activity_value"],
                    emission_factor=tx["emission_factor"],
                    activity_unit=tx.get("activity_unit", "kwh"),
                    precision=precision
                )
                results.append({
                    **tx,
                    "co2e_kg": co2e_kg,
                    "co2e_tonnes": co2e_tonnes,
                    "audit_info": audit_info,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    **tx,
                    "status": "error",
                    "error": str(e)
                })
        
        return results

    @staticmethod
    def convert_to_base_unit(value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert value from one unit to another using internal conversion table.
        Standardizes on:
        - Energy: kwh
        - Mass: kg
        - Volume: liter
        - Distance: km
        """
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()
        
        if from_unit == to_unit:
            return value

        # Direct conversion if to_unit is base unit (factor=1.0 in table)
        # However, our table is normalized to base unit = 1.0. 
        # So to convert FROM 'kj' TO 'mj': 
        # val_in_base = val * factor_from
        # result = val_in_base / factor_to
        
        factor_from = CalculationService.UNIT_CONVERSIONS.get(from_unit)
        factor_to = CalculationService.UNIT_CONVERSIONS.get(to_unit)
        
        if not factor_from or not factor_to:
             raise ValueError(f"Unsupported unit conversion: {from_unit} -> {to_unit}")
             
        # Convert to base, then to target
        value_base = value * factor_from
        return value_base / factor_to

    @staticmethod
    async def calculate_emissions(
        db: AsyncSession, 
        event: "StandardizedEmissionEvent"
    ) -> "EmissionResult":
        """
        Calculate emissions for a standardized event (US-3.1)
        Hybrid Logic: Use latest data (Local vs Climatiq)
        """
        from app.schemas.emissions import EmissionResult
        from app.services.emission_factor_service import EmissionFactorService
        from app.services.climatiq_service import ClimatiqService, ClimatiqEstimateRequest, ClimatiqEmissionFactor
        
        climatiq_svc = ClimatiqService()
        
        # 1. Look for local factor
        local_factor = None
        if event.activity_id:
            local_factor = await EmissionFactorService.get_latest_factor_by_activity_id(
                db, event.activity_id
            )
            
        # 2. Check Climatiq for updates (simplification: always check metadata if activity_id exists)
        # In a real system, we might cache this or check periodically.
        climatiq_metadata = None
        use_climatiq = False
        
        if event.activity_id:
            try:
                climatiq_metadata = await climatiq_svc.get_activity_id_metadata(event.activity_id)
                if climatiq_metadata:
                    # Logic: use Climatiq if local factor is missing or if Climatiq has a newer year/version
                    if not local_factor:
                        use_climatiq = True
                    else:
                        # Compare years (master logic: latest year wins)
                        climatiq_year = climatiq_metadata.get("year", 0)
                        local_year = local_factor.year or 0
                        if climatiq_year > local_year:
                           use_climatiq = True
                        elif climatiq_year == local_year:
                            # If years are same, check data_version if available
                            climatiq_ver = climatiq_metadata.get("data_version", "")
                            local_ver = local_factor.data_version or ""
                            if climatiq_ver > local_ver:
                                use_climatiq = True
            except Exception as e:
                logger.warning(f"Failed to check Climatiq metadata for {event.activity_id}: {str(e)}")

        # 3. Perform calculation
        if use_climatiq and climatiq_metadata:
            # Perform calculation using Climatiq API
            try:
                param_name = CalculationService._get_climatiq_param_name(event.activity_type)
                estimate_req = ClimatiqEstimateRequest(
                    emission_factor=ClimatiqEmissionFactor(
                        activity_id=event.activity_id,
                        id=climatiq_metadata.get("id")
                    ),
                    parameters={
                        param_name: event.activity_value,
                        f"{param_name}_unit": event.activity_unit.lower()
                    }
                )
                climatiq_resp = await climatiq_svc.estimate(estimate_req)
                
                return EmissionResult(
                    location_based_co2e_kg=climatiq_resp.co2e,
                    market_based_co2e_kg=climatiq_resp.co2e, # Default fallback
                    factor_used={
                        "activity_id": event.activity_id,
                        "climatiq_id": climatiq_metadata.get("id"),
                        "source": climatiq_resp.emission_factor.get("source"),
                        "year": climatiq_metadata.get("year")
                    },
                    calculation_method="climatiq_api_latest"
                )
            except Exception as e:
                logger.error(f"Climatiq calculation failed: {str(e)}")
                # If Climatiq fails, try to fall back to local if available
                if not local_factor:
                    raise

        # 4. Fallback/Default to local calculation
        if not local_factor:
            # Mock factor if none found (as in original code)
            factor_val = 0.5
            factor_info = {"name": "Mock Grid Average", "source": "Mock DB", "denominator": "kwh"}
        else:
            factor_val = local_factor.factor_value
            factor_info = {
                "name": local_factor.name, 
                "source": local_factor.source,
                "denominator": local_factor.factor_unit.split("/")[-1].lower() if "/" in local_factor.factor_unit else "kwh"
            }

        # Original calculation logic
        try:
           converted_activity = CalculationService.convert_to_base_unit(
               event.activity_value, 
               event.activity_unit, 
               factor_info["denominator"]
           )
        except ValueError:
            logger.warning(f"Unit conversion failed for {event.activity_unit} -> {factor_info['denominator']}")
            raise

        location_co2e_kg = converted_activity * factor_val
        market_co2e_kg = 0.0 if event.market_instruments else location_co2e_kg

        return EmissionResult(
            location_based_co2e_kg=round(location_co2e_kg, 4),
            market_based_co2e_kg=round(market_co2e_kg, 4),
            factor_used=factor_info,
            calculation_method="local_db_latest" if local_factor else "standard_factor_mock"
        )

    @staticmethod
    def _get_climatiq_param_name(activity_type: str) -> str:
        """Map internal activity types to Climatiq parameter names"""
        mapping = {
            "electricity": "energy",
            "natural_gas": "energy",
            "diesel": "volume",
            "purchased_goods": "money",
            "refrigerant": "weight"
        }
        return mapping.get(activity_type, "energy")