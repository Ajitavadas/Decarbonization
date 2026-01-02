"""
Organization management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.core.security import get_current_user

router = APIRouter()


class OrganizationResponse(BaseModel):
    id: str
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None


@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no organization"
        )
    
    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        industry=org.industry,
        country=org.country,
        is_active=org.is_active
    )


@router.put("/me", response_model=OrganizationResponse)
async def update_my_organization(
    update_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no organization"
        )
    
    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields if provided
    if update_data.name is not None:
        org.name = update_data.name
    if update_data.industry is not None:
        org.industry = update_data.industry
    if update_data.country is not None:
        org.country = update_data.country
    
    db.commit()
    db.refresh(org)
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        industry=org.industry,
        country=org.country,
        is_active=org.is_active
    )
