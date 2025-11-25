from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from app.database import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def api_health():
    """Basic API health check."""
    return {"status": "healthy", "service": "api"}

@router.get("/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    """PostgreSQL health check."""
    try:
        result = await db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "postgres"}
    except Exception as e:
        return {"status": "unhealthy", "service": "postgres", "error": str(e)}, 500

@router.get("/redis")
async def redis_health():
    """Redis health check."""
    try:
        redis_client = redis.from_url("redis://redis:6379")
        await redis_client.ping()
        await redis_client.close()
        return {"status": "healthy", "service": "redis"}
    except Exception as e:
        return {"status": "unhealthy", "service": "redis", "error": str(e)}, 500

@router.get("/all")
async def all_services_health(db: AsyncSession = Depends(get_db)):
    """Check all service dependencies."""
    checks = {}
    
    # API
    checks["api"] = {"status": "healthy"}
    
    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = {"status": "healthy"}
    except Exception as e:
        checks["postgres"] = {"status": "unhealthy", "error": str(e)}
    
    # Redis
    try:
        redis_client = redis.from_url("redis://redis:6379")
        await redis_client.ping()
        await redis_client.close()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
    
    all_healthy = all(v["status"] == "healthy" for v in checks.values())
    return {
        "overall_status": "healthy" if all_healthy else "degraded",
        "services": checks
    }
