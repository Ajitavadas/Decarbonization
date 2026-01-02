"""
Authentication endpoints
User registration, login, and token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, ResponseBase
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register new user with organization"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create organization for new user
    org_name = f"{user_in.full_name}'s Organization" if user_in.full_name else f"{user_in.email.split('@')[0]}'s Organization"
    org = Organization(
        name=org_name,
        is_active=True
    )
    db.add(org)
    db.flush()  # Get org.id before creating user
    
    # Create new user with organization
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        organization_id=org.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """User login"""
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/logout", response_model=ResponseBase)
async def logout(current_user: User = Depends(get_current_user)):
    """
    User logout
    Note: With JWT, logout is handled client-side by removing the token
    """
    return {"success": True, "message": "Successfully logged out"}
