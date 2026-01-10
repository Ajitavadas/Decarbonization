"""
Emission Archetype Configuration
Defines the 7 emission archetypes and their expected fingerprints for audit validation

Universal Industry Taxonomy:
1. The Digital Service - Tech, Finance, SaaS
2. The Material Transformer - Manufacturing, Pharma, Textiles
3. The Structure Builder - Construction, Real Estate
4. The Mover - Logistics, Airlines, Shipping
5. The Land Steward - Agriculture, Forestry, Food & Beverage
6. The Energy Producer - Utilities, Oil & Gas, Mining
7. The Retailer - Retail, E-commerce, Hospitality
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ArchetypeFingerprint:
    """Expected emission patterns for an archetype"""
    name: str
    display_name: str
    corresponding_industries: List[str]
    expected_activity_types: List[str]
    expected_scopes: List[str]
    scope_distribution: Dict[str, float]  # Expected % distribution
    key_emission_signals: List[str]
    seasonal_patterns: Optional[Dict[str, List[int]]]  # month numbers for expected peaks
    thresholds: Dict[str, float]  # Domain-specific thresholds


# Main archetype configuration
ARCHETYPE_FINGERPRINTS: Dict[str, ArchetypeFingerprint] = {
    "digital_service": ArchetypeFingerprint(
        name="digital_service",
        display_name="The Digital Service",
        corresponding_industries=["Technology", "Finance", "Insurance", "SaaS", "Software", "Banking"],
        expected_activity_types=["procurement", "business_travel", "electricity", "employee_commuting"],
        expected_scopes=["Scope 2", "Scope 3"],
        scope_distribution={"Scope 1": 0.05, "Scope 2": 0.25, "Scope 3": 0.70},
        key_emission_signals=["cloud_services", "employee_laptops", "business_travel", "office_leases"],
        seasonal_patterns=None,  # No strong seasonality
        thresholds={
            "max_scope1_ratio": 0.15,  # Alert if Scope 1 > 15%
            "min_scope3_ratio": 0.50,  # Alert if Scope 3 < 50%
            "electricity_intensity_kwh_per_employee": 5000,  # Annual baseline
        }
    ),
    
    "material_transformer": ArchetypeFingerprint(
        name="material_transformer",
        display_name="The Material Transformer",
        corresponding_industries=["Manufacturing", "Pharmaceuticals", "Textiles", "Chemicals", "Industrial"],
        expected_activity_types=["stationary_combustion", "electricity", "procurement", "fuel"],
        expected_scopes=["Scope 1", "Scope 2", "Scope 3"],
        scope_distribution={"Scope 1": 0.40, "Scope 2": 0.20, "Scope 3": 0.40},
        key_emission_signals=["natural_gas", "diesel", "raw_materials", "process_heat"],
        seasonal_patterns=None,
        thresholds={
            "min_scope1_ratio": 0.20,  # Alert if Scope 1 < 20%
            "max_electricity_only_ratio": 0.60,  # Alert if electricity is > 60% of total
        }
    ),
    
    "structure_builder": ArchetypeFingerprint(
        name="structure_builder",
        display_name="The Structure Builder",
        corresponding_industries=["Construction", "Real Estate Development", "Infrastructure", "Architecture"],
        expected_activity_types=["stationary_combustion", "fuel", "procurement", "electricity"],
        expected_scopes=["Scope 1", "Scope 2", "Scope 3"],
        scope_distribution={"Scope 1": 0.30, "Scope 2": 0.10, "Scope 3": 0.60},
        key_emission_signals=["concrete", "steel", "heavy_machinery", "demolition_waste"],
        seasonal_patterns={"construction_peak": [4, 5, 6, 7, 8, 9]},  # Spring-Fall peak
        thresholds={
            "min_scope3_ratio": 0.40,  # Embodied carbon should be significant
        }
    ),
    
    "mover": ArchetypeFingerprint(
        name="mover",
        display_name="The Mover",
        corresponding_industries=["Logistics", "Airlines", "Shipping", "Transportation", "Freight", "Delivery"],
        expected_activity_types=["fuel", "stationary_combustion", "business_travel", "transportation"],
        expected_scopes=["Scope 1", "Scope 3"],
        scope_distribution={"Scope 1": 0.70, "Scope 2": 0.05, "Scope 3": 0.25},
        key_emission_signals=["jet_fuel", "marine_diesel", "fleet_vehicles", "diesel"],
        seasonal_patterns={"holiday_peak": [11, 12]},  # Holiday shipping peak
        thresholds={
            "min_scope1_ratio": 0.50,  # Mobile combustion should dominate
            "min_fuel_activities": 1,  # Must have fuel consumption
        }
    ),
    
    "land_steward": ArchetypeFingerprint(
        name="land_steward",
        display_name="The Land Steward",
        corresponding_industries=["Agriculture", "Forestry", "Food & Beverage", "Farming", "Livestock"],
        expected_activity_types=["stationary_combustion", "fuel", "procurement", "electricity"],
        expected_scopes=["Scope 1", "Scope 2", "Scope 3"],
        scope_distribution={"Scope 1": 0.50, "Scope 2": 0.10, "Scope 3": 0.40},
        key_emission_signals=["fertilizer", "livestock", "land_use", "irrigation"],
        seasonal_patterns={"growing_season": [4, 5, 6, 7, 8, 9], "harvest": [9, 10, 11]},
        thresholds={
            "min_scope1_ratio": 0.30,  # N2O and CH4 emissions
        }
    ),
    
    "energy_producer": ArchetypeFingerprint(
        name="energy_producer",
        display_name="The Energy Producer",
        corresponding_industries=["Utilities", "Oil & Gas", "Mining", "Power Generation", "Renewable Energy"],
        expected_activity_types=["stationary_combustion", "fuel", "electricity"],
        expected_scopes=["Scope 1", "Scope 2"],
        scope_distribution={"Scope 1": 0.85, "Scope 2": 0.05, "Scope 3": 0.10},
        key_emission_signals=["fugitive_emissions", "methane", "extraction", "combustion"],
        seasonal_patterns={"winter_peak": [12, 1, 2], "summer_peak": [6, 7, 8]},  # Heating/cooling demand
        thresholds={
            "min_scope1_ratio": 0.70,  # Direct emissions should dominate
        }
    ),
    
    "retailer": ArchetypeFingerprint(
        name="retailer",
        display_name="The Retailer",
        corresponding_industries=["Retail", "E-commerce", "Hospitality", "Food Service", "Consumer Goods"],
        expected_activity_types=["electricity", "procurement", "business_travel", "transportation"],
        expected_scopes=["Scope 2", "Scope 3"],
        scope_distribution={"Scope 1": 0.10, "Scope 2": 0.30, "Scope 3": 0.60},
        key_emission_signals=["warehousing", "store_electricity", "packaging", "logistics"],
        seasonal_patterns={"holiday_peak": [11, 12]},  # Holiday retail peak
        thresholds={
            "min_scope3_ratio": 0.40,  # Supply chain emissions significant
        }
    ),
}


def get_archetype(archetype_name: str) -> Optional[ArchetypeFingerprint]:
    """Get archetype configuration by name"""
    return ARCHETYPE_FINGERPRINTS.get(archetype_name)


def infer_archetype_from_industry(industry: str) -> Optional[str]:
    """Attempt to infer archetype from industry string"""
    if not industry:
        return None
    
    industry_lower = industry.lower()
    
    for archetype_name, fingerprint in ARCHETYPE_FINGERPRINTS.items():
        for ind in fingerprint.corresponding_industries:
            if ind.lower() in industry_lower or industry_lower in ind.lower():
                return archetype_name
    
    return None


def get_all_archetypes() -> List[str]:
    """Get list of all available archetype names"""
    return list(ARCHETYPE_FINGERPRINTS.keys())
