"""
Authorization helpers for multi-tenant data isolation.

These helpers ensure users can only access resources belonging to their organization.
Returns 404 (not 403) to avoid leaking information about resource existence.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.batch_job import BatchJob
from app.models.activity import EmissionActivity
from app.models.user import User


def verify_project_access(db: Session, project_id: str, user: User) -> Project:
    """
    Verify user has access to the specified project.
    
    Args:
        db: Database session
        project_id: Project ID to check
        user: Current authenticated user
        
    Returns:
        Project if access is granted
        
    Raises:
        HTTPException 404 if project doesn't exist or user doesn't have access
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.organization_id != user.organization_id:
        # Return 404 to avoid leaking info about resource existence
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


def verify_activity_access(db: Session, activity_id: str, user: User) -> EmissionActivity:
    """
    Verify user has access to the specified activity.
    
    Args:
        db: Database session
        activity_id: Activity ID to check
        user: Current authenticated user
        
    Returns:
        EmissionActivity if access is granted
        
    Raises:
        HTTPException 404 if activity doesn't exist or user doesn't have access
    """
    activity = db.query(EmissionActivity).filter(EmissionActivity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check via project ownership
    project = db.query(Project).filter(Project.id == activity.project_id).first()
    if not project or project.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return activity


def verify_batch_job_access(db: Session, job_id: str, user: User) -> BatchJob:
    """
    Verify user has access to the specified batch job.
    
    Args:
        db: Database session
        job_id: Batch job ID to check
        user: Current authenticated user
        
    Returns:
        BatchJob if access is granted
        
    Raises:
        HTTPException 404 if job doesn't exist or user doesn't have access
    """
    job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check via project ownership
    project = db.query(Project).filter(Project.id == job.project_id).first()
    if not project or project.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job
