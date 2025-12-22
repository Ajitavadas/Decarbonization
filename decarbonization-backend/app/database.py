# app/database.py
"""
Database configuration and session management
- Async PostgreSQL connection with SQLAlchemy
- Session factory for dependency injection
- Database initialization utilities
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import os
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,  # Use NullPool to avoid connection pooling issues in containerized environments
    future=True,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session
    
    Usage:
        db: AsyncSession = Depends(get_db)
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables
    
    Call this once at startup to create all tables
    """
    async with engine.begin() as conn:
        # Enable PostGIS extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        
        # Import models to register them with Base
        from app.models.models import Base
        import app.models.agents  # Register AgentState

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables():
    """
    Drop all database tables
    
    WARNING: This will delete all data. Use with caution!
    """
    async with engine.begin() as conn:
        from app.models.models import Base
        import app.models.agents

        await conn.run_sync(Base.metadata.drop_all)


async def close_db():
    """Close database connection"""
    await engine.dispose()

__all__ = ['get_db', 'init_db', 'drop_all_tables', 'close_db', 'async_session', 'engine']