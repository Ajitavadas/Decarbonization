# app/schemas/schemas.py
"""
Pydantic schemas for request/response validation
- User registration and login
- Emission transaction management
- Emission factor handling
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional


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
    """Schema for user response"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    organization_id: str
    created_at: datetime
    last_login: Optional[datetime]
    
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


class EmissionTransactionResponse(BaseModel):
    """Schema for emission transaction response"""
    id: str
    organization_id: str
    description: str
    transaction_date: datetime
    scope: int
    category: str
    activity_value: float
    activity_unit: str
    co2e_kg: float
    co2e_tonnes: float
    ai_scope_prediction: Optional[int]
    ai_confidence_score: Optional[float]
    ai_needs_review: bool
    supplier_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
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