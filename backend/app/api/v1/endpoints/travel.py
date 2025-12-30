"""
Travel calculation endpoints
Distance-based and spend-based travel emissions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.activity import EmissionActivity
from app.schemas import TravelDistanceRequest, TravelSpendRequest, EstimateResponseSchema
from app.services.calculation_engine import calculation_engine
from app.integration.climatiq.service import ClimatiqService
from app.services.scope_classifier import scope_classifier
from app.core.security import get_current_user

router = APIRouter()
climatiq_service = ClimatiqService()


@router.post("/distance", response_model=EstimateResponseSchema)
async def calculate_travel_distance(
    request: TravelDistanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate emissions for distance-based travel
    
    Supports: air, car, rail, bus
    """
    try:
        # Calculate using service
        result = await calculation_engine.calculate_travel(
            travel_mode=request.travel_mode,
            origin=request.origin,
            destination=request.destination,
            cabin_class=request.cabin_class,
            year=request.year
        )
        
        # Save to database if project provided
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="travel",
                sub_type=request.travel_mode,
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=result["co2e_kg"],
                input_data={
                    "origin": request.origin,
                    "destination": request.destination,
                    "travel_mode": request.travel_mode,
                    "cabin_class": request.cabin_class
                },
                description=f"{request.travel_mode.title()} travel: {request.origin} to {request.destination}"
            )
            db.add(activity)
            db.commit()
            
            result["activity_id"] = str(activity.id)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spend", response_model=EstimateResponseSchema)
async def calculate_travel_spend(
    request: TravelSpendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate emissions for spend-based travel
    
    Supports: hotel, car_rental, rail, air
    Critical: spend_year is required for inflation adjustment
    """
    try:
        result = await climatiq_service.calculate_hotel_emissions(
            spend_amount=request.amount,
            currency=request.currency,
            spend_year=request.spend_year,
            location=request.location
        ) if request.spend_type == "hotel" else await climatiq_service.client.travel_spend({
            "spend_type": request.spend_type,
            "money": float(request.amount),
            "money_unit": request.currency,
            "spend_year": request.spend_year
        })
        
        # Save to database
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="travel",
                sub_type=f"spend_{request.spend_type}",
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=result["co2e"],
                input_data={
                    "spend_type": request.spend_type,
                    "amount": float(request.amount),
                    "currency": request.currency,
                    "spend_year": request.spend_year,
                    "location": request.location
                },
                description=f"Spend-based {request.spend_type}: {request.amount} {request.currency}"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": {"co2e_kg": result["co2e"], "scope": "Scope 3"}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
