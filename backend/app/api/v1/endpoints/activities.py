"""
Activities endpoints
View and manage emission activities
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.schemas import ActivityResponse, ActivitySummary, PaginatedResponse
from app.crud.crud_activity import crud_activity
from app.core.security import get_current_user

router = APIRouter()


@router.get("/", response_model=List[ActivityResponse])
async def list_activities(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    scope: Optional[str] = None,
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List activities for a project
    
    Optional filters: scope, activity_type
    """
    if scope:
        activities = crud_activity.get_by_scope(db, project_id=project_id, scope=scope)
    else:
        activities = crud_activity.get_by_project(
            db,
            project_id=project_id,
            skip=skip,
            limit=limit
        )
    
    # Apply activity_type filter if provided
    if activity_type:
        activities = [a for a in activities if a.activity_type == activity_type]
    
    return activities


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific activity details"""
    activity = crud_activity.get(db, id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.get("/project/{project_id}/summary", response_model=ActivitySummary)
async def get_project_summary(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary statistics for a project
    
    Returns:
    - Total CO2e
    - Breakdown by scope
    - Breakdown by activity type
    - Total number of activities
    """
    total_emissions = crud_activity.get_total_emissions(db, project_id=project_id)
    scope_breakdown = crud_activity.get_emissions_by_scope(db, project_id=project_id)
    activity_breakdown = crud_activity.get_emissions_by_activity_type(db, project_id=project_id)
    total_count = crud_activity.count(db, filters={"project_id": project_id})
    
    return {
        "total_activities": total_count,
        "total_co2e_kg": total_emissions,
        "scope_breakdown": scope_breakdown,
        "activity_type_breakdown": activity_breakdown
    }


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an activity"""
    activity = crud_activity.get(db, id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    crud_activity.delete(db, id=activity_id)
    return {"success": True, "message": "Activity deleted"}
