"""
API v1 Router - Aggregates all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    upload,
    activities,
    projects,
    batch,
    organizations,
    reports,
    audit,
    targets,
    copilot
)

api_router = APIRouter()

# Include essential endpoint routers only
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(upload.router, prefix="/upload", tags=["File Upload"])
api_router.include_router(activities.router, prefix="/activities", tags=["Activities"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(batch.router, prefix="/batch", tags=["Batch Operations"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(audit.router, prefix="/audit", tags=["Carbon Auditor"])
api_router.include_router(targets.router, prefix="/targets", tags=["Reduction Targets"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["Carbon Copilot"])


