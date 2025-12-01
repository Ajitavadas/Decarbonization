# app/main.py
"""
FastAPI Application Entry Point
- Application initialization
- Router registration
- Middleware configuration
- Startup/shutdown events
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.routers import health
from app.routers import organizations
# app.include_router(organizations.router)
from app.routers.auth import router as auth_router
from app.database import init_db, close_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Decarbonization Platform API")
    await init_db()
    logger.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down API")
    await close_db()
    logger.info("✅ Database connection closed")


# Create FastAPI app
app = FastAPI(
    title="Decarbonization Platform API",
    version="1.0.0",
    description="Carbon emissions tracking and management platform",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth_router, tags=["authentication"])


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "status": "Decarbonization Platform API Running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


# Health check endpoint
@app.get("/health/ready", tags=["health"])
async def readiness():
    """Readiness probe for Kubernetes"""
    return {"status": "ready"}
