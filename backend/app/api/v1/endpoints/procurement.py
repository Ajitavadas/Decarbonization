"""
Procurement calculation endpoints
Spend-based emissions using EEIO models
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.activity import EmissionActivity
from app.schemas import ProcurementCalculationRequest, EstimateResponseSchema
from app.integration.climatiq.service import ClimatiqService
from app.core.security import get_current_user

router = APIRouter()
climatiq_service = ClimatiqService()


@router.post("/calculate", response_model=EstimateResponseSchema)
async def calculate_procurement(
    request: ProcurementCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate procurement emissions from spend data
    
    Uses EEIO (Environmentally-Extended Input-Output) models
    Critical: spend_year is required for inflation adjustment
    """
    try:
        result = await climatiq_service.calculate_procurement_emissions(
            spend_amount=request.amount,
            currency=request.currency,
            spend_year=request.spend_year,
            classification_code=request.classification_code,
            classification_type=request.classification_type
        )
        
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="procurement",
                sub_type="spend_based",
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=result["co2e"],
                year=str(request.spend_year),
                input_data={
                    "amount": float(request.amount),
                    "currency": request.currency,
                    "spend_year": request.spend_year,
                    "classification_code": request.classification_code,
                    "classification_type": request.classification_type
                },
                description=f"Procurement: {request.amount} {request.currency} ({request.classification_code})"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": {"co2e_kg": result["co2e"], "scope": "Scope 3"}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
