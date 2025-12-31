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
    
    Supports: air, car, rail
    
    Locations can be:
    - IATA codes (3 letters): CDG, BER, JFK
    - Free text: "Berlin, Germany"
    - Coordinates: "52.520008,13.404954"
    
    For air: specify cabin_class (economy, business, first, average)
    For car: specify car_size (small, medium, large) and car_type (petrol, diesel, hybrid, battery)
    """
    try:
        # Map cabin_class to flight_class for service
        result = await climatiq_service.calculate_travel_distance(
            travel_mode=request.travel_mode,
            origin=request.origin,
            destination=request.destination,
            year=request.year,
            flight_class=request.cabin_class if request.travel_mode == "air" else None,
            car_size=getattr(request, 'car_size', None),
            car_type=getattr(request, 'car_type', None)
        )
        
        co2e = result.get("co2e", result.get("total_co2e", 0))
        distance_km = result.get("distance_km", result.get("distance", 0))
        
        # Save to database if project provided
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="travel",
                sub_type=request.travel_mode,
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=co2e,
                input_data={
                    "origin": request.origin,
                    "destination": request.destination,
                    "travel_mode": request.travel_mode,
                    "cabin_class": request.cabin_class,
                    "year": request.year
                },
                description=f"{request.travel_mode.title()} travel: {request.origin} to {request.destination}"
            )
            db.add(activity)
            db.commit()
        
        return {
            "success": True,
            "data": {
                "co2e_kg": co2e,
                "distance_km": distance_km,
                "scope": "Scope 3",
                "raw_response": result
            }
        }
        
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
    
    Supports: hotel, air, rail, road, sea
    
    Critical: spend_year is required for inflation adjustment
    Location helps with regional emission factors
    """
    try:
        result = await climatiq_service.calculate_travel_spend(
            spend_type=request.spend_type,
            amount=request.amount,
            currency=request.currency,
            spend_year=request.spend_year,
            location=request.location
        )
        
        co2e = result.get("co2e", result.get("total_co2e", 0))
        
        # Save to database
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="travel",
                sub_type=f"spend_{request.spend_type}",
                scope="Scope 3",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=co2e,
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
        
        return {"success": True, "data": {"co2e_kg": co2e, "scope": "Scope 3", "raw_response": result}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
