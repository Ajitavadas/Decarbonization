import pytest
from httpx import AsyncClient

# Test Data
VALID_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "Password123!", 
    "full_name": "Test User",
    "organization_name": "Test Corp"
}

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """
    US-1.1 AC3: Test successful registration.
    Also validates Organization auto-creation logic.
    """
    response = await client.post("/auth/register", json=VALID_USER)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == VALID_USER["email"]
    assert "id" in data
    # Check if organization was created automatically
    assert "organization_id" in data
    assert data["is_active"] is True

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """
    US-1.1 AC4: Error handling for duplicates.
    """
    # Register once
    await client.post("/auth/register", json=VALID_USER)
    
    # Register again
    response = await client.post("/auth/register", json=VALID_USER)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """
    US-1.1 AC1 & AC2: Secure login and JWT generation.
    """
    # 1. Register
    await client.post("/auth/register", json=VALID_USER)
    
    # 2. Login (OAuth2 form data)
    login_data = {
        "username": VALID_USER["email"], # Using email as username per logic
        "password": VALID_USER["password"]
    }
    response = await client.post("/auth/token", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """
    US-1.1 AC4: Error handling for bad password.
    """
    # 1. Register
    await client.post("/auth/register", json=VALID_USER)
    
    # 2. Login with wrong password
    login_data = {
        "username": VALID_USER["email"],
        "password": "WrongPassword123!"
    }
    response = await client.post("/auth/token", data=login_data)
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_password_strength(client: AsyncClient):
    """
    US-1.1 AC: Password complexity validation.
    """
    weak_user = VALID_USER.copy()
    weak_user["password"] = "weak" # No digits, no special chars, too short
    
    response = await client.post("/auth/register", json=weak_user)
    assert response.status_code == 422 # Validation Error