import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
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