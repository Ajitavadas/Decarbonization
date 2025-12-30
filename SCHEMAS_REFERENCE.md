# 📊 COMPREHENSIVE SCHEMAS REFERENCE - Climatiq API Integration

This document provides exact Pydantic schema definitions for all Climatiq API endpoints, based on your research and the official documentation.

---

## PART 1: Core Estimation Schemas

### 1.1 Estimate Endpoint Schemas

```python
# backend/app/integration/climatiq/schemas/estimate.py

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal

class EmissionFactor(BaseModel):
    """Identifies a specific emission factor in the Climatiq database"""
    activity_id: str = Field(..., description="e.g., electricity-supply_grid-source_residual_mix")
    data_version: str = Field(default="^28", description="^28 = latest 28.x; 28 = exact version")
    region: Optional[str] = Field(None, description="ISO 3166-1 Alpha-2 or extended (US-CA, US-NY)")
    year: Optional[int] = Field(None, description="2023, 2024, etc.")
    source: Optional[str] = Field(None, description="BEIS, EPA, etc.")

class EnergyParameters(BaseModel):
    """For energy-type factors"""
    energy: Decimal
    energy_unit: str = Field(..., description="kWh, MWh, MJ, GJ, BTU, therm")

class WeightParameters(BaseModel):
    """For weight-type factors"""
    weight: Decimal
    weight_unit: str = Field(..., description="kg, t, lb, ton")

class MoneyParameters(BaseModel):
    """For spend-based factors (EEIO)"""
    money: Decimal
    money_unit: str = Field(..., description="usd, eur, gbp, jpy, aud")

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

class BatchEstimateRequest(BaseModel):
    """Batch request: up to 100 items"""
    estimates: list[EstimateRequest] = Field(..., max_items=100)

class BatchEstimateResult(BaseModel):
    """Individual batch result (mirrors single estimate or error)"""
    co2e: Optional[Decimal] = None
    co2e_unit: Optional[str] = None
    error: Optional[Dict[str, str]] = None

class BatchEstimateResponse(BaseModel):
    """Batch response: results array 1-to-1 with input"""
    results: list[BatchEstimateResult]

```

---

## PART 2: Travel Schemas

### 2.1 Distance-Based Travel

```python
# backend/app/integration/climatiq/schemas/travel.py

class LocationReference(BaseModel):
    """Location can be specified multiple ways"""
    query: Optional[str] = None           # "New York, NY"
    iata: Optional[str] = None            # "LHR" for airports
    un_locode: Optional[str] = None       # "DE-HAM" for Hamburg port
    coordinates: Optional[Dict[str, float]] = None  # {"latitude": 51.5, "longitude": -0.1}

class AirTravelDetails(BaseModel):
    """Air-specific parameters"""
    class_: str = Field(..., alias="class", description="economy, business, first, premium_economy")
    # Class allocation matters: business ≈ 2-3x economy emissions per pax

class CarTravelDetails(BaseModel):
    """Car/road travel specifics"""
    car_type: str = Field(..., description="petrol, diesel, hybrid, battery (EV)")

class DistanceTravelRequest(BaseModel):
    """Distance-based calculation"""
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
    travel_mode: str
    calculation_method: str = "ipcc_ar6_gwp100"

class SpendTravelRequest(BaseModel):
    """Spend-based travel (invoice entries, credit cards, etc.)"""
    spend_type: str = Field(..., description="air, hotel, rail, road, sea")
    money: Decimal
    money_unit: str = Field(..., description="usd, eur, gbp")
    spend_year: int = Field(..., description="CRITICAL: Year of purchase for inflation adjustment")
    spend_location: Optional[LocationReference] = None  # Hotel region matters!

class SpendTravelResponse(BaseModel):
    """Spend travel result"""
    co2e: Decimal
    co2e_unit: str = "kg"
    spend_type: str
```

---

## PART 3: Energy Schemas

### 3.1 Electricity Schemas

```python
# backend/app/integration/climatiq/schemas/energy.py

class EnergyAmount(BaseModel):
    """Standard energy quantity"""
    energy: Decimal
    energy_unit: str = Field(..., description="kWh, MWh, MJ, GJ, BTU, therm")

class RenewableEnergyCredits(BaseModel):
    """Renewable Energy Certificates for market-based reporting"""
    energy: Decimal
    energy_unit: str

class ElectricityComponent(BaseModel):
    """Custom power mix component"""
    energy_type: str = Field(..., description="solar, wind, hydro, natural_gas, coal")
    connection_type: str = Field(..., description="direct, grid")
    energy: Decimal
    energy_unit: str

class ElectricityRequest(BaseModel):
    """Electricity calculation"""
    region: str = Field(..., description="Grid region: US-NY, DE, GB, etc. CRITICAL for accuracy")
    year: int = Field(default=2024)
    amount: EnergyAmount
    connection_type: str = Field(default="grid", description="grid or direct (dedicated line)")
    source_set: str = Field(default="core", description="core or iea (premium)")
    
    # Market-based vs Location-based reporting
    recs: Optional[RenewableEnergyCredits] = None  # Quantity covered by green certs
    
    # Custom power mix (e.g., 20% solar, 80% grid)
    components: Optional[list[ElectricityComponent]] = None

class HeatSteamRequest(BaseModel):
    """Heat and steam (purchased thermal energy)"""
    region: str
    year: int
    amount: EnergyAmount
    loss_factor: Optional[float] = None  # Critical for steam; accounts for distribution losses

class FuelRequest(BaseModel):
    """Direct fuel combustion (Scope 1)"""
    fuel_type: str = Field(..., description="natural_gas, diesel_b7, biodiesel_b100, lpg, etc.")
    amount: Decimal
    unit: str = Field(..., description="kg, liters, therms, etc.")
    year: int = Field(default=2024)

class EnergyResponse(BaseModel):
    """Energy calculation result"""
    co2e: Decimal
    co2e_unit: str = "kg"
    biogenic_emissions: Optional[Decimal] = None  # Separate for biofuels
    calculation_method: str = "ipcc_ar6_gwp100"
    scope: str  # "1" for fuel, "2" for electricity/heat/steam
```

---

## PART 4: Freight Schemas

### 4.1 Intermodal Freight

```python
# backend/app/integration/climatiq/schemas/freight.py

class FreightLocation(BaseModel):
    """Route location point"""
    query: Optional[str] = None              # "Port of Shanghai"
    un_locode: Optional[str] = None          # "CN-SHA" (critical for ports!)
    iata: Optional[str] = None               # For airports
    coordinates: Optional[Dict[str, float]] = None

class RoadLegDetails(BaseModel):
    """Road freight specifics"""
    region: str = Field(..., description="north_america, china, rest_of_world")
    vehicle_type: str = Field(..., description="van, rigid_truck, articulated_truck")
    load_type: str = Field(default="average", description="light, average, full")
    # Empty running accounted for automatically

class AirLegDetails(BaseModel):
    """Air freight specifics"""
    aircraft_type: str = Field(..., description="freighter, belly_freight")
    radiative_forcing_index: float = Field(default=2.0, description="1.0=CO2 only; 2.0=includes RFI warming")
    # RFI accounts for cirrus clouds, NOx warming at altitude

class SeaLegDetails(BaseModel):
    """Sea freight specifics"""
    vessel_type: str = Field(..., description="container_ship, bulk_carrier, tanker")
    transit_type: str = Field(..., description="partial_load, full_load")

class RailLegDetails(BaseModel):
    """Rail freight specifics"""
    propulsion: str = Field(..., description="diesel, electric, mixed")

class LogisticsHubLegDetails(BaseModel):
    """Hub processing (ports, terminals, warehouses)"""
    logistics_hub_type: str = Field(..., description="transshipment, warehouse")

class FreightLeg(BaseModel):
    """Transport leg between locations"""
    leg_details: Dict[str, Any]  # road, air, sea, rail, or logistics_hubs

class Cargo(BaseModel):
    """Freight payload"""
    weight: Decimal
    weight_unit: str = Field(..., description="kg, t, ton, lb")

class IntermodalFreightRequest(BaseModel):
    """Complete multi-leg freight route"""
    route: list[FreightLocation | FreightLeg] = Field(..., description="Alternating: location, leg, location, leg, ...")
    cargo: Cargo

class FreightLegResult(BaseModel):
    """Result for a single leg"""
    co2e: Decimal
    distance: Optional[Decimal] = None

class IntermodalFreightResponse(BaseModel):
    """Complete route result"""
    co2e: Decimal
    co2e_unit: str = "kg"
    legs: list[FreightLegResult]  # Breakdown by leg for transparency
    total_distance: Optional[Decimal] = None
    scope: str = "3"  # Scope 3.4 or 3.9 (upstream/downstream)
```

---

## PART 5: Procurement & Classification Schemas

### 5.1 Procurement (Spend-Based)

```python
# backend/app/integration/climatiq/schemas/procurement.py

class ClassificationObject(BaseModel):
    """Industry/product code"""
    classification_code: str  # "25", "6202", etc.
    classification_type: str  # "isic4", "nace2", "naics2017", "mcc"

class ProcurementRequest(BaseModel):
    """Spend-based emissions calculation"""
    activity: ClassificationObject
    money: Decimal
    money_unit: str = Field(..., description="usd, eur, gbp, etc.")
    spend_year: int = Field(..., description="Critical for inflation adjustment!")
    spend_region: str = Field(default="GLOBAL", description="Where purchase occurred")
    
    # Optional price adjustments
    tax_margin: Optional[float] = None          # VAT percentage
    trade_margin: Optional[float] = None        # Markup
    transport_margin: Optional[float] = None    # Shipping added

class ClassificationResponse(BaseModel):
    """Classification result"""
    co2e: Decimal
    co2e_unit: str = "kg"
    classification_code: str
    classification_type: str
    source_dataset: str = "EXIOBASE"  # Default EEIO model
```

---

## PART 6: Autopilot Schemas

### 6.1 Autopilot NLP Classification

```python
# backend/app/integration/climatiq/schemas/autopilot.py

class AutopilotSuggestRequest(BaseModel):
    """Request factor suggestions based on text"""
    description: str = Field(..., description="E.g., '500 Dell Latitude Laptops'")
    domain: Optional[str] = Field(default="general", description="general or manufacturing")

class AutopilotCandidate(BaseModel):
    """Suggested emission factor"""
    activity_id: str
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="0.0-1.0 confidence")
    region: Optional[str] = None
    source: Optional[str] = None

class AutopilotSuggestResponse(BaseModel):
    """Multiple candidate suggestions"""
    suggestions: list[AutopilotCandidate]

class AutopilotEstimateRequest(BaseModel):
    """Combined: Suggest + Calculate in one call"""
    description: str
    domain: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None  # Optional quantity params

class AutopilotEstimateResponse(BaseModel):
    """Result with transparency"""
    co2e: Decimal
    co2e_unit: str = "kg"
    activity_id: str  # The matched factor
    confidence: float
    source_trail: str  # Explanation of why this factor was chosen
```

---

## PART 7: Custom Mappings Schemas

### 7.1 Custom Mappings (ERP Integration)

```python
# backend/app/integration/climatiq/schemas/mappings.py

class CreateCustomMappingRequest(BaseModel):
    """Define a new organizational mapping"""
    internal_label: str = Field(..., description="ERP code, e.g., 'GL-TRAVEL-001'")
    climatiq_activity_id: str  # Target emission factor ID
    source: Optional[str] = None  # Preferred data source
    year: Optional[int] = None     # Preferred year

class CustomMappingResponse(BaseModel):
    """Stored mapping"""
    id: str
    internal_label: str
    climatiq_activity_id: str
    confidence_score: Optional[float] = None
    created_at: str

class EstimateWithMappingRequest(BaseModel):
    """Use pre-defined mapping for calculation"""
    internal_label: str  # Look up in mappings table
    parameters: Dict[str, Any]  # Standard params (energy, money, weight)
```

---

## PART 8: Database Activity Storage Schemas

### 8.1 Database Models (SQLAlchemy/Pydantic)

```python
# backend/app/db/models/activity.py

from sqlalchemy import Column, String, Numeric, DateTime, JSON, UUID
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class EmissionActivity(Base):
    """Core ledger of all carbon activities"""
    __tablename__ = "emission_activities"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: UUID = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    
    # Classification
    activity_type: str = Column(String(50))  # travel, freight, energy, procurement
    scope: str = Column(String(10))          # Scope 1, 2, or 3
    description: str = Column(String(500))   # Human label
    
    # Data
    activity_date: date = Column(Date)
    region_code: str = Column(String(10))    # US-CA, DE, GB, etc.
    
    # Raw inputs (stored for auditability)
    input_data: dict = Column(JSONB)         # Exact Climatiq payload sent
    
    # Results
    co2e_kg: Decimal = Column(Numeric(20, 6))
    co2e_unit: str = Column(String(10), default="kg")
    calculation_method: str = Column(String(20))  # ar4, ar5, ar6
    source_dataset: str = Column(String(100))    # EPA, BEIS, EXIOBASE, etc.
    
    # Metadata
    is_estimate: bool = Column(Boolean, default=False)  # True if from Autopilot
    batch_job_id: UUID = Column(UUID(as_uuid=True), ForeignKey("batch_jobs.id"))
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

class CustomMapping(Base):
    """Organizational memory of ERP → Climatiq mappings"""
    __tablename__ = "custom_mappings"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: UUID = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    internal_label: str = Column(String(255))  # ERP code
    climatiq_activity_id: str = Column(String(255))
    source: Optional[str] = Column(String(100))
    year: Optional[int] = Column(Integer)
    confidence_score: Optional[float] = Column(Float)
    
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

class BatchJob(Base):
    """Track async batch processing status"""
    __tablename__ = "batch_jobs"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True)
    organization_id: UUID = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    status: str = Column(String(20))  # queued, processing, completed, failed
    file_url: str = Column(String(500))
    
    total_records: int = Column(Integer, default=0)
    processed_records: int = Column(Integer, default=0)
    
    error_log: list[dict] = Column(JSONB, default=[])  # [{row: 5, error: "Invalid region"}]
    
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    completed_at: Optional[datetime] = Column(DateTime)
```

---

## PART 9: Response Schemas for Endpoints

### 9.1 API Response Wrappers

```python
# backend/app/schemas/responses.py

class ActivityCreateResponse(BaseModel):
    """Response when activity is created"""
    id: str
    activity_type: str
    scope: str
    co2e_kg: Decimal
    co2e_unit: str = "kg"
    created_at: str

class DashboardSummary(BaseModel):
    """Dashboard overview"""
    total_co2e_kg: Decimal
    scope_breakdown: Dict[str, Decimal]  # {"Scope 1": 100, "Scope 2": 500, "Scope 3": 2000}
    activity_count: int
    date_range: Dict[str, str]  # {"start": "2024-01-01", "end": "2024-12-31"}

class BatchJobStatus(BaseModel):
    """Status of async batch job"""
    job_id: str
    status: str  # queued, processing, completed, failed
    processed_records: int
    total_records: int
    error_count: int
    errors: list[Dict] = []  # Detailed error objects
    created_at: str
    completed_at: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error format"""
    error_code: str
    message: str
    details: Optional[Dict] = None
```

---

## CRITICAL IMPLEMENTATION NOTES

### 1. Data Versioning
Always use dynamic versioning: `"data_version": "^28"`
This ensures you get latest science while maintaining reproducibility within major version.

### 2. Region Specificity
NEVER omit region for energy calculations. Grid carbon intensity varies 10x globally:
- Coal-heavy: 800+ g CO2/kWh
- Hydro/Nuclear: 10-50 g CO2/kWh

### 3. Spend Year for Inflation
CRITICAL for spend-based calculations:
```python
{
    "spend_type": "hotel",
    "money": 1000,
    "spend_year": 2023  # DON'T OMIT
}
```
Without spend_year, Climatiq assumes current year → artificial reduction in emissions.

### 4. Batch Error Handling
200 OK response with individual errors in results array:
```python
results = [
    {"co2e": 500},  # Success
    {"error": "Invalid region: XY"},  # Failure
    {"co2e": 750}   # Success
]
```
Client must iterate and handle each individually.

### 5. Confidence Scoring for Autopilot
Store confidence from suggestions:
```python
custom_mapping = CustomMapping(
    internal_label="Dell Laptop",
    climatiq_activity_id="computers_manufacturing",
    confidence_score=0.92  # Store this!
)
```

This enables future UI warnings: "Only 72% confident in this classification."

---

## Schema Validation Rules

```python
# Validators to include in schemas

class EstimateRequest(BaseModel):
    @validator('parameters')
    def validate_parameters(cls, v, values):
        factor_type = infer_unit_type(values.get('emission_factor'))
        if factor_type == 'energy' and 'energy' not in v:
            raise ValueError("Energy parameters require 'energy' field")
        return v

class ProcurementRequest(BaseModel):
    @validator('spend_year')
    def validate_year(cls, v):
        if v < 2000 or v > 2025:
            raise ValueError("Spend year must be between 2000 and 2025")
        return v

class IntermodalFreightRequest(BaseModel):
    @validator('route')
    def validate_route_structure(cls, v):
        # Must alternate: location, leg, location, leg, ...location
        if len(v) < 3:
            raise ValueError("Route must have at least origin + leg + destination")
        return v
```

---

This comprehensive schema reference covers all Climatiq endpoints and provides exact implementation patterns for your FastAPI backend.

