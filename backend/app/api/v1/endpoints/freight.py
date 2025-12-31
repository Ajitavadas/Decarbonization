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
from app.schemas import FreightCalculationRequest, MultiLegFreightRequest, EstimateResponseSchema
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
    Calculate single-leg freight emissions
    
    Supports modes: road, air, sea, rail
    
    Locations can be:
    - Free text: "Barcelona, Spain"
    - IATA codes: "JFK"
    - UN-LOCODE: "DE-HAM"
    - Coordinates: "52.520008,13.404954"
    """
    try:
        result = await climatiq_service.calculate_freight_emissions(
            origin=request.origin,
            destination=request.destination,
            transport_mode=request.transport_mode,
            cargo_weight=request.cargo_weight,
            weight_unit=request.weight_unit
        )
        
        co2e = result.get("co2e", result.get("total_co2e", 0))
        
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="freight",
                sub_type=request.transport_mode,
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=co2e,
                input_data={
                    "origin": request.origin,
                    "destination": request.destination,
                    "transport_mode": request.transport_mode,
                    "cargo_weight": float(request.cargo_weight),
                    "weight_unit": request.weight_unit
                },
                description=f"Freight ({request.transport_mode}): {request.cargo_weight} {request.weight_unit} from {request.origin} to {request.destination}"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": {"co2e_kg": co2e, "scope": "Scope 3", "raw_response": result}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multileg", response_model=EstimateResponseSchema)
async def calculate_multileg_freight(
    request: MultiLegFreightRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate multi-leg intermodal freight emissions
    
    Example route:
    [
        {"location": "Barcelona, Spain", "transport_mode": "road"},
        {"location": "JFK", "transport_mode": "air"},
        {"location": "Los Angeles, USA"}
    ]
    """
    try:
        route_legs = [{"location": leg.location, "transport_mode": leg.transport_mode} for leg in request.route]
        
        result = await climatiq_service.calculate_intermodal_freight_emissions(
            route_legs=route_legs,
            cargo_weight=request.cargo_weight,
            weight_unit=request.weight_unit
        )
        
        co2e = result.get("co2e", result.get("total_co2e", 0))
        
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="freight",
                sub_type="intermodal",
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=co2e,
                input_data={
                    "route": [leg.model_dump() for leg in request.route],
                    "cargo_weight": float(request.cargo_weight),
                    "weight_unit": request.weight_unit
                },
                description=f"Intermodal freight: {request.cargo_weight} {request.weight_unit}"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": {"co2e_kg": co2e, "scope": "Scope 3", "raw_response": result}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
