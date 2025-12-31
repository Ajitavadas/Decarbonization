"""
Pydantic schemas for API request/response models
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, Field, UUID4


# ========== Base Schemas ==========

class ResponseBase(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None


# ========== User Schemas ==========

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(UserBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ========== Organization Schemas ==========

class OrganizationBase(BaseModel):
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Project Schemas ==========

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    reporting_year: str


class ProjectCreate(ProjectBase):
    organization_id: UUID4


class ProjectResponse(ProjectBase):
    id: UUID4
    organization_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Activity Schemas ==========

class ActivityBase(BaseModel):
    activity_type: str
    sub_type: Optional[str] = None
    activity_date: datetime
    description: Optional[str] = None


class ActivityCreate(ActivityBase):
    project_id: UUID4
    input_data: Dict[str, Any]


class ActivityResponse(ActivityBase):
    id: UUID4
    project_id: UUID4
    scope: str
    co2e_kg: Decimal
    co2e_unit: str
    calculation_method: str
    emission_factor_id: Optional[str]
    source_dataset: Optional[str]
    region: Optional[str]
    year: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivitySummary(BaseModel):
    """Summary statistics for activities"""
    total_activities: int
    total_co2e_kg: Decimal
    scope_breakdown: Dict[str, Decimal]
    activity_type_breakdown: Dict[str, Decimal]


# ========== Estimate Schemas ==========

class EstimateRequestSchema(BaseModel):
    """Single estimation request"""
    activity_id: str = Field(..., description="Climatiq emission factor ID")
    parameters: Dict[str, Any] = Field(..., description="Activity parameters")
    region: Optional[str] = None
    year: Optional[int] = None
    activity_type: str = Field(..., description="travel, freight, energy, procurement")
    sub_type: Optional[str] = None
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None
    description: Optional[str] = None


class EstimateResponseSchema(ResponseBase):
    """Single estimation response"""
    data: Dict[str, Any]


class BatchEstimateRequestSchema(BaseModel):
    """Batch estimation request"""
    project_id: UUID4
    estimates: List[Dict[str, Any]] = Field(..., max_length=1000)


class BatchEstimateResponseSchema(ResponseBase):
    """Batch estimation response"""
    job_id: UUID4
    status: str
    total_records: int


# ========== Travel Schemas ==========

class TravelDistanceRequest(BaseModel):
    """Distance-based travel request"""
    origin: str
    destination: str
    travel_mode: str = Field(..., description="air, car, rail, bus")
    cabin_class: Optional[str] = "economy"  # For air travel
    year: Optional[int] = 2024
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None


class TravelSpendRequest(BaseModel):
    """Spend-based travel request"""
    spend_type: str = Field(..., description="hotel, car_rental, rail, air")
    amount: Decimal
    currency: str = Field(..., description="usd, eur, gbp")
    spend_year: int = Field(..., description="Year for inflation adjustment")
    location: Optional[str] = None
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None


# ========== Energy Schemas ==========

class ElectricityCalculationRequest(BaseModel):
    """Electricity calculation request"""
    energy_kwh: Decimal
    region: str = Field(..., description="Grid region code (required)")
    year: Optional[int] = 2024
    renewable_credits: Optional[Decimal] = None
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None


class FuelCalculationRequest(BaseModel):
    """Fuel combustion calculation request"""
    fuel_type: str = Field(..., description="natural_gas, diesel, coal, gasoline, biodiesel_bio_100, ethanol, cng, etc.")
    amount: Decimal
    unit: str = Field(..., description="l, kg, t, gal, m3, kWh, MJ")
    unit_type: str = Field("volume", description="volume, weight, or energy")
    region: Optional[str] = Field(None, description="2-letter ISO country code")
    year: Optional[int] = None
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None


# ========== Freight Schemas ==========

class FreightLegRequest(BaseModel):
    """Single freight leg (for multi-leg routes)"""
    location: str = Field(..., description="Query, IATA, UN-LOCODE, or lat,lon coordinates")
    transport_mode: Optional[str] = Field(None, description="road, air, sea, rail - omit for final destination")


class FreightCalculationRequest(BaseModel):
    """Intermodal freight calculation request"""
    origin: str = Field(..., description="Start location")
    destination: str = Field(..., description="End location")
    transport_mode: str = Field(..., description="road, air, sea, rail")
    cargo_weight: Decimal
    weight_unit: str = Field("kg", description="kg, t, lb, ton")
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None


class MultiLegFreightRequest(BaseModel):
    """Multi-leg intermodal freight calculation"""
    route: List[FreightLegRequest]
    cargo_weight: Decimal
    weight_unit: str = Field("kg", description="kg, t, lb, ton")
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None


# ========== Procurement Schemas ==========

class ProcurementCalculationRequest(BaseModel):
    """Spend-based procurement calculation request"""
    amount: Decimal
    currency: str = Field(..., description="eur, usd, gbp, etc.")
    classification_code: str = Field(..., description="Industry/category code")
    classification_type: str = Field("mcc", description="mcc, unspsc, isic4, nace2")
    region: Optional[str] = Field(None, description="Supplier country (2-letter ISO)")
    spend_year: Optional[int] = Field(None, description="Year for inflation adjustment")
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None


# ========== Autopilot Schemas ==========
# NOTE: Autopilot is an ADD-ON feature that requires explicit opt-in from Climatiq.

class AutopilotSuggestRequestSchema(BaseModel):
    """Autopilot suggestion request (v1-preview4)"""
    text: str = Field(..., description="Natural language activity description")
    max_suggestions: int = Field(5, ge=1, le=20)
    unit_type: Optional[List[str]] = Field(None, description="Filter: Money, Weight, Volume, Energy, Number")
    region: Optional[str] = None
    year: Optional[int] = None
    source: Optional[List[str]] = Field(None, description="Filter by data sources: EPA, BEIS, Ecoinvent, etc.")
    scope: Optional[List[str]] = Field(None, description="Filter by scope: 1, 2, 3, 3.1, 3.2, etc.")


class AutopilotEstimateRequestSchema(BaseModel):
    """Autopilot one-shot estimate (v1-preview4)"""
    text: str = Field(..., description="Natural language activity description")
    amount: Decimal
    unit: str = Field(..., description="Unit: eur, usd, kg, t, kWh, etc.")
    unit_type: str = Field("money", description="money, weight, volume, or energy")
    region: Optional[str] = None
    year: Optional[int] = None
    scope: Optional[List[str]] = Field(None, description="Filter by scope: 1, 2, 3")
    project_id: Optional[UUID4] = None
    activity_date: Optional[datetime] = None


# ========== Custom Mapping Schemas ==========

class CustomMappingCreate(BaseModel):
    """Create custom mapping"""
    internal_label: str
    internal_code: Optional[str] = None
    category: Optional[str] = None
    query: str = Field(..., description="For Autopilot suggestion")
    climatiq_activity_id: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None


class CustomMappingResponse(BaseModel):
    """Custom mapping response"""
    id: UUID4
    internal_label: str
    internal_code: Optional[str]
    category: Optional[str]
    climatiq_activity_id: str
    confidence_score: Optional[float]
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class EstimateWithMappingRequest(BaseModel):
    """Estimate using custom mapping"""
    mapping_id: UUID4
    parameters: Dict[str, Any]
    project_id: UUID4
    activity_date: Optional[datetime] = None


# ========== Batch Job Schemas ==========

class BatchJobResponse(BaseModel):
    """Batch job status response"""
    id: UUID4
    job_type: str
    status: str
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    progress_percentage: float
    error_log: List[Dict[str, Any]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ========== Dashboard Schemas ==========

class DashboardSummary(BaseModel):
    """Dashboard overview statistics"""
    total_co2e_kg: Decimal
    scope_1: Decimal
    scope_2: Decimal
    scope_3: Decimal
    total_activities: int
    date_range: Dict[str, str]
    activity_breakdown: Dict[str, Decimal]
    monthly_trend: List[Dict[str, Any]]


# ========== Pagination Schema ==========

class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
