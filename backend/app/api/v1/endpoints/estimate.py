"""
Estimate endpoints
Single and batch emission estimation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.activity import EmissionActivity
from app.schemas import (
    EstimateRequestSchema,
    EstimateResponseSchema,
    BatchEstimateRequestSchema,
    BatchEstimateResponseSchema
)
from app.services.calculation_engine import calculation_engine
from app.core.security import get_current_user
from app.core.errors import ClimatiqAPIError

router = APIRouter()


@router.post("/single", response_model=EstimateResponseSchema)
async def calculate_single_estimate(
    request: EstimateRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate single emission estimate
    
    Automatically:
    - Classifies into correct scope (1, 2, or 3)
    - Caches result for future requests
    - Saves to database if project_id provided
    """
    try:
        # Calculate emission
        result = await calculation_engine.calculate_emission(
            activity_type=request.activity_type,
            activity_id=request.activity_id,
            parameters=request.parameters,
            region=request.region,
            year=request.year,
            sub_type=request.sub_type,
            use_cache=True
        )
        
        # Save to database if project_id provided
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type=request.activity_type,
                sub_type=request.sub_type,
                scope=result["scope"],
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=result["co2e_kg"],
                co2e_unit=result["co2e_unit"],
                calculation_method=result["calculation_method"],
                constituent_gases=result.get("constituent_gases"),
                input_data=result["input_data"],
                emission_factor_id=request.activity_id,
                source_dataset=result.get("source_dataset"),
                region=request.region,
                year=str(request.year) if request.year else None,
                description=request.description
            )
            db.add(activity)
            db.commit()
            db.refresh(activity)
            
            result["activity_id"] = str(activity.id)
        
        return {
            "success": True,
            "message": "Emission calculated successfully",
            "data": result
        }
        
    except ClimatiqAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchEstimateResponseSchema)
async def calculate_batch_estimates(
    request: BatchEstimateRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate batch emissions (async processing)
    
    For large batches:
    - Creates a batch job for tracking
    - Processes asynchronously with Celery
    - Returns job ID for status polling
    """
    from app.models.batch_job import BatchJob
    from app.tasks.batch_processing import process_batch_estimates
    
    # Create batch job
    job = BatchJob(
        job_type="batch_estimate",
        status="queued",
        total_records=len(request.estimates),
        project_id=request.project_id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Queue async task
    task = process_batch_estimates.delay(
        job_id=str(job.id),
        project_id=str(request.project_id),
        estimates=request.estimates
    )
    
    job.celery_task_id = task.id
    db.commit()
    
    return {
        "success": True,
        "message": "Batch job queued for processing",
        "job_id": job.id,
        "status": job.status,
        "total_records": job.total_records
    }
