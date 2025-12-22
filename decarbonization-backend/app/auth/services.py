import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.models import User, Organization
from app.utils import verify_password

async def get_or_create_organization(db: AsyncSession, org_name: str, org_slug: str = None) -> uuid.UUID:
    """
    Finds an organization by name, or creates it if it doesn't exist.
    """
    # 2. Check if exists
    result = await db.execute(select(Organization).filter(Organization.organization_name == org_name))
    existing_org = result.scalars().first()

    if existing_org:
        return existing_org.id

    # 3. Create new if not found
    new_org = Organization(
        id=uuid.uuid4(),
        organization_name=org_name,
        countries=[],
        is_public_company=False
    )
    db.add(new_org)
    await db.flush() 
    
    return new_org.id

async def authenticate_user(db: AsyncSession, email: str, password: str):
    """
    Verifies user credentials using email.
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        return False
    
    if not verify_password(password, user.password_hash):
        return False
        
    return user