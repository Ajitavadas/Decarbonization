import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.models import User, Organization
from app.utils import verify_password

async def get_or_create_organization(db: AsyncSession, org_name: str, org_slug: str = None) -> str:
    """
    Finds an organization by slug, or creates it if it doesn't exist.
    Returns the Organization ID.
    """
    # 1. Generate slug if not provided (simple lowercase replacement)
    if not org_slug:
        org_slug = re.sub(r'[^a-z0-9]+', '-', org_name.lower()).strip('-')

    # 2. Check if exists
    result = await db.execute(select(Organization).filter(Organization.slug == org_slug))
    existing_org = result.scalars().first()

    if existing_org:
        return existing_org.id

    # 3. Create new if not found
    new_org_id = f"org-{str(uuid.uuid4())[:8]}"
    new_org = Organization(
        id=new_org_id,
        name=org_name,
        slug=org_slug,
        is_active=True
    )
    db.add(new_org)
    # We flush here so the ID is available, but commit happens in the main transaction later
    await db.flush() 
    
    return new_org_id

async def authenticate_user(db: AsyncSession, username_or_email: str, password: str):
    """
    Verifies user credentials using either username or email.
    Returns User object or False.
    """
    # Try to find user by email first, then by username
    result = await db.execute(
        select(User).filter(
            (User.email == username_or_email) | (User.username == username_or_email)
        )
    )
    user = result.scalars().first()

    if not user:
        return False
    
    if not verify_password(password, user.hashed_password):
        return False
        
    return user