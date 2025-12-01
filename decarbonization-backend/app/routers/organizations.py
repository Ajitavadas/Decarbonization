"""Organization management router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
import uuid

from app.database import get_db
from app.models.models import Organization
from app.schemas.schemas import OrganizationCreate, OrganizationResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new organization
    
    Args:
        org_data: Organization name and slug
        db: Database session
        
    Returns:
        OrganizationResponse: Created organization
        
    Raises:
        HTTPException: If slug already exists
    """
    try:
        # Generate organization ID
        org_id = f"org-{str(uuid.uuid4())[:8]}"
        
        # Check if slug already exists
        result = await db.execute(
            select(Organization).where(Organization.slug == org_data.slug)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization slug already exists"
            )
        
        # Create organization
        organization = Organization(
            id=org_id,
            name=org_data.name,
            slug=org_data.slug,
            description=org_data.description,
        )
        
        db.add(organization)
        await db.commit()
        await db.refresh(organization)
        
        return OrganizationResponse.model_validate(organization)
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization already exists"
        )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get organization by ID
    
    Args:
        org_id: Organization ID
        db: Database session
        
    Returns:
        OrganizationResponse: Organization data
        
    Raises:
        HTTPException: If organization not found
    """
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse.model_validate(organization)


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
):
    """
    List all organizations
    
    Args:
        db: Database session
        
    Returns:
        list[OrganizationResponse]: All organizations
    """
    result = await db.execute(select(Organization))
    organizations = result.scalars().all()
    return [OrganizationResponse.model_validate(org) for org in organizations]
