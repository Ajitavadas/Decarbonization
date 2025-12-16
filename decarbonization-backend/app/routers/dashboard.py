"""
Dashboard Router - US-2.3
Provides carbon dashboard data
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.database import get_db
from app.auth.oauth2_scheme import get_current_user
from app.models.models import User
from app.services.dashboard_service import DashboardService
from app.schemas.schemas import DashboardResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    scope_filter: Optional[int] = Query(None, ge=1, le=3)
):
    """
    Get dashboard data (US-2.3)
    
    AC:
    - Dashboard shows total emissions prominently
    - Pie chart accurately represents Scope breakdown
    - 12-month trend is visible and accurate
    - Dashboard loads in under 2 seconds
    - Mobile view is readable and functional
    """
    org_id = current_user.organization_id
    
    # Get total emissions
    total_emissions = await DashboardService.get_total_emissions(
        db, org_id, start_date, end_date
    )
    
    # Get scope breakdown
    scope_breakdown = await DashboardService.get_scope_breakdown(
        db, org_id, start_date, end_date
    )
    
    # Get monthly trend
    monthly_trend = await DashboardService.get_monthly_trend(
        db, org_id, months=12
    )
    
    # Get category breakdown
    category_breakdown = await DashboardService.get_category_breakdown(
        db, org_id, scope=scope_filter, limit=10
    )
    
    return {
        "total_emissions_tonnes": total_emissions,
        "scope_breakdown": scope_breakdown,
        "monthly_trend": monthly_trend,
        "category_breakdown": category_breakdown,
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    }