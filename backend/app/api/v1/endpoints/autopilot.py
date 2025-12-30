"""
Autopilot endpoints
AI-powered emission factor suggestions and automated estimation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.activity import EmissionActivity
from app.schemas import (
    AutopilotSuggestRequestSchema,
    AutopilotEstimateRequestSchema,
    EstimateResponseSchema
)
from app.integration.climatiq.service import ClimatiqService
from app.core.security import get_current_user

router = APIRouter()
climatiq_service = ClimatiqService()


@router.post("/suggest")
async def suggest_emission_factors(
    request: AutopilotSuggestRequestSchema,
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered emission factor suggestions
    
    Uses NLP to match natural language descriptions to emission factors
    Returns multiple suggestions with confidence scores
    """
    try:
        result = await climatiq_service.suggest_emission_factors(
            description=request.query,
            domain=request.domain
        )
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate", response_model=EstimateResponseSchema)
async def autopilot_estimate(
    request: AutopilotEstimateRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Combined suggestion + estimation
    
    One-step process:
    1. AI suggests best emission factor
    2. Calculates emissions
    3. Returns result with explanation
    """
    try:
        result = await climatiq_service.calculate_with_autopilot(
            description=request.query,
            parameters=request.parameters
        )
        
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="autopilot",
                sub_type="automated",
                scope="Scope 3",  # Default, could be refined
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=result["co2e"],
                emission_factor_id=result["activity_id"],
                input_data={
                    "query": request.query,
                    "parameters": request.parameters,
                    "confidence": result.get("confidence"),
                    "source_trail": result.get("source_trail")
                },
                description=f"Autopilot: {request.query}"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
