"""
Custom mappings endpoints
Manage organizational ERP->Climatiq mappings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.custom_mapping import CustomMapping
from app.models.activity import EmissionActivity
from app.schemas import (
    CustomMappingCreate,
    CustomMappingResponse,
    EstimateWithMappingRequest,
    EstimateResponseSchema
)
from app.crud.crud_mapping import crud_mapping
from app.integration.climatiq.service import ClimatiqService
from app.core.security import get_current_user

router = APIRouter()
climatiq_service = ClimatiqService()


@router.post("/", response_model=CustomMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    mapping_in: CustomMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new custom mapping
    
    Uses Autopilot to suggest best emission factor if climatiq_activity_id not provided
    """
    try:
        # If no activity_id provided, use Autopilot
        if not mapping_in.climatiq_activity_id:
            suggestions = await climatiq_service.suggest_emission_factors(mapping_in.query)
            
            if not suggestions.get("suggestions"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No emission factors found for query"
                )
            
            # Use top suggestion
            top_suggestion = suggestions["suggestions"][0]
            activity_id = top_suggestion["activity_id"]
            confidence = top_suggestion["confidence"]
        else:
            activity_id = mapping_in.climatiq_activity_id
            confidence = 1.0
        
        # Create mapping
        mapping = CustomMapping(
            organization_id=current_user.organization_id,
            internal_label=mapping_in.internal_label,
            internal_code=mapping_in.internal_code,
            category=mapping_in.category,
            climatiq_activity_id=activity_id,
            confidence_score=confidence,
            mapping_method="autopilot" if not mapping_in.climatiq_activity_id else "manual",
            default_parameters=mapping_in.default_parameters,
            created_by=current_user.id
        )
        
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        
        return mapping
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CustomMappingResponse])
async def list_mappings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all mappings for user's organization"""
    mappings = crud_mapping.get_by_organization(
        db,
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit
    )
    return mappings


@router.get("/{mapping_id}", response_model=CustomMappingResponse)
async def get_mapping(
    mapping_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific mapping"""
    mapping = crud_mapping.get(db, id=mapping_id)
    if not mapping or mapping.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping


@router.post("/estimate", response_model=EstimateResponseSchema)
async def estimate_with_mapping(
    request: EstimateWithMappingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate emissions using pre-defined mapping
    
    Simplifies repeated calculations for common internal codes
    """
    try:
        # Get mapping
        mapping = crud_mapping.get(db, id=request.mapping_id)
        if not mapping or mapping.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        # Merge default parameters with request parameters
        parameters = {**(mapping.default_parameters or {}), **request.parameters}
        
        # Calculate emission
        from app.services.calculation_engine import calculation_engine
        result = await calculation_engine.calculate_emission(
            activity_type="mapped",
            activity_id=mapping.climatiq_activity_id,
            parameters=parameters,
            region=mapping.climatiq_region,
            year=int(mapping.climatiq_year) if mapping.climatiq_year else None
        )
        
        # Increment usage counter
        crud_mapping.increment_usage(db, mapping_id=request.mapping_id)
        
        # Save activity
        activity = EmissionActivity(
            project_id=request.project_id,
            activity_type="mapped",
            sub_type=mapping.category,
            scope=result["scope"],
            activity_date=request.activity_date or datetime.utcnow(),
            co2e_kg=result["co2e_kg"],
            emission_factor_id=mapping.climatiq_activity_id,
            input_data={"mapping_id": str(mapping.id), "parameters": parameters},
            description=f"Mapped: {mapping.internal_label}"
        )
        db.add(activity)
        db.commit()
        
        return {"success": True, "data": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
