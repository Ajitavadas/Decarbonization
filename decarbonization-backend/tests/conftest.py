import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, timezone
from app.models.models import (
    Base, User, Organization, EmissionTransaction, EmissionFactor
)
from app.auth.jwt_handler import create_access_token
import uuid
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import get_db
from app.models.models import Base
from app.config import settings

# Override the database URL for testing to ensure isolation.
# Point at the postgres service inside docker-compose and a dedicated test DB.
TEST_DATABASE_URL = "postgresql+asyncpg://decarb_user:decarb_password@postgres:5432/decarb_test_db"

# Create a specific engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Create tables once at the start of the test session 
    and drop them at the end.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a fresh SQLAlchemy session for each test.
    Let the application manage transactions (commit/rollback) per request.
    """
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture
    to override the `get_db` dependency.
    """
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass # Session is closed by the fixture above

    app.dependency_overrides[get_db] = override_get_db
    
    # ASGITransport is needed for newer httpx versions with FastAPI
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def test_org(db_session):
    """Create test organization"""
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Organization",
        slug="test-org",
        is_active=True
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org

@pytest.fixture
async def test_user(db_session, test_org):
    """Create test user"""
    from app.utils import get_password_hash
    
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPassword123!"),
        organization_id=test_org.id,
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_admin_user(db_session, test_org):
    """Create test admin user"""
    from app.utils import get_password_hash
    
    user = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("AdminPassword123!"),
        organization_id=test_org.id,
        is_active=True,
        is_admin=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
def test_user_token(test_user):
    """Create JWT token for test user"""
    return create_access_token(data={"sub": test_user.id})

@pytest.fixture
def admin_token(test_admin_user):
    """Create JWT token for test admin"""
    return create_access_token(data={"sub": test_admin_user.id})

@pytest.fixture
async def test_transaction(db_session, test_user, test_org):
    """Create test emission transaction"""
    tx = EmissionTransaction(
        id=str(uuid.uuid4()),
        organization_id=test_org.id,
        description="Purchased 100 kWh electricity",
        transaction_date=datetime.now(timezone.utc),
        scope=2,
        category="Electricity",
        activity_value=100.0,
        activity_unit="kWh",
        emission_factor_value=0.4,
        co2e_kg=40.0,
        co2e_tonnes=0.04,
        created_by_user_id=test_user.id
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)
    return tx

@pytest.fixture
async def async_client(db_session, test_user_token):
    """Create async HTTP client for testing"""
    from httpx import AsyncClient
    from app.main import app
    
    # Override dependency for testing
    async def override_get_db():
        yield db_session
    
    from app.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()