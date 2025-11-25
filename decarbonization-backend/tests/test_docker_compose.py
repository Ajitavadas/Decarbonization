import pytest
import httpx
import asyncio
from sqlalchemy import text
from app.database import async_session

@pytest.mark.asyncio
async def test_all_services_healthy():
    """Verify all services are healthy within 30 seconds."""
    max_retries = 6
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health/all")
                if response.status_code == 200:
                    data = response.json()
                    assert data["overall_status"] == "healthy"
                    assert data["services"]["api"]["status"] == "healthy"
                    assert data["services"]["postgres"]["status"] == "healthy"
                    assert data["services"]["redis"]["status"] == "healthy"
                    break
        except Exception:
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
            else:
                raise

@pytest.mark.asyncio
async def test_database_connectivity():
    """Verify PostgreSQL connectivity."""
    async with async_session() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

@pytest.mark.asyncio
async def test_timescaledb_extension():
    """Verify TimescaleDB extension is loaded."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT extname FROM pg_extension WHERE extname='timescaledb'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "timescaledb"
