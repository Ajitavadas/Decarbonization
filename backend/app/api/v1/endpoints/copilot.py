"""
Copilot API Endpoints - Semantic query functions for offline-first Carbon Copilot

All endpoints here answer queries WITHOUT any LLM call (offline-first design).
LLM calls are only made when explicitly requested.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.activity import EmissionActivity
from app.models.project import Project
from app.models.reduction_target import ReductionTarget
from app.models.flagged_event import FlaggedEvent
from app.db.session import get_db
from app.core.archetype_config import get_archetype

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== Response Schemas ==========

class EmissionsSummary(BaseModel):
    """Summary of emissions by scope or category"""
    total_kg: float
    by_scope: Dict[str, float]
    by_category: Dict[str, float]
    by_month: List[Dict[str, Any]]
    top_sources: List[Dict[str, Any]]
    period: str


class DataCompleteness(BaseModel):
    """Data completeness against archetype requirements"""
    overall_percentage: float
    by_scope: Dict[str, float]
    missing_categories: List[str]
    expected_categories: List[str]
    months_with_data: int
    total_activities: int
    archetype: Optional[str]


class TrendAnalysis(BaseModel):
    """Trend analysis response"""
    direction: str  # "increasing", "decreasing", "stable"
    percentage_change: float
    period_comparison: Dict[str, float]
    insights: List[str]


class QuickStat(BaseModel):
    """Quick stat for copilot widget"""
    label: str
    value: str
    change: Optional[str]
    trend: Optional[str]


# ========== Semantic Query Endpoints ==========

@router.get("/summary", response_model=EmissionsSummary)
async def get_emissions_summary(
    scope: Optional[str] = Query(None, description="Filter by scope"),
    year: Optional[int] = Query(None, description="Filter by year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get emissions summary - Answers: "What are my total emissions?"
    
    Pure SQL query, no LLM call.
    """
    query = db.query(EmissionActivity).join(
        Project
    ).filter(
        Project.organization_id == current_user.organization_id
    )
    
    if scope:
        query = query.filter(EmissionActivity.scope == scope)
    if year:
        query = query.filter(extract('year', EmissionActivity.activity_date) == year)
    
    activities = query.all()
    
    if not activities:
        return EmissionsSummary(
            total_kg=0,
            by_scope={},
            by_category={},
            by_month=[],
            top_sources=[],
            period="No data"
        )
    
    # Calculate totals
    total = sum(float(a.co2e_kg or 0) for a in activities)
    
    # By scope
    by_scope = {}
    for a in activities:
        scope_key = a.scope or "Unknown"
        by_scope[scope_key] = by_scope.get(scope_key, 0) + float(a.co2e_kg or 0)
    
    # By category (actually activity_type in the model)
    by_category = {}
    for a in activities:
        cat_key = a.activity_type or "Unknown"
        by_category[cat_key] = by_category.get(cat_key, 0) + float(a.co2e_kg or 0)
    
    # By month
    monthly = {}
    for a in activities:
        if a.activity_date:
            key = a.activity_date.strftime("%Y-%m")
            monthly[key] = monthly.get(key, 0) + float(a.co2e_kg or 0)
    by_month = [{"month": k, "emissions": v} for k, v in sorted(monthly.items())]
    
    # Top sources
    source_totals = {}
    for a in activities:
        source = a.description or a.activity_type or "Unknown"
        source_totals[source] = source_totals.get(source, 0) + float(a.co2e_kg or 0)
    top_sources = [
        {"source": k, "emissions": v, "percentage": (v/total)*100 if total > 0 else 0}
        for k, v in sorted(source_totals.items(), key=lambda x: -x[1])[:5]
    ]
    
    return EmissionsSummary(
        total_kg=total,
        by_scope=by_scope,
        by_category=by_category,
        by_month=by_month,
        top_sources=top_sources,
        period=f"{min(a.activity_date for a in activities if a.activity_date).year if any(a.activity_date for a in activities) else 'N/A'}"
    )


@router.get("/completeness", response_model=DataCompleteness)
async def get_data_completeness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get data completeness against archetype requirements
    
    Answers: "How complete is my data?"
    Pure SQL query, no LLM call.
    """
    from app.models.organization import Organization
    
    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    archetype = org.emission_archetype if org else None
    archetype_info = get_archetype(archetype) if archetype else None
    
    # Get all activities
    activities = db.query(EmissionActivity).join(
        Project
    ).filter(
        Project.organization_id == current_user.organization_id
    ).all()
    
    # Categories present
    present_categories = set(a.activity_type for a in activities if a.activity_type)
    
    # Expected categories from archetype
    if archetype_info:
        expected_categories = archetype_info.expected_activity_types
    else:
        # Default expected categories
        expected_categories = ["electricity", "natural_gas", "fuel", "travel", "waste"]
    
    missing = [c for c in expected_categories if c not in present_categories]
    
    # Scope coverage
    by_scope = {"Scope 1": 0, "Scope 2": 0, "Scope 3": 0}
    scope_expected = {"Scope 1": 30, "Scope 2": 30, "Scope 3": 30}  # Min activities expected
    
    for a in activities:
        if a.scope in by_scope:
            by_scope[a.scope] += 1
    
    for scope in by_scope:
        by_scope[scope] = min((by_scope[scope] / scope_expected[scope]) * 100, 100) if scope_expected[scope] > 0 else 0
    
    # Months with data
    months_set = set()
    for a in activities:
        if a.activity_date:
            months_set.add(a.activity_date.strftime("%Y-%m"))
    
    # Overall completeness
    category_score = ((len(expected_categories) - len(missing)) / len(expected_categories) * 100) if expected_categories else 100
    scope_score = sum(by_scope.values()) / 3
    month_score = min((len(months_set) / 12) * 100, 100)
    
    overall = (category_score * 0.4 + scope_score * 0.4 + month_score * 0.2)
    
    return DataCompleteness(
        overall_percentage=round(overall, 1),
        by_scope={k: round(v, 1) for k, v in by_scope.items()},
        missing_categories=missing,
        expected_categories=expected_categories,
        months_with_data=len(months_set),
        total_activities=len(activities),
        archetype=archetype
    )


@router.get("/trends", response_model=TrendAnalysis)
async def get_trend_analysis(
    period: str = Query("quarterly", description="monthly, quarterly, yearly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get emission trends - Answers: "Are my emissions increasing or decreasing?"
    
    Pure SQL query, no LLM call.
    """
    activities = db.query(EmissionActivity).join(
        Project
    ).filter(
        Project.organization_id == current_user.organization_id
    ).order_by(EmissionActivity.activity_date).all()
    
    if len(activities) < 2:
        return TrendAnalysis(
            direction="insufficient_data",
            percentage_change=0,
            period_comparison={},
            insights=["Not enough data for trend analysis"]
        )
    
    # Group by period
    periods = {}
    for a in activities:
        if not a.activity_date:
            continue
        
        if period == "monthly":
            key = a.activity_date.strftime("%Y-%m")
        elif period == "quarterly":
            quarter = (a.activity_date.month - 1) // 3 + 1
            key = f"{a.activity_date.year}-Q{quarter}"
        else:  # yearly
            key = str(a.activity_date.year)
        
        periods[key] = periods.get(key, 0) + float(a.co2e_kg or 0)
    
    sorted_periods = sorted(periods.items())
    
    if len(sorted_periods) < 2:
        return TrendAnalysis(
            direction="insufficient_data",
            percentage_change=0,
            period_comparison=dict(sorted_periods),
            insights=["Only one period available"]
        )
    
    # Compare last two periods
    current = sorted_periods[-1][1]
    previous = sorted_periods[-2][1]
    
    if previous > 0:
        change = ((current - previous) / previous) * 100
    else:
        change = 0
    
    if change > 5:
        direction = "increasing"
        insights = [f"Emissions increased by {abs(change):.1f}% compared to previous {period}"]
    elif change < -5:
        direction = "decreasing"
        insights = [f"Emissions decreased by {abs(change):.1f}% compared to previous {period}"]
    else:
        direction = "stable"
        insights = ["Emissions have remained relatively stable"]
    
    return TrendAnalysis(
        direction=direction,
        percentage_change=round(change, 1),
        period_comparison=dict(sorted_periods[-6:]),  # Last 6 periods
        insights=insights
    )


@router.get("/quick-stats", response_model=List[QuickStat])
async def get_quick_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quick stats for dashboard widgets
    
    Pure SQL queries, no LLM calls.
    """
    stats = []
    
    # Total emissions
    total = db.query(func.sum(EmissionActivity.co2e_kg)).join(
        Project
    ).filter(
        Project.organization_id == current_user.organization_id
    ).scalar() or 0
    
    stats.append(QuickStat(
        label="Total Emissions",
        value=f"{float(total):,.0f} kg CO₂e",
        change=None,
        trend=None
    ))
    
    # Active targets
    target_count = db.query(func.count(ReductionTarget.id)).filter(
        ReductionTarget.organization_id == current_user.organization_id,
        ReductionTarget.is_active == True
    ).scalar() or 0
    
    on_track = db.query(func.count(ReductionTarget.id)).filter(
        ReductionTarget.organization_id == current_user.organization_id,
        ReductionTarget.status.in_(["on_track", "achieved"])
    ).scalar() or 0
    
    stats.append(QuickStat(
        label="Reduction Targets",
        value=f"{on_track}/{target_count} on track",
        change=None,
        trend="positive" if on_track == target_count and target_count > 0 else None
    ))
    
    # Open findings
    open_findings = db.query(func.count(FlaggedEvent.id)).filter(
        FlaggedEvent.organization_id == current_user.organization_id,
        FlaggedEvent.status == "open"
    ).scalar() or 0
    
    critical = db.query(func.count(FlaggedEvent.id)).filter(
        FlaggedEvent.organization_id == current_user.organization_id,
        FlaggedEvent.status == "open",
        FlaggedEvent.severity == "critical"
    ).scalar() or 0
    
    stats.append(QuickStat(
        label="Open Findings",
        value=f"{open_findings}" + (f" ({critical} critical)" if critical > 0 else ""),
        change=None,
        trend="negative" if critical > 0 else None
    ))
    
    return stats


# ========== Chat Endpoint (NEW) ==========

class ChatRequest(BaseModel):
    """Chat request from frontend"""
    message: str = Field(..., min_length=1, max_length=1000)
    history: Optional[List[Dict[str, Any]]] = Field(default=[])
    include_llm: bool = Field(default=True, description="Include LLM explanation if available")


class ChatResponse(BaseModel):
    """Chat response with data and optional LLM explanation"""
    text: str
    intent: str
    data: Dict[str, Any]
    source: str  # "deterministic", "llm", "cache", "budget_exceeded"
    model: Optional[str]
    suggestions: List[str]


@router.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with Carbon Copilot
    
    Provides context-aware responses based on organization's emission data.
    Uses SQL-first approach with optional LLM explanation.
    
    Intent Classification (deterministic):
    - total_emissions: "What are my total emissions?"
    - scope_breakdown: "Show by scope"
    - trend: "Are emissions increasing?"
    - target_progress: "How are my targets doing?"
    - findings: "Any issues?"
    - explain: "Why did X happen?"
    - suggest: "How can I reduce?"
    """
    from app.services.copilot_service import create_copilot_service
    
    try:
        copilot = create_copilot_service(
            db=db,
            organization_id=current_user.organization_id,
            redis_client=None  # TODO: Add Redis when available
        )
        
        result = await copilot.chat(
            message=request.message,
            history=request.history,
            include_llm=request.include_llm
        )
        
        return ChatResponse(
            text=result["text"],
            intent=result["intent"],
            data=result["data"],
            source=result["source"],
            model=result.get("model"),
            suggestions=result.get("suggestions", [])
        )
        
    except Exception as e:
        logger.error(f"Copilot chat error: {e}")
        # Return offline fallback on error
        return ChatResponse(
            text="I'm having trouble accessing your data. Please try again.",
            intent="error",
            data={},
            source="error",
            model=None,
            suggestions=["Try again", "Check your data uploads"]
        )

