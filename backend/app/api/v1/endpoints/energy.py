"""
Energy calculation endpoints
Electricity, fuel combustion, and heat/steam
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.activity import EmissionActivity
from app.schemas import ElectricityCalculationRequest, FuelCalculationRequest, EstimateResponseSchema
from app.integration.climatiq.service import ClimatiqService
from app.core.security import get_current_user

router = APIRouter()
climatiq_service = ClimatiqService()


@router.post("/electricity", response_model=EstimateResponseSchema)
async def calculate_electricity(
    request: ElectricityCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate Scope 2 electricity emissions
    
    Critical: Region is REQUIRED (grid carbon intensity varies 10x globally)
    
    Example regions: US, GB, DE, ZA, SE, FR, etc. (2-letter ISO codes)
    """
    try:
        result = await climatiq_service.calculate_electricity_emissions(
            energy_kwh=request.energy_kwh,
            region=request.region,
            year=request.year or 2024,
            renewable_credits=request.renewable_credits
        )
        
        # Extract CO2e from nested response structure
        # Climatiq returns: location.consumption.co2e for location-based, market.consumption.co2e for market-based
        co2e = 0
        if "location" in result and "consumption" in result["location"]:
            co2e = result["location"]["consumption"].get("co2e", 0)
        elif "co2e" in result:
            co2e = result.get("co2e", 0)
        elif "total_co2e" in result:
            co2e = result.get("total_co2e", 0)
        
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="energy",
                sub_type="electricity",
                scope="Scope 2",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=co2e,
                region=request.region,
                year=str(request.year),
                input_data={
                    "energy_kwh": float(request.energy_kwh),
                    "region": request.region,
                    "renewable_credits": float(request.renewable_credits) if request.renewable_credits else None
                },
                description=f"Electricity: {request.energy_kwh} kWh in {request.region}"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": {"co2e_kg": co2e, "scope": "Scope 2", "raw_response": result}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fuel", response_model=EstimateResponseSchema)
async def calculate_fuel(
    request: FuelCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate Scope 1 fuel combustion emissions
    
    Direct emissions from owned sources
    
    Supported fuel_types: natural_gas, coal, cng, diesel, biodiesel_bio_100,
    gasoline, ethanol, heavy_fuel_oil, fuel_oil, kerosene, biogas_bio_100,
    hydrogen, wood_chips_bio_100, recycled_gas, propane
    """
    try:
        result = await climatiq_service.calculate_fuel_emissions(
            fuel_type=request.fuel_type,
            amount=request.amount,
            unit=request.unit,
            unit_type=request.unit_type,
            region=request.region,
            year=request.year
        )
        
        # Extract CO2e from nested response structure
        # Climatiq returns: combustion.co2e for fuel calculations
        co2e = 0
        if "combustion" in result:
            co2e = result["combustion"].get("co2e", 0)
        elif "co2e" in result:
            co2e = result.get("co2e", 0)
        elif "total_co2e" in result:
            co2e = result.get("total_co2e", 0)
        
        if request.project_id:
            activity = EmissionActivity(
                project_id=request.project_id,
                activity_type="energy",
                sub_type="fuel",
                scope="Scope 1",
                activity_date=request.activity_date or datetime.utcnow(),
                co2e_kg=co2e,
                region=request.region,
                year=str(request.year) if request.year else None,
                input_data={
                    "fuel_type": request.fuel_type,
                    "amount": float(request.amount),
                    "unit": request.unit,
                    "unit_type": request.unit_type
                },
                description=f"Fuel combustion: {request.amount} {request.unit} of {request.fuel_type}"
            )
            db.add(activity)
            db.commit()
        
        return {"success": True, "data": {"co2e_kg": co2e, "scope": "Scope 1", "raw_response": result}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
