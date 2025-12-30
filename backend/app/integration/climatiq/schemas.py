"""
Pydantic schemas for Climatiq API integration
Comprehensive models for all Climatiq endpoints
"""

from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


# ========== PART 1: Core Estimation Schemas ==========

class EmissionFactor(BaseModel):
    """Identifies a specific emission factor in the Climatiq database"""
    activity_id: str = Field(..., description="e.g., electricity-supply_grid-source_residual_mix")
    data_version: str = Field(default="^28", description="^28 = latest 28.x; 28 = exact version")
    region: Optional[str] = Field(None, description="ISO 3166-1 Alpha-2 or extended (US-CA, US-NY)")
    year: Optional[int] = Field(None, description="2023, 2024, etc.")
    source: Optional[str] = Field(None, description="BEIS, EPA, etc.")


class EstimateRequest(BaseModel):
    """Single estimate request"""
    emission_factor: EmissionFactor
    parameters: Dict[str, Any]  # Energy, Weight, or Money params


class EstimateResponse(BaseModel):
    """Single estimate response"""
    co2e: Decimal = Field(..., description="Result in kg CO2e")
    co2e_unit: str = Field(default="kg")
    co2e_calculation_method: str = Field(default="ipcc_ar6_gwp100")
    constituent_gases: Optional[Dict[str, Decimal]] = None
    source_dataset: Optional[str] = None
    emission_factor: Optional[Dict[str, Any]] = None


class BatchEstimateRequest(BaseModel):
    """Batch request: up to 100 items"""
    estimates: List[EstimateRequest] = Field(..., max_length=100)


class BatchEstimateResult(BaseModel):
    """Individual batch result (mirrors single estimate or error)"""
    co2e: Optional[Decimal] = None
    co2e_unit: Optional[str] = None
    co2e_calculation_method: Optional[str] = None
    constituent_gases: Optional[Dict[str, Decimal]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class BatchEstimateResponse(BaseModel):
    """Batch response: results array 1-to-1 with input"""
    results: List[BatchEstimateResult]


# ========== PART 2: Travel Schemas ==========

class LocationReference(BaseModel):
    """Location can be specified multiple ways"""
    query: Optional[str] = None           # "New York, NY"
    iata: Optional[str] = None            # "LHR" for airports
    un_locode: Optional[str] = None       # "DE-HAM" for Hamburg port
    coordinates: Optional[Dict[str, float]] = None  # {"latitude": 51.5, "longitude": -0.1}


class AirTravelDetails(BaseModel):
    """Air-specific parameters"""
    cabin_class: str = Field(..., alias="class", description="economy, business, first, premium_economy")
    
    class Config:
        populate_by_name = True


class CarTravelDetails(BaseModel):
    """Car/road travel specifics"""
    car_type: str = Field(..., description="petrol, diesel, hybrid, battery (EV)")


class DistanceTravelRequest(BaseModel):
    """Distance-based travel calculation"""
    origin: LocationReference
    destination: LocationReference
    travel_mode: str = Field(..., description="air, car, rail, bus")
    year: int = Field(default=2024)
    
    # Mode-specific details
    air_details: Optional[AirTravelDetails] = None
    car_details: Optional[CarTravelDetails] = None


class DistanceTravelResponse(BaseModel):
    """Distance travel result"""
    distance: Optional[Decimal] = Field(None, description="km")
    co2e: Decimal
    co2e_unit: str = "kg"
    co2e_calculation_method: str = "ipcc_ar6_gwp100"


class SpendTravelRequest(BaseModel):
    """Spend-based travel (invoice entries, credit cards, etc.)"""
    spend_type: str = Field(..., description="hotel, car_rental, rail, air")
    money: Decimal
    money_unit: str = Field(..., description="usd, eur, gbp, jpy, aud")
    spend_year: int = Field(..., description="Year of spend for inflation adjustment")
    spend_location: Optional[LocationReference] = None  # Hotel region matters!


class SpendTravelResponse(BaseModel):
    """Spend travel result"""
    co2e: Decimal
    co2e_unit: str = "kg"
    spend_type: str


# ========== PART 3: Energy Schemas ==========

class ElectricityRequest(BaseModel):
    """Electricity calculation"""
    energy: Decimal
    energy_unit: str = Field(..., description="kWh, MWh, MJ, GJ, BTU, therm")
    region: str = Field(..., description="Grid region (required)")
    year: int = Field(default=2024)
    
    # Market-based reporting (optional)
    renewable_energy_credits: Optional[Decimal] = None
    components: Optional[List[Dict[str, Any]]] = None  # Custom power mix


class HeatSteamRequest(BaseModel):
    """Heat and steam (purchased thermal energy)"""
    energy: Decimal
    energy_unit: str
    fuel_type: str = Field(..., description="natural_gas, district_heating")
    loss_factor: Optional[float] = None  # Critical for steam


class FuelRequest(BaseModel):
    """Direct fuel combustion (Scope 1)"""
    fuel_type: str = Field(..., description="natural_gas, diesel, gasoline, propane")
    volume: Optional[Decimal] = None
    volume_unit: Optional[str] = None
    energy: Optional[Decimal] = None
    energy_unit: Optional[str] = None
    year: int = Field(default=2024)


class EnergyResponse(BaseModel):
    """Energy calculation result"""
    co2e: Decimal
    co2e_unit: str = "kg"
    constituent_gases: Optional[Dict[str, Decimal]] = None
    scope: str  # "1" for fuel, "2" for electricity/heat/steam


# ========== PART 4: Freight Schemas ==========

class FreightLocation(BaseModel):
    """Route location point"""
    query: Optional[str] = None
    iata: Optional[str] = None
    un_locode: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None


class RoadLegDetails(BaseModel):
    """Road freight specifics"""
    vehicle_type: str = Field(..., description="hgv, van, truck")
    fuel_type: str = Field(..., description="diesel, electric, cng")


class AirLegDetails(BaseModel):
    """Air freight specifics"""
    aircraft_type: Optional[str] = None
    rfi: float = Field(default=2.0, description="Radiative Forcing Index (1.0-3.0)")


class SeaLegDetails(BaseModel):
    """Sea freight specifics"""
    vessel_type: str = Field(..., description="container_ship, bulk_carrier, tanker")
    transit_type: str = Field(..., description="partial_load, full_load")


class RailLegDetails(BaseModel):
    """Rail freight specifics"""
    propulsion: str = Field(..., description="diesel, electric, mixed")


class FreightLeg(BaseModel):
    """Transport leg between locations"""
    origin: FreightLocation
    destination: FreightLocation
    transport_mode: str = Field(..., description="road, air, sea, rail")
    leg_details: Dict[str, Any]


class Cargo(BaseModel):
    """Freight payload"""
    weight: Decimal
    weight_unit: str = Field(..., description="kg, t, ton, lb")


class IntermodalFreightRequest(BaseModel):
    """Complete multi-leg freight route"""
    route: List[FreightLeg]
    cargo: Cargo


class FreightLegResult(BaseModel):
    """Result for a single leg"""
    co2e: Decimal
    distance: Optional[Decimal] = None


class IntermodalFreightResponse(BaseModel):
    """Complete route result"""
    total_co2e: Decimal
    total_co2e_unit: str = "kg"
    total_distance: Optional[Decimal] = None
    legs: List[FreightLegResult]
    scope: str = "3"  # Scope 3.4 or 3.9


# ========== PART 5: Procurement Schemas ==========

class ClassificationObject(BaseModel):
    """Industry/product code"""
    code: str
    classification_type: str  # "isic4", "nace2", "naics2017", "mcc"


class ProcurementRequest(BaseModel):
    """Spend-based emissions calculation"""
    money: Decimal
    money_unit: str = Field(..., description="usd, eur, gbp")
    spend_year: int = Field(..., description="Critical for EEIO inflation adjustment")
    classification: ClassificationObject
    region: Optional[str] = None


class ProcurementResponse(BaseModel):
    """Procurement result"""
    co2e: Decimal
    co2e_unit: str = "kg"
    classification: ClassificationObject
    source_dataset: str = "EXIOBASE"  # Default EEIO model


# ========== PART 6: Autopilot Schemas ==========

class AutopilotSuggestRequest(BaseModel):
    """Request factor suggestions based on text"""
    query: str = Field(..., description="Natural language description")
    domain: Optional[str] = Field(default="general", description="general or manufacturing")


class AutopilotCandidate(BaseModel):
    """Suggested emission factor"""
    activity_id: str
    name: str
    confidence: float
    region: Optional[str] = None
    source: Optional[str] = None


class AutopilotSuggestResponse(BaseModel):
    """Multiple candidate suggestions"""
    suggestions: List[AutopilotCandidate]


class AutopilotEstimateRequest(BaseModel):
    """Combined: Suggest + Calculate in one call"""
    query: str
    parameters: Optional[Dict[str, Any]] = None  # Optional quantity params


class AutopilotEstimateResponse(BaseModel):
    """Result with transparency"""
    co2e: Decimal
    co2e_unit: str = "kg"
    activity_id: str
    confidence: float
    source_trail: str  # Explanation of why this factor was chosen


# ========== PART 7: Custom Mappings Schemas ==========

class CreateCustomMappingRequest(BaseModel):
    """Define a new organizational mapping"""
    internal_label: str
    query: str  # Natural language for Autopilot
    region: Optional[str] = None
    year: Optional[int] = None


class CustomMappingResponse(BaseModel):
    """Stored mapping"""
    id: str
    internal_label: str
    activity_id: str
    confidence: float
    created_at: str


class EstimateWithMappingRequest(BaseModel):
    """Use pre-defined mapping for calculation"""
    mapping_id: str
    parameters: Dict[str, Any]  # Standard params (energy, money, weight)
