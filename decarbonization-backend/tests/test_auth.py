# tests/test_auth.py
"""
Authentication tests for US-1.1
- User registration
- User login
- JWT token validation
- Password hashing
- Error handling
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.models import Base, User, Organization


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_local = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db():
        async with async_session_local() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test organization
    async with async_session_local() as session:
        test_org = Organization(
            id="test-org-1",
            name="Test Organization",
            slug="test-org",
        )
        session.add(test_org)
        await session.commit()
    
    yield async_session_local
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_user_registration_success(test_db):
    """Test successful user registration - AC3-S1.1"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123!",
                "full_name": "Test User",
                "organization_id": "test-org-1",
            },
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_user_registration_duplicate_email(test_db):
    """Test registration fails with duplicate email"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First registration
        response1 = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser1",
                "password": "SecurePass123!",
                "organization_id": "test-org-1",
            },
        )
        assert response1.status_code == 201
        
        # Duplicate email
        response2 = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser2",
                "password": "SecurePass123!",
                "organization_id": "test-org-1",
            },
        )
        assert response2.status_code == 409
        assert "already registered" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_user_registration_duplicate_username(test_db):
    """Test registration fails with duplicate username"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First registration
        response1 = await client.post(
            "/auth/register",
            json={
                "email": "test1@example.com",
                "username": "testuser",
                "password": "SecurePass123!",
                "organization_id": "test-org-1",
            },
        )
        assert response1.status_code == 201
        
        # Duplicate username
        response2 = await client.post(
            "/auth/register",
            json={
                "email": "test2@example.com",
                "username": "testuser",
                "password": "SecurePass123!",
                "organization_id": "test-org-1",
            },
        )
        assert response2.status_code == 409
        assert "already taken" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_user_login_success(test_db):
    """Test successful user login - AC2-S1.1"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        register_response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123!",
                "organization_id": "test-org-1",
            },
        )
        assert register_response.status_code == 201
        
        # Login
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )
    
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1440 * 60  # 24 hours in seconds
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_user_login_invalid_credentials(test_db):
    """Test login fails with invalid credentials - AC4-S1.1"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123!",
                "organization_id": "test-org-1",
            },
        )
        
        # Login with wrong password
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!",
            },
        )
    
    assert login_response.status_code == 401
    assert "Invalid credentials" in login_response.json()["detail"]


@pytest.mark.asyncio
async def test_user_login_nonexistent_user(test_db):
    """Test login fails for nonexistent user"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SecurePass123!",
            },
        )
    
    assert login_response.status_code == 401
    assert "Invalid credentials" in login_response.json()["detail"]


@pytest.mark.asyncio
async def test_password_strength_validation(test_db):
    """Test password strength requirements"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # No uppercase
        response = await client.post(
            "/auth/register",
            json={
                "email": "test1@example.com",
                "username": "testuser1",
                "password": "securepass123!",
                "organization_id": "test-org-1",
            },
        )
        assert response.status_code == 422
        
        # No digit
        response = await client.post(
            "/auth/register",
            json={
                "email": "test2@example.com",
                "username": "testuser2",
                "password": "SecurePass!",
                "organization_id": "test-org-1",
            },
        )
        assert response.status_code == 422
        
        # No special character
        response = await client.post(
            "/auth/register",
            json={
                "email": "test3@example.com",
                "username": "testuser3",
                "password": "SecurePass123",
                "organization_id": "test-org-1",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_current_user(test_db):
    """Test getting current user information"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login
        await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123!",
                "organization_id": "test-org-1",
            },
        )
        
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )
        
        token = login_response.json()["access_token"]
        
        # Get current user
        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_logout(test_db):
    """Test logout functionality"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login
        await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123!",
                "organization_id": "test-org-1",
            },
        )
        
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )
        
        token = login_response.json()["access_token"]
        
        # Logout
        logout_response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
    
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out successfully"
