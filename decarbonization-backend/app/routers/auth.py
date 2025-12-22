import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.models import User
from app.schemas.schemas import UserRegister, UserResponse, TokenResponse, UserLogin
from app.utils import get_password_hash
from app.auth.jwt_handler import create_access_token
from app.auth.services import authenticate_user, get_or_create_organization
from app.auth.oauth2_scheme import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Register a new user. 
    """
    # 1. Check if email already exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # 2. Handle Organization
    org_name = user_data.organization_name or f"{user_data.email}'s Org"
    org_id = await get_or_create_organization(db, org_name)

    # 3. Create User
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(
        id=uuid.uuid4(),
        organization_id=org_id,
        email=user_data.email,
        password_hash=hashed_pwd,
        first_name=user_data.full_name.split()[0] if user_data.full_name else "User",
        last_name=user_data.full_name.split()[1] if user_data.full_name and len(user_data.full_name.split()) > 1 else "",
        role="admin",
        is_active=True
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get an access token.
    """
    user = await authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    # 24h expiry for alignment with US-1.1 AC2 and tests
    expires_in = 60 * 60 * 24
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=user,
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_user)
):
    """Get the current authenticated user's profile"""
    return current_user