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
    organization_id: Optional[UUID4] = None  # Auto-set from current user if not provided


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
    input_data: Optional[Dict[str, Any]] = None  # Contains full Climatiq response with emission factor info
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
