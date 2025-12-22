# app/schemas/schemas.py
"""
Pydantic schemas for request/response validation
- User registration and login
- Emission transaction management
- Emission factor handling
"""

import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


# ==================== User Schemas ====================

class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)
    # Organization can be provided or created during registration
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    organization_slug: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response aligned with new model"""
    id: uuid.UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    role: str
    organization_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class PasswordChangeRequest(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=255)
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


# ==================== Emission Transaction Schemas ====================

class EmissionTransactionCreate(BaseModel):
    """Schema for creating emission transaction"""
    description: str = Field(..., max_length=500)
    transaction_date: datetime
    category: str = Field(..., max_length=100)
    activity_value: float = Field(..., gt=0)
    activity_unit: str = Field(..., max_length=50)
    emission_factor_id: Optional[str] = None
    emission_factor_value: float = Field(..., gt=0)
    scope: int = Field(..., ge=1, le=3)
    supplier_name: Optional[str] = None
    project_id: Optional[str] = None
    notes: Optional[str] = None


class EmissionTransactionUpdate(BaseModel):
    """Schema for updating emission transaction"""
    description: Optional[str] = None
    category: Optional[str] = None
    activity_value: Optional[float] = None
    activity_unit: Optional[str] = None
    scope: Optional[int] = None
    supplier_name: Optional[str] = None
    notes: Optional[str] = None


class EmissionEventResponse(BaseModel):
    id: str
    organization_id: str
    activity_date: datetime
    activity_value: float
    activity_unit_raw: Optional[str]
    activity_unit_normalized: str
    activity_value_normalized: float
    source_type: str
    scope: str
    scope_3_category: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class CalculationLedgerResponse(BaseModel):
    id: str
    organization_id: str
    emission_event_id: str
    calculation_timestamp: datetime
    activity_value: float
    activity_unit_normalized: str
    emission_factor_value: float
    result_kg_co2e: float
    result_kg_total: float
    fell_back_to_climatiq: bool
    calculated_by_user_id: Optional[str]
    
    class Config:
        from_attributes = True

class EmissionTransactionResponse(BaseModel):
    """Combined schema for dashboard/list views (Legacy name, new structure)"""
    id: str
    event_id: str
    description: Optional[str]
    date: datetime
    scope: str
    category: Optional[str]
    amount: float
    unit: str
    co2e_tonnes: float
    
    class Config:
        from_attributes = True


# ==================== Emission Factor Schemas ====================

class EmissionFactorCreate(BaseModel):
    """Schema for creating emission factor"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    source: str = Field(..., max_length=255)
    scope: int = Field(..., ge=1, le=3)
    category: str = Field(..., max_length=100)
    subcategory: Optional[str] = None
    factor_value: float = Field(..., gt=0)
    factor_unit: str = Field(..., max_length=50)
    region: Optional[str] = None
    country: Optional[str] = None
    effective_date: datetime


class EmissionFactorResponse(BaseModel):
    """Schema for emission factor response"""
    id: str
    name: str
    source: str
    scope: int
    category: str
    subcategory: Optional[str]
    factor_value: float
    factor_unit: str
    region: Optional[str]
    country: Optional[str]
    activity_id: Optional[str]
    climatiq_id: Optional[str]
    data_version: Optional[str]
    year: Optional[int]
    is_active: bool
    effective_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Dashboard Schemas ====================

class EmissionSummaryResponse(BaseModel):
    """Schema for emission summary"""
    total_co2e_kg: float
    total_co2e_tonnes: float
    scope_1_co2e: float
    scope_2_co2e: float
    scope_3_co2e: float
    transaction_count: int
    date_range: dict


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    old_values: Optional[dict]
    new_values: Optional[dict]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrganizationCreate(BaseModel):
    """Organization creation schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(..., min_length=1, max_length=255, description="Organization slug (URL-friendly)")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Leading sustainability company"
            }
        }

# ==================== Organization ====================
class OrganizationResponse(BaseModel):
    """Organization response schema"""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "org-a1b2c3d4",
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Leading sustainability company",
                "is_active": True,
                "created_at": "2025-12-01T14:09:00Z",
                "updated_at": "2025-12-01T14:09:00Z"
            }
        }

# ==================== CSV Import Schemas ====================

class CSVImportResponse(BaseModel):
    """Response for CSV import operation"""
    import_id: str
    status: str  # "pending", "processing", "completed", "failed"
    total_rows: Optional[int] = None
    successful_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    errors: Optional[List[dict]] = None
    processing_time_seconds: Optional[float] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "import_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "total_rows": 1000,
                "successful_rows": 995,
                "failed_rows": 5,
                "errors": [
                    {"row": 15, "error": "Invalid scope value"},
                    {"row": 42, "error": "Missing required field: activity_value"}
                ],
                "processing_time_seconds": 12.5
            }
        }

class CSVImportErrorResponse(BaseModel):
    """Error details for CSV import"""
    import_id: str
    total_errors: int
    errors: List[dict]  # [{"row": int, "error": str}]
    
    class Config:
        json_schema_extra = {
            "example": {
                "import_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_errors": 5,
                "errors": [
                    {"row": 15, "error": "Scope must be 1, 2, or 3. Got: 4"},
                    {"row": 20, "error": "Missing required field: scope"},
                    {"row": 42, "error": "Activity value must be positive. Got: -100"}
                ]
            }
        }
# Week 2 features

class EmissionReviewRequest(BaseModel):
    """Schema for reviewing AI classification (US-2.4)"""
    approved: bool = Field(..., description="True to accept AI recommendation, False to override")
    final_scope: Optional[int] = Field(None, ge=1, le=3, description="Manual scope if not approved")
    review_notes: Optional[str] = Field(None, max_length=500, description="Explanation for override")
    
    class Config:
        json_schema_extra = {
            "example": {
                "approved": False,
                "final_scope": 2,
                "review_notes": "This is purchased electricity, not direct combustion"
            }
        }


class EmissionReviewResponse(BaseModel):
    """Schema for review response"""
    transaction_id: str
    final_scope: int
    decision: str  # "AI_APPROVED" or "MANUAL_OVERRIDE"
    reviewed_by: str
    reviewed_at: datetime


class DashboardResponse(BaseModel):
    """Schema for dashboard data (US-2.3)"""
    total_emissions_tonnes: float
    scope_breakdown: Dict[str, float]
    monthly_trend: List[Dict]
    category_breakdown: List[Dict]
    period: Dict[str, Optional[str]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_emissions_tonnes": 1234.567,
                "scope_breakdown": {
                    1: 345.123,
                    2: 456.234,
                    3: 433.210
                },
                "monthly_trend": [
                    {"year": 2024, "month": 1, "date": "2024-01", "emissions_tonnes": 95.234}
                ],
                "category_breakdown": [
                    {"category": "Purchased Electricity", "emissions_tonnes": 456.234, "transaction_count": 12}
                ],
                "period": {
                    "start_date": "2024-01-01T00:00:00Z",
                    "end_date": "2024-12-31T23:59:59Z"
                }
            }
        }


class FactorSearchRequest(BaseModel):
    """Schema for emission factor search"""
    scope: Optional[int] = Field(None, ge=1, le=3)
    category: Optional[str] = None
    region: Optional[str] = None
    search_term: Optional[str] = None
    limit: int = Field(100, ge=1, le=500)


# ==================== Notification Schemas ====================

class FlaggedEvent(BaseModel):
    """Schema for events flagged by the Auditor"""
    event_id: str
    organization_id: str
    event_type: str  # "gap", "anomaly", "compliance"
    description: str
    severity: str  # "low", "medium", "high", "critical"
    details: Dict
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_123",
                "organization_id": "org_abc",
                "event_type": "gap",
                "description": "Missing Scope 1 Heating",
                "severity": "medium",
                "details": {"facility": "Boston", "month": "January"},
                "created_at": "2024-01-15T12:00:00Z"
            }
        }


class NotificationMessage(BaseModel):
    """Schema for WebSocket notifications"""
    type: str  # "ping", "prompt", "alert"
    user_id: str
    content: str
    event_ref: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict] = None

