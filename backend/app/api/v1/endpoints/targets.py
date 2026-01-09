"""
Reduction Targets API Endpoints
CRUD operations for reduction targets and AI strategy generation
"""

import logging
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.reduction_service import create_reduction_service
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== Request/Response Schemas ==========

class MilestoneSchema(BaseModel):
    """Interim milestone schema"""
    year: str
    value: float  # Percentage reduction target
    achieved: bool = False
    achieved_at: Optional[str] = None


class TargetCreateRequest(BaseModel):
    """Request to create a reduction target"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: str = Field(..., pattern="^(absolute|percentage)$")
    scope: Optional[str] = Field("all", pattern="^(Scope 1|Scope 2|Scope 3|all)$")
    baseline_year: str = Field(..., pattern="^\\d{4}$")
    baseline_value: float = Field(..., gt=0)
    target_year: str = Field(..., pattern="^\\d{4}$")
    target_value: float = Field(..., gt=0)
    milestones: Optional[List[MilestoneSchema]] = []
    project_id: Optional[UUID] = None


class TargetUpdateRequest(BaseModel):
    """Request to update a reduction target"""
    name: Optional[str] = None
    description: Optional[str] = None
    target_type: Optional[str] = None
    scope: Optional[str] = None
    baseline_year: Optional[str] = None
    baseline_value: Optional[float] = None
    target_year: Optional[str] = None
    target_value: Optional[float] = None
    milestones: Optional[List[MilestoneSchema]] = None
    is_active: Optional[bool] = None


class TargetResponse(BaseModel):
    """Reduction target response"""
    id: str
    name: str
    description: Optional[str]
    target_type: str
    scope: Optional[str]
    baseline_year: str
    baseline_value: float
    target_year: str
    target_value: float
    milestones: list
    current_year: Optional[str]
    current_value: Optional[float]
    current_reduction_pct: Optional[float]
    progress_percentage: Optional[float]
    status: str
    is_active: bool
    created_at: str
    last_calculated_at: Optional[str]

    class Config:
        from_attributes = True


class StrategyResponse(BaseModel):
    """Reduction strategy response"""
    id: str
    title: str
    description: str
    category: str
    scope: Optional[str]
    difficulty: Optional[str]
    priority: int
    implementation_timeframe: Optional[str]
    estimated_reduction_pct: Optional[float]
    estimated_cost: Optional[float]
    estimated_savings: Optional[float]
    payback_period_months: Optional[int]
    source: str
    status: str
    is_ai_generated: bool
    created_at: str


class StrategyGenerateRequest(BaseModel):
    """Request to generate strategies"""
    force_refresh: bool = False
    max_strategies: int = Field(5, ge=1, le=10)


class StrategyStatusUpdateRequest(BaseModel):
    """Request to update strategy status"""
    status: str = Field(..., pattern="^(suggested|considering|in_progress|completed|rejected)$")


# ========== API Endpoints ==========

@router.post("/", response_model=TargetResponse)
async def create_target(
    request: TargetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new reduction target
    
    Supports:
    - Absolute targets (reduce to X kg CO2e)
    - Percentage targets (reduce by X%)
    - Interim milestones
    - Scope-specific or organization-wide
    """
    service = create_reduction_service(db, current_user.organization_id)
    
    target = service.create_target(
        name=request.name,
        description=request.description,
        target_type=request.target_type,
        scope=request.scope,
        baseline_year=request.baseline_year,
        baseline_value=request.baseline_value,
        target_year=request.target_year,
        target_value=request.target_value,
        milestones=[m.model_dump() for m in request.milestones] if request.milestones else [],
        project_id=request.project_id
    )
    
    return _target_to_response(target)


@router.get("/", response_model=List[TargetResponse])
async def get_targets(
    active_only: bool = Query(True, description="Filter to active targets only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reduction targets for the organization"""
    service = create_reduction_service(db, current_user.organization_id)
    targets = service.get_targets(active_only=active_only)
    return [_target_to_response(t) for t in targets]


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific reduction target"""
    service = create_reduction_service(db, current_user.organization_id)
    target = service.get_target(target_id)
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return _target_to_response(target)


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: UUID,
    request: TargetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a reduction target"""
    service = create_reduction_service(db, current_user.organization_id)
    
    update_data = request.model_dump(exclude_unset=True)
    if 'milestones' in update_data and update_data['milestones']:
        update_data['milestones'] = [m.model_dump() if hasattr(m, 'model_dump') else m for m in update_data['milestones']]
    
    target = service.update_target(target_id, **update_data)
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return _target_to_response(target)


@router.delete("/{target_id}")
async def delete_target(
    target_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a reduction target"""
    service = create_reduction_service(db, current_user.organization_id)
    success = service.delete_target(target_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return {"message": "Target deleted successfully"}


@router.post("/{target_id}/calculate-progress", response_model=TargetResponse)
async def calculate_progress(
    target_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recalculate progress for a specific target"""
    service = create_reduction_service(db, current_user.organization_id)
    target = service.update_target_progress(target_id)
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return _target_to_response(target)


@router.post("/calculate-all-progress")
async def calculate_all_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recalculate progress for all active targets"""
    service = create_reduction_service(db, current_user.organization_id)
    updated_count = service.update_all_targets_progress()
    return {"message": f"Updated progress for {updated_count} targets"}


# ========== Strategy Endpoints ==========

@router.post("/{target_id}/strategies/generate", response_model=List[StrategyResponse])
async def generate_strategies(
    target_id: UUID,
    request: StrategyGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered reduction strategies for a target
    
    Rate-limit conscious:
    - Uses llama-3.3-70b-versatile (high-quality model)
    - Results are cached for 7 days
    - Pass force_refresh=true to regenerate (uses API quota)
    """
    service = create_reduction_service(db, current_user.organization_id)
    
    # Check target exists
    target = service.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    strategies = await service.generate_strategies(
        target_id=target_id,
        force_refresh=request.force_refresh,
        max_strategies=request.max_strategies
    )
    
    return [_strategy_to_response(s) for s in strategies]


@router.get("/{target_id}/strategies", response_model=List[StrategyResponse])
async def get_strategies(
    target_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get existing strategies for a target (from cache)"""
    service = create_reduction_service(db, current_user.organization_id)
    strategies = service.get_strategies(target_id=target_id)
    return [_strategy_to_response(s) for s in strategies]


@router.patch("/strategies/{strategy_id}/status", response_model=StrategyResponse)
async def update_strategy_status(
    strategy_id: UUID,
    request: StrategyStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update strategy status (considering, in_progress, completed, rejected)"""
    service = create_reduction_service(db, current_user.organization_id)
    strategy = service.update_strategy_status(strategy_id, request.status)
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return _strategy_to_response(strategy)


# ========== Helper Functions ==========

def _target_to_response(target) -> dict:
    """Convert target model to response dict"""
    return {
        "id": str(target.id),
        "name": target.name,
        "description": target.description,
        "target_type": target.target_type,
        "scope": target.scope,
        "baseline_year": target.baseline_year,
        "baseline_value": float(target.baseline_value) if target.baseline_value else 0,
        "target_year": target.target_year,
        "target_value": float(target.target_value) if target.target_value else 0,
        "milestones": target.milestones or [],
        "current_year": target.current_year,
        "current_value": float(target.current_value) if target.current_value else None,
        "current_reduction_pct": float(target.current_reduction_pct) if target.current_reduction_pct else None,
        "progress_percentage": float(target.progress_percentage) if target.progress_percentage else None,
        "status": target.status,
        "is_active": target.is_active,
        "created_at": target.created_at.isoformat() if target.created_at else None,
        "last_calculated_at": target.last_calculated_at.isoformat() if target.last_calculated_at else None,
    }


def _strategy_to_response(strategy) -> dict:
    """Convert strategy model to response dict"""
    return {
        "id": str(strategy.id),
        "title": strategy.title,
        "description": strategy.description,
        "category": strategy.category,
        "scope": strategy.scope,
        "difficulty": strategy.difficulty,
        "priority": strategy.priority,
        "implementation_timeframe": strategy.implementation_timeframe,
        "estimated_reduction_pct": float(strategy.estimated_reduction_pct) if strategy.estimated_reduction_pct else None,
        "estimated_cost": float(strategy.estimated_cost) if strategy.estimated_cost else None,
        "estimated_savings": float(strategy.estimated_savings) if strategy.estimated_savings else None,
        "payback_period_months": strategy.payback_period_months,
        "source": strategy.source,
        "status": strategy.status,
        "is_ai_generated": strategy.source == "ai",
        "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
    }
