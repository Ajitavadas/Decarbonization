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
    async def calculate_emissions(event: "StandardizedEmissionEvent") -> "EmissionResult":
        """
        Calculate emissions for a standardized event (US-3.1)
        
        Logic:
        1. Determine Factor (Mocked for now - always 0.5 kgCO2e/kWh for electricity)
        2. Convert Activity to Factor Unit
        3. Calculate Location-Based
        4. Calculate Market-Based (Dual Reporting)
        """
        from app.schemas.emissions import EmissionResult
        
        # 1. MOCK: Get Factor
        # Real logic would use EmissionFactorService.match(event)
        # For now, hardcoded mock
        mock_factor = {
            "value": 0.5, # kgCO2e / kWh (mock)
            "unit": "kg",
            "denominator": "kwh",
            "name": "Mock Grid Average",
            "source": "Mock DB"
        }
        
        # 2. Convert Activity
        # Target unit is the factor's denominator
        try:
           converted_activity = CalculationService.convert_to_base_unit(
               event.activity_value, 
               event.activity_unit, 
               mock_factor["denominator"]
           )
        except ValueError:
            # Fallback if conversion fails (e.g. unknown unit), just treat as 1:1 for MVP if compatible
            # Or raise error. Let's log and re-raise for robustness
            logger.warning(f"Unit conversion failed for {event.activity_unit} -> {mock_factor['denominator']}")
            raise

        # 3. Location-Based Calculation
        location_co2e_kg = converted_activity * mock_factor["value"]
        
        # 4. Market-Based Calculation
        # Rule: If market instruments (RECs) exist, market_based = 0 (assuming 100% matched for MVP logic)
        # Otherwise, falls back to location-based (Grid Mix)
        if event.market_instruments:
             market_co2e_kg = 0.0
        else:
             market_co2e_kg = location_co2e_kg

        return EmissionResult(
            location_based_co2e_kg=round(location_co2e_kg, 4),
            market_based_co2e_kg=round(market_co2e_kg, 4),
            factor_used=mock_factor,
            calculation_method="standard_factor_mock"
        )