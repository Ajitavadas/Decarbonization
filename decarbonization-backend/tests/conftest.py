# tests/conftest.py
"""
Pytest Configuration - FIXED: Import Base from correct module
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import patch, MagicMock
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models.models import Base  # ✅ FIXED: Import from models, not database
from app.config import settings
from app.models.models import Organization, User
from app.utils import get_password_hash
import google.generativeai as genai

# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://decarb_user:decarb_password@postgres:5432/decarb_test_db"

# Test engine with proper isolation
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

# Test session factory
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False, future=True)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create session-scoped event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Setup test DB once per session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Transaction isolation per test"""
    async with TestingSessionLocal() as session:
        async with session.begin():
            yield session
        # Transaction automatically rolls back here

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test client with AI mocking"""
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # Mock Gemini AI globally for all tests
    with patch.object(genai, 'configure'), \
         patch.object(genai.GenerativeModel, 'generate_content_async') as mock_ai:
        
        mock_response = MagicMock()
        mock_response.text = '{"scope": 2, "confidence": 0.90}'
        mock_ai.return_value = mock_response
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    
    app.dependency_overrides.clear()

# AI Mocking Fixture
@pytest.fixture
def mock_gemini():
    """Provide customizable Gemini AI mock"""
    with patch.object(genai, 'configure'), \
         patch.object(genai.GenerativeModel, 'generate_content_async') as mock_generate:
        
        mock_response = MagicMock()
        mock_response.text = '{"scope": 2, "confidence": 0.90}'
        mock_generate.return_value = mock_response
        
        def setup(scope: int = 2, confidence: float = 0.90):
            mock_response.text = f'{{"scope": {scope}, "confidence": {confidence}}}'
        
        yield {
            'setup': setup,
            'mock': mock_generate
        }

# Test data fixtures
@pytest_asyncio.fixture
async def test_org(db_session):
    org = Organization(id="test-org-123", name="Test Org", slug="test-org", is_active=True)
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org

@pytest_asyncio.fixture
async def test_user(db_session, test_org):
    user = User(
        id="test-user-123",
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test User",
        organization_id=test_org.id,
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def auth_headers(client, test_user):
    """Get authenticated headers for test user"""
    response = await client.post("/auth/token", data={
        "username": test_user.email,
        "password": "TestPass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Data fixtures
@pytest.fixture
def valid_csv_content():
    return b"""description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value,supplier_name
Electricity for office,2025-01-15,2,Electricity,1000,kWh,0.5,GridCo
Gas for heating,2025-01-16,1,Fuel,500,liters,2.3,GasCompany
Flight to conference,2025-01-17,3,Business Travel,2000,miles,0.18,Airline"""

@pytest.fixture
def csv_with_errors():
    return b"""description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value
Invalid scope,2025-01-15,4,Electricity,100,kWh,0.5
Negative value,2025-01-16,1,Fuel,-50,liters,2.3"""

@pytest.fixture
def large_csv_content():
    rows = ["description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value"]
    for i in range(1000):
        rows.append(f"Transaction {i},2025-01-15,1,Fuel,100,liters,2.3")
    return "\n".join(rows).encode('utf-8')

# Settings fixture
@pytest.fixture(autouse=True)
def configure_test_settings():
    settings.ENVIRONMENT = "testing"
    settings.DEBUG = False
    settings.SECRET_KEY = "test-secret-key"
    settings.GEMINI_API_KEY = "test-gemini-key"
    settings.AI_MIN_CONFIDENCE_THRESHOLD = 0.80

def create_test_transaction(
    org_id: str,
    user_id: str,
    scope: int = 1,
    co2e_tonnes: float = 10.0,
    category: str = "Test Category",
    transaction_date: datetime = None,
    ai_needs_review: bool = False,
    ai_scope_prediction: int = None,
    ai_confidence_score: float = None
) -> EmissionTransaction:
    """Helper to create test emission transactions"""
    if transaction_date is None:
        transaction_date = datetime.now(timezone.utc)
    
    return EmissionTransaction(
        organization_id=org_id,
        description="Test transaction",
        transaction_date=transaction_date,
        scope=scope,
        category=category,
        activity_value=100.0,
        activity_unit="kwh",
        emission_factor_value=0.5,
        co2e_kg=co2e_tonnes * 1000,
        co2e_tonnes=co2e_tonnes,
        ai_scope_prediction=ai_scope_prediction,
        ai_confidence_score=ai_confidence_score,
        ai_needs_review=ai_needs_review,
        created_by_user_id=user_id
    )
