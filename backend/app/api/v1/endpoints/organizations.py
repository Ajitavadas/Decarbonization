"""
Organization management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.core.security import get_current_user

router = APIRouter()


# Archetype definitions with detailed descriptions for user understanding
ARCHETYPES = [
    {
        "id": "digital_service",
        "name": "The Digital Service",
        "icon": "💻",
        "tagline": "Bytes over barrels",
        "description": "Technology companies, financial services, SaaS providers, and other knowledge-based businesses. Your emissions mainly come from electricity (data centers, offices), business travel, and purchased goods/services. Scope 3 typically dominates your footprint.",
        "examples": ["Software companies", "Banks & Insurance", "Consulting firms", "Tech startups"],
        "dominant_scope": "Scope 3 (70%)"
    },
    {
        "id": "material_transformer",
        "name": "The Material Transformer",
        "icon": "🏭",
        "tagline": "We make things",
        "description": "Manufacturers that transform raw materials into products. Your emissions come from process heat, machinery, and raw material procurement. Expect a more balanced mix across all scopes with significant Scope 1 from combustion.",
        "examples": ["Manufacturing", "Pharmaceuticals", "Chemicals", "Textiles"],
        "dominant_scope": "Scope 1 & 3 (40% each)"
    },
    {
        "id": "structure_builder",
        "name": "The Structure Builder", 
        "icon": "🏗️",
        "tagline": "Building the future",
        "description": "Construction companies and real estate developers. Your emissions are heavily influenced by embodied carbon in materials like concrete and steel, plus on-site equipment fuel. Scope 3 from materials is your biggest challenge.",
        "examples": ["Construction", "Real Estate Development", "Infrastructure", "Architecture"],
        "dominant_scope": "Scope 3 (60%)"
    },
    {
        "id": "mover",
        "name": "The Mover",
        "icon": "🚚",
        "tagline": "Moving the world",
        "description": "Logistics, transportation, and delivery companies. Your business runs on fuel - whether it's jet fuel, diesel, or marine fuel. Scope 1 from your fleet is the dominant source of emissions.",
        "examples": ["Logistics", "Airlines", "Shipping", "Delivery services"],
        "dominant_scope": "Scope 1 (70%)"
    },
    {
        "id": "land_steward",
        "name": "The Land Steward",
        "icon": "🌾",
        "tagline": "From the earth",
        "description": "Agricultural, forestry, and food & beverage businesses. Your emissions include unique sources like livestock methane, fertilizer N2O, and land use changes. These biological emissions set you apart from other archetypes.",
        "examples": ["Farming", "Food & Beverage", "Forestry", "Livestock"],
        "dominant_scope": "Scope 1 (50%)"
    },
    {
        "id": "energy_producer",
        "name": "The Energy Producer",
        "icon": "⚡",
        "tagline": "Powering progress",
        "description": "Utilities, oil & gas, and mining companies. Your direct emissions from fuel combustion and fugitive emissions (like methane leaks) dominate your footprint. Scope 1 is typically 85%+ of your total.",
        "examples": ["Power generation", "Oil & Gas", "Mining", "Renewable energy"],
        "dominant_scope": "Scope 1 (85%)"
    },
    {
        "id": "retailer",
        "name": "The Retailer",
        "icon": "🛒",
        "tagline": "Connecting consumers",
        "description": "Retail, e-commerce, and hospitality businesses. Your emissions come from store operations (electricity, heating) and your supply chain. Scope 3 from purchased goods and logistics is usually your largest category.",
        "examples": ["Retail stores", "E-commerce", "Hotels", "Restaurants"],
        "dominant_scope": "Scope 3 (60%)"
    }
]


class OrganizationResponse(BaseModel):
    id: str
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    emission_archetype: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None


class SetArchetypeRequest(BaseModel):
    archetype: str


class ArchetypeItem(BaseModel):
    id: str
    name: str
    icon: str
    tagline: str
    description: str
    examples: List[str]
    dominant_scope: str


class ArchetypeListResponse(BaseModel):
    archetypes: List[Dict[str, Any]]


@router.get("/archetypes", response_model=ArchetypeListResponse)
async def get_archetypes():
    """
    Get all available emission archetypes with detailed descriptions
    
    Returns the 7 universal emission archetypes that organizations
    can identify with for better anomaly detection and benchmarking.
    """
    return {"archetypes": ARCHETYPES}


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
        emission_archetype=org.emission_archetype,
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
        emission_archetype=org.emission_archetype,
        is_active=org.is_active
    )


@router.patch("/archetype", response_model=OrganizationResponse)
async def set_organization_archetype(
    request: SetArchetypeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set the emission archetype for the current user's organization
    
    This archetype is used by the Carbon Auditor to provide
    industry-specific anomaly detection and benchmarking.
    """
    # Validate archetype
    valid_archetypes = [a["id"] for a in ARCHETYPES]
    if request.archetype not in valid_archetypes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid archetype. Must be one of: {', '.join(valid_archetypes)}"
        )
    
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
    
    org.emission_archetype = request.archetype
    db.commit()
    db.refresh(org)
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        industry=org.industry,
        country=org.country,
        emission_archetype=org.emission_archetype,
        is_active=org.is_active
    )

