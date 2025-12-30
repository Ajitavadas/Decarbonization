"""
Freight calculation endpoints
Intermodal freight routing
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.activity import EmissionActivity
from app.schemas import FreightCalculationRequest, EstimateResponseSchema
from app.integration.climatiq.service import ClimatiqService
from app.core.security import get_current_user

router = APIRouter()
climatiq_service = ClimatiqService()


@router.post("/intermodal", response_model=EstimateResponseSchema)
async def calculate_freight(
    request: FreightCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate intermodal freight emissions
    
    Supports multi-leg routes: road, air, sea, rail
    """
    try:
        # Convert request to Climatiq format
        route_legs = []
        for leg in request.route:
            route_legs.append({
                "origin": {"query": leg.origin},
                "destination": {"query": leg.destination},
                "transport_mode": leg.transport_mode,
                "leg_details": leg.leg_details or {}
            })
        
        result = await climatiq_service.calculate_freight_emissions(
            route=route_legs,
            cargo_weight_kg=request.cargo_weight_kg
        )
        
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="freight",
                sub_type="intermodal",
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=result["total_co2e"],
                input_data={
                    "route": [leg.dict() for leg in request.route],
                    "cargo_weight_kg": float(request.cargo_weight_kg)
                },
                description=f"Freight: {request.cargo_weight_kg} kg cargo"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
