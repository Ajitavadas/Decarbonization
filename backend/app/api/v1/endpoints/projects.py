"""
Projects endpoints
Manage reporting projects
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas import ProjectCreate, ProjectResponse
from app.core.security import get_current_user
from app.core.authorization import verify_project_access

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new reporting project"""
    # Ensure user has an organization
    if not current_user.organization_id:
        from app.models.organization import Organization
        # Create default organization
        org = Organization(
            name=f"{current_user.full_name or current_user.email}'s Organization",
            is_active=True
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        current_user.organization_id = org.id
        db.commit()
    
    # Use current user's organization_id (override if provided in request)
    project_data = project_in.dict()
    project_data["organization_id"] = current_user.organization_id
    
    project = Project(**project_data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects for user's organization"""
    projects = (
        db.query(Project)
        .filter(Project.organization_id == current_user.organization_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific project"""
    # verify_project_access checks both existence AND organization ownership
    project = verify_project_access(db, project_id, current_user)
    return project
