# app/routers/auth.py
"""
Authentication Router
- User registration (US-1.1 AC3)
- User login with JWT (US-1.1 AC2)
- Password validation with bcrypt hashing (US-1.1 AC1)
- Error handling (US-1.1 AC4)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

from app.database import get_db
from app.models.models import User, Organization, AuditLog
from app.schemas.schemas import UserRegister, UserLogin, UserResponse, TokenResponse, PasswordChangeRequest
from app.auth.jwt_handler import create_access_token
from app.auth.oauth2_scheme import get_current_user
from app.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["authentication"])


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


async def log_audit(
    db: AsyncSession,
    user_id: str,
    organization_id: str,
    action: str,
    resource_type: str,
    resource_id: str = None,
    old_values: dict = None,
    new_values: dict = None,
    description: str = None,
    ip_address: str = None,
) -> None:
    """Create audit log entry"""
    audit_log = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        description=description,
        ip_address=ip_address,
    )
    db.add(audit_log)
    await db.commit()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user
    
    **US-1.1 AC1**: Create user database with bcrypt hashing
    **US-1.1 AC3**: Build login form (username/password input)
    
    Args:
        user_data: User registration data with email, username, password
        db: Database session
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: If email/username already exists
    """
    try:
        # Verify organization exists
        org_result = await db.execute(
            select(Organization).where(Organization.id == user_data.organization_id)
        )
        organization = org_result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Check if email already exists
        email_result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Check if username already exists
        username_result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if username_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
        
        # Create new user with hashed password (bcrypt)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            organization_id=user_data.organization_id,
            is_active=True,
        )
        
        db.add(new_user)
        await db.flush()  # Flush to get the user ID
        
        # Log registration
        await log_audit(
            db=db,
            user_id=new_user.id,
            organization_id=user_data.organization_id,
            action="CREATE",
            resource_type="User",
            resource_id=new_user.id,
            new_values={
                "email": new_user.email,
                "username": new_user.username,
                "full_name": new_user.full_name,
            },
            description=f"User registered: {user_data.email}",
        )
        
        await db.commit()
        await db.refresh(new_user)
        
        return UserResponse.model_validate(new_user)
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    User login endpoint
    
    **US-1.1 AC2**: Set up JWT authentication tokens
    **US-1.1 AC4**: Error handling (show 'Invalid credentials')
    **AC: Sessions active 24 hours**
    
    Args:
        credentials: User email and password
        db: Database session
        
    Returns:
        TokenResponse: JWT access token and user data
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and is active
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    await db.flush()
    
    # Log login
    await log_audit(
        db=db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="LOGIN",
        resource_type="User",
        resource_id=user.id,
        description=f"User logged in: {user.email}",
    )
    
    await db.commit()
    
    # Create access token (24 hour expiration per AC)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change user password
    
    Args:
        password_data: Current and new password
        current_user_id: ID of current user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    user.hashed_password = hash_password(password_data.new_password)
    db.add(user)
    await db.flush()
    
    # Log password change
    await log_audit(
        db=db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="UPDATE",
        resource_type="User",
        resource_id=user.id,
        description="User changed password",
    )
    
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user information
    
    Args:
        current_user_id: ID of current user
        db: Database session
        
    Returns:
        UserResponse: Current user data
    """
    result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.post("/logout")
async def logout(
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user (log the action for audit trail)
    
    Args:
        current_user_id: ID of current user
        db: Database session
        
    Returns:
        dict: Success message
    """
    result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Log logout
        await log_audit(
            db=db,
            user_id=user.id,
            organization_id=user.organization_id,
            action="LOGOUT",
            resource_type="User",
            resource_id=user.id,
            description=f"User logged out: {user.email}",
        )
        await db.commit()
    
    return {"message": "Logged out successfully"}
