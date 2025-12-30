"""
Batch operations endpoints
Track and manage async batch jobs
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.batch_job import BatchJob
from app.schemas import BatchJobResponse
from app.core.security import get_current_user

router = APIRouter()


@router.get("/jobs", response_model=List[BatchJobResponse])
async def list_batch_jobs(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List batch jobs"""
    query = db.query(BatchJob)
    
    if status:
        query = query.filter(BatchJob.status == status)
    
    jobs = query.order_by(BatchJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=BatchJobResponse)
async def get_batch_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get batch job status
    
    Use for polling job progress during async processing
    """
    job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.delete("/jobs/{job_id}")
async def cancel_batch_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a batch job (if still queued or processing)"""
    job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    # Revoke Celery task
    from app.core.celery_app import celery_app
    if job.celery_task_id:
        celery_app.control.revoke(job.celery_task_id, terminate=True)
    
    job.status = "cancelled"
    db.commit()
    
    return {"success": True, "message": "Job cancelled"}
