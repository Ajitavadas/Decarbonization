"""
RegionalFactor model - Country/Region-specific regulatory and grid factors
Dynamic table for regional context injection into AI prompts
"""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base


class RegionalFactor(Base):
    """
    Country/Region-specific factors for AI context injection
    
    Stores:
    - Grid emission factors (kgCO2e/kWh)
    - Regulatory frameworks and incentives
    - Benchmark data per industry/archetype
    - Carbon pricing information
    """
    
    __tablename__ = "regional_factors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Region identification
    country_code = Column(String(2), nullable=False, index=True)  # ISO 3166-1 Alpha-2
    region_code = Column(String(10), nullable=True, index=True)  # Sub-national region (optional)
    region_name = Column(String(100), nullable=True)  # Human-readable name
    
    # Grid emission factors
    grid_ef_kwh = Column(Numeric(10, 6), nullable=True)  # kgCO2e per kWh
    grid_ef_source = Column(String(100), nullable=True)  # Source (e.g., "IEA 2024", "EPA eGRID")
    grid_ef_year = Column(String(4), nullable=True)  # Data year
    
    # Regulatory context (JSONB for flexibility)
    # Example: {"name": "PAT Scheme", "description": "Perform Achieve Trade", "incentive_type": "trading"}
    regulations = Column(JSONB, default=[])
    
    # Incentives and subsidies
    # Example: {"name": "Solar Rooftop Subsidy", "value_pct": 40, "eligibility": "commercial"}
    incentives = Column(JSONB, default=[])
    
    # Carbon pricing
    carbon_price_usd = Column(Numeric(10, 2), nullable=True)  # USD per tonne CO2e
    carbon_pricing_scheme = Column(String(100), nullable=True)  # e.g., "EU ETS", "India PAT"
    
    # Archetype-specific benchmarks
    # Example: {"digital_service": {"intensity_kg_per_employee": 2500}, "mover": {"intensity_kg_per_km": 0.15}}
    archetype_benchmarks = Column(JSONB, default={})
    
    # Metadata
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<RegionalFactor {self.country_code} - {self.region_name or 'National'}>"
    
    def to_ai_context(self, archetype: str = None) -> dict:
        """
        Convert to AI-ready context dictionary
        
        Args:
            archetype: Optional archetype to include specific benchmarks
            
        Returns:
            Dict with regional context for AI prompts
        """
        context = {
            "country_code": self.country_code,
            "region_name": self.region_name or f"{self.country_code} National",
            "grid_ef_kwh": float(self.grid_ef_kwh) if self.grid_ef_kwh else None,
            "grid_ef_source": self.grid_ef_source,
            "regulations": self.regulations or [],
            "incentives": self.incentives or [],
            "carbon_price_usd": float(self.carbon_price_usd) if self.carbon_price_usd else None,
            "carbon_pricing_scheme": self.carbon_pricing_scheme,
        }
        
        # Add archetype-specific benchmark if available
        if archetype and self.archetype_benchmarks:
            context["archetype_benchmark"] = self.archetype_benchmarks.get(archetype, {})
        
        return context


# Default regional factors for seeding
DEFAULT_REGIONAL_FACTORS = [
    {
        "country_code": "IN",
        "region_name": "India National",
        "grid_ef_kwh": 0.708,  # India grid average 2023
        "grid_ef_source": "CEA India 2023",
        "grid_ef_year": "2023",
        "regulations": [
            {"name": "BRSR", "description": "Business Responsibility and Sustainability Reporting", "mandatory": True},
            {"name": "PAT Scheme", "description": "Perform Achieve and Trade for industrial efficiency", "incentive_type": "trading"},
            {"name": "Green Open Access", "description": "Access to renewable energy from the grid", "incentive_type": "regulatory"},
        ],
        "incentives": [
            {"name": "Solar Rooftop Subsidy", "description": "40% subsidy for residential, 20% for commercial", "value_pct": 20, "eligibility": "commercial"},
            {"name": "Accelerated Depreciation", "description": "40% depreciation on solar assets", "value_pct": 40, "eligibility": "commercial"},
            {"name": "Net Metering", "description": "Sell excess solar power to grid", "incentive_type": "tariff"},
        ],
        "archetype_benchmarks": {
            "digital_service": {"intensity_kg_per_employee": 2800, "benchmark_source": "CDP India 2023"},
            "material_transformer": {"intensity_kg_per_unit": 0.45, "benchmark_source": "BEE India 2023"},
            "mover": {"intensity_kg_per_km": 0.12, "benchmark_source": "ICCT India 2023"},
        },
    },
    {
        "country_code": "US",
        "region_name": "United States National",
        "grid_ef_kwh": 0.386,  # US grid average 2023
        "grid_ef_source": "EPA eGRID 2023",
        "grid_ef_year": "2023",
        "regulations": [
            {"name": "SEC Climate Disclosure", "description": "Climate-related disclosure rules", "mandatory": True},
            {"name": "California Cap-and-Trade", "description": "State-level emissions trading", "incentive_type": "trading"},
        ],
        "incentives": [
            {"name": "IRA Tax Credits", "description": "Inflation Reduction Act clean energy tax credits", "value_pct": 30, "eligibility": "commercial"},
            {"name": "45Q Carbon Capture", "description": "Tax credit for carbon capture", "value_usd_per_tonne": 85},
        ],
        "archetype_benchmarks": {
            "digital_service": {"intensity_kg_per_employee": 2200, "benchmark_source": "CDP US 2023"},
            "material_transformer": {"intensity_kg_per_unit": 0.35, "benchmark_source": "EPA 2023"},
            "retailer": {"intensity_kg_per_sqm": 85, "benchmark_source": "EPA Energy Star 2023"},
        },
    },
    {
        "country_code": "GB",
        "region_name": "United Kingdom",
        "grid_ef_kwh": 0.207,  # UK grid 2023
        "grid_ef_source": "UK DEFRA 2023",
        "grid_ef_year": "2023",
        "regulations": [
            {"name": "SECR", "description": "Streamlined Energy and Carbon Reporting", "mandatory": True},
            {"name": "UK ETS", "description": "UK Emissions Trading Scheme", "incentive_type": "trading"},
        ],
        "incentives": [
            {"name": "Climate Change Levy Exemption", "description": "Exemption for renewable energy", "incentive_type": "tax"},
        ],
        "carbon_price_usd": 45.0,
        "carbon_pricing_scheme": "UK ETS",
        "archetype_benchmarks": {
            "digital_service": {"intensity_kg_per_employee": 1800, "benchmark_source": "CDP UK 2023"},
        },
    },
    {
        "country_code": "DE",
        "region_name": "Germany",
        "grid_ef_kwh": 0.366,  # Germany grid 2023
        "grid_ef_source": "UBA Germany 2023",
        "grid_ef_year": "2023",
        "regulations": [
            {"name": "CSRD", "description": "Corporate Sustainability Reporting Directive", "mandatory": True},
            {"name": "EU ETS", "description": "European Emissions Trading System", "incentive_type": "trading"},
            {"name": "LkSG", "description": "German Supply Chain Due Diligence Act", "mandatory": True},
        ],
        "carbon_price_usd": 75.0,
        "carbon_pricing_scheme": "EU ETS",
        "archetype_benchmarks": {
            "material_transformer": {"intensity_kg_per_unit": 0.28, "benchmark_source": "VDI 2023"},
        },
    },
]
