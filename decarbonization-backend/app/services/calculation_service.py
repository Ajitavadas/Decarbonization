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
        
        # Volume - Liquids
        "liter": 1.0,
        "litre": 1.0,
        "l": 1.0,
        "gallon": 3.78541,
        "gal": 3.78541,
        "m3": 1000.0,
        
        # Mass
        "kg": 1.0,
        "kilogram": 1.0,
        "gram": 0.001,
        "g": 0.001,
        "tonne": 1000.0,
        "ton": 907.185,
        "lb": 0.453592,
        "pound": 0.453592,
        
        # Distance
        "km": 1.0,
        "kilometer": 1.0,
        "mile": 1.60934,
        "mi": 1.60934,
        "meter": 0.001,
        "m": 0.001,
        
        # Special
        "night": 1.0,
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