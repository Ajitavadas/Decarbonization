"""
Unit Normalization Service

Normalizes unit formats to match Climatiq API requirements.
Handles common unit variations and case-insensitive input.
"""

from typing import Dict, Optional


class UnitNormalizer:
    """
    Service for normalizing unit formats to Climatiq API-compatible standards.
    
    Handles common variations like:
    - kwh, KWH → kWh
    - gallons, Gallons → gal
    - miles, Miles → mi
    """
    
    # Comprehensive unit mappings (lowercase keys for case-insensitive lookup)
    UNIT_MAPPINGS: Dict[str, str] = {
        # Energy Units
        "kwh": "kWh",
        "kilowatt-hour": "kWh",
        "kilowatt hour": "kWh",
        "kilowatthour": "kWh",
        "kw-h": "kWh",
        "mwh": "MWh",
        "megawatt-hour": "MWh",
        "megawatt hour": "MWh",
        "gwh": "GWh",
        "gigawatt-hour": "GWh",
        "therm": "kWh",  # Convert to kWh (1 therm = 29.3 kWh)
        "therms": "kWh",
        "btu": "BTU",
        "btus": "BTU",
        "mmbtu": "MMBTU",
        "mmbtus": "MMBTU",
        "joule": "J",
        "joules": "J",
        "j": "J",
        "kj": "kJ",
        "kilojoule": "kJ",
        "kilojoules": "kJ",
        "mj": "MJ",
        "megajoule": "MJ",
        "megajoules": "MJ",
        
        # Volume Units
        "gallon": "gal",
        "gallons": "gal",
        "gal": "gal",
        "gals": "gal",
        "liter": "L",
        "liters": "L",
        "litre": "L",
        "litres": "L",
        "l": "L",
        "ml": "ml",
        "milliliter": "ml",
        "millilitre": "ml",
        "m3": "m³",
        "m^3": "m³",
        "cubic meter": "m³",
        "cubic metre": "m³",
        "barrel": "bbl",
        "barrels": "bbl",
        "bbl": "bbl",
        
        # Distance Units
        "mile": "mi",
        "miles": "mi",
        "mi": "mi",
        "kilometer": "km",
        "kilometers": "km",
        "kilometre": "km",
        "kilometres": "km",
        "km": "km",
        "meter": "m",
        "meters": "m",
        "metre": "m",
        "metres": "m",
        "m": "m",
        "foot": "ft",
        "feet": "ft",
        "ft": "ft",
        "yard": "yd",
        "yards": "yd",
        "yd": "yd",
        
        # Mass/Weight Units
        "kilogram": "kg",
        "kilograms": "kg",
        "kg": "kg",
        "kgs": "kg",
        "gram": "g",
        "grams": "g",
        "g": "g",
        "ton": "ton",
        "tons": "ton",
        "tonne": "tonne",
        "tonnes": "tonne",
        "metric ton": "tonne",
        "metric tons": "tonne",
        "mt": "tonne",
        "pound": "lb",
        "pounds": "lb",
        "lb": "lb",
        "lbs": "lb",
        "ounce": "oz",
        "ounces": "oz",
        "oz": "oz",
        
        # Currency Units (for spend-based calculations - use lowercase for Climatiq compatibility)
        "usd": "usd",
        "dollar": "usd",
        "dollars": "usd",
        "$": "usd",
        "eur": "eur",
        "euro": "eur",
        "euros": "eur",
        "€": "eur",
        "gbp": "gbp",
        "pound sterling": "gbp",
        "£": "gbp",
        
        # Time Units
        "hour": "h",
        "hours": "h",
        "h": "h",
        "hr": "h",
        "hrs": "h",
        "day": "d",
        "days": "d",
        "d": "d",
        "year": "yr",
        "years": "yr",
        "yr": "yr",
        "month": "month",
        "months": "month",
        
        # Area Units
        "square meter": "m²",
        "square meters": "m²",
        "square metre": "m²",
        "square metres": "m²",
        "m2": "m²",
        "m^2": "m²",
        "square foot": "ft²",
        "square feet": "ft²",
        "sq ft": "ft²",
        "sqft": "ft²",
        "ft2": "ft²",
        "ft^2": "ft²",
        "acre": "acre",
        "acres": "acre",
        "hectare": "ha",
        "hectares": "ha",
        "ha": "ha",
    }
    
    def __init__(self):
        """Initialize the unit normalizer."""
        pass
    
    def normalize(self, unit: str) -> str:
        """
        Normalize a unit string to Climatiq API-compatible format.
        
        Args:
            unit: Raw unit string from user input (e.g., "kwh", "Gallons", "MILES")
            
        Returns:
            Normalized unit string (e.g., "kWh", "gal", "mi")
            If unit is not found in mappings, returns original unit unchanged.
            
        Examples:
            >>> normalizer = UnitNormalizer()
            >>> normalizer.normalize("kwh")
            'kWh'
            >>> normalizer.normalize("Gallons")
            'gal'
            >>> normalizer.normalize("MILES")
            'mi'
            >>> normalizer.normalize("kWh")  # Already correct
            'kWh'
        """
        if not unit or not isinstance(unit, str):
            return unit
        
        # Strip whitespace
        unit = unit.strip()
        
        if not unit:
            return unit
        
        # Try case-insensitive lookup
        normalized = self.UNIT_MAPPINGS.get(unit.lower())
        
        if normalized:
            return normalized
        
        # If not found, return original (might already be correct)
        return unit
    
    def normalize_batch(self, units: list) -> list:
        """
        Normalize a list of units.
        
        Args:
            units: List of unit strings
            
        Returns:
            List of normalized unit strings
        """
        return [self.normalize(unit) for unit in units]
    
    def is_valid_climatiq_unit(self, unit: str) -> bool:
        """
        Check if a unit is in the valid Climatiq format.
        
        Args:
            unit: Unit string to check
            
        Returns:
            True if unit matches a known Climatiq format
        """
        # Check if it's in our normalized values
        return unit in self.UNIT_MAPPINGS.values()


# Singleton instance
unit_normalizer = UnitNormalizer()
