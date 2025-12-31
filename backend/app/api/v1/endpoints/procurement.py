"""
Procurement calculation endpoints
Spend-based emissions using EEIO models

NOTE: Procurement is an ADD-ON feature that requires access from Climatiq.
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
    
    Uses EEIO (Environmentally-Extended Input-Output) models from EXIOBASE
    
    Classification types:
    - mcc: Merchant Category Codes
    - unspsc: United Nations Standard Products and Services Code  
    - isic4: International Standard Industrial Classification
    - nace2: Statistical Classification of Economic Activities (EU)
    - naics2017: North American Industry Classification System
    
    Critical: spend_year and region are REQUIRED for accurate inflation adjustment
    """
    try:
        result = await climatiq_service.calculate_procurement_emissions(
            spend_amount=request.amount,
            currency=request.currency,
            classification_code=request.classification_code,
            classification_type=request.classification_type,
            region=request.region,
            spend_year=request.spend_year
        )
        
        # Extract co2e from nested estimate object
        estimate = result.get("estimate", {})
        co2e = estimate.get("co2e", 0)
        
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="procurement",
                sub_type="spend_based",
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=co2e,
                region=request.region,
                year=str(request.spend_year) if request.spend_year else None,
                input_data={
                    "amount": float(request.amount),
                    "currency": request.currency,
                    "spend_year": request.spend_year,
                    "classification_code": request.classification_code,
                    "classification_type": request.classification_type,
                    "region": request.region,
                    "source_trail": result.get("source_trail")
                },
                description=f"Procurement: {request.amount} {request.currency} ({request.classification_type}:{request.classification_code})"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": {"co2e_kg": co2e, "scope": "Scope 3", "raw_response": result}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
