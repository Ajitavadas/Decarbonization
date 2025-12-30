"""
API v1 Router - Aggregates all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    estimate,
    travel,
    energy,
    freight,
    procurement,
    autopilot,
    mappings,
    activities,
    projects,
    batch
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(estimate.router, prefix="/estimate", tags=["Estimates"])
api_router.include_router(travel.router, prefix="/travel", tags=["Travel"])
api_router.include_router(energy.router, prefix="/energy", tags=["Energy"])
api_router.include_router(freight.router, prefix="/freight", tags=["Freight"])
api_router.include_router(procurement.router, prefix="/procurement", tags=["Procurement"])
api_router.include_router(autopilot.router, prefix="/autopilot", tags=["Autopilot"])
api_router.include_router(mappings.router, prefix="/mappings", tags=["Custom Mappings"])
api_router.include_router(activities.router, prefix="/activities", tags=["Activities"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(batch.router, prefix="/batch", tags=["Batch Operations"])
