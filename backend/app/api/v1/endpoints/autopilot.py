"""
Autopilot endpoints
AI-powered emission factor suggestions and automated estimation

NOTE: Autopilot is an ADD-ON feature that requires explicit opt-in from Climatiq.
Contact Climatiq at https://www.climatiq.io/contact-us to enable this feature.
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
    Get AI-powered emission factor suggestions (Autopilot Suggest v1-preview4)
    
    NOTE: Requires Autopilot ADD-ON enabled on your Climatiq account.
    
    Uses NLP to match natural language descriptions to emission factors.
    Returns multiple suggestions with suggestion_ids for use with /estimate/with-suggestion.
    
    Examples:
    - text: "Cement" -> finds cement-related emission factors
    - text: "Polypropylene" with unit_type: ["Weight"] -> finds material emission factors
    - text: "Laptop" -> finds electronics-related factors
    """
    try:
        result = await climatiq_service.suggest_emission_factors(
            text=request.text,
            max_suggestions=request.max_suggestions,
            unit_type=request.unit_type,
            region=request.region,
            year=request.year,
            source=request.source,
            scope=request.scope
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
    One-shot estimation (Autopilot One-shot Estimate v1-preview4)
    
    NOTE: Requires Autopilot ADD-ON enabled on your Climatiq account.
    
    One-step process:
    1. AI suggests best emission factor based on text
    2. Calculates emissions using provided amount
    3. Returns result with explanation
    
    Examples:
    - text: "Steel", amount: 100, unit: "usd", unit_type: "money"
    - text: "Cement", amount: 100, unit: "kg", unit_type: "weight", region: "DE"
    - text: "Brown Rice", amount: 10, unit: "t", unit_type: "weight", region: "ZA"
    """
    try:
        result = await climatiq_service.calculate_with_autopilot(
            text=request.text,
            amount=request.amount,
            unit=request.unit,
            unit_type=request.unit_type,
            region=request.region,
            year=request.year,
            scope=request.scope
        )
        
        # Extract co2e from nested estimate object (v1-preview4 format)
        estimate = result.get("estimate", {})
        co2e = estimate.get("co2e", result.get("co2e", 0))
        
        if request.project_id:
            # Determine scope from emission factor info
            emission_factor = estimate.get("emission_factor", {})
            scopes = emission_factor.get("scopes", ["3"])
            scope_str = f"Scope {scopes[0]}" if scopes else "Scope 3"
            
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="autopilot",
                sub_type="automated",
                scope=scope_str,
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=co2e,
                emission_factor_id=emission_factor.get("activity_id"),
                input_data={
                    "text": request.text,
                    "amount": float(request.amount),
                    "unit": request.unit,
                    "unit_type": request.unit_type,
                    "model": result.get("model"),
                    "model_version": result.get("model_version"),
                    "source_trail": result.get("source_trail")
                },
                description=f"Autopilot: {request.text} ({request.amount} {request.unit})"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": {"co2e_kg": co2e, "scope": "Scope 3", "raw_response": result}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
