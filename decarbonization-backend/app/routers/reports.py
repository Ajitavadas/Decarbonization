"""
Reports Router - US-2.5
Handles PDF report generation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db
from app.auth.oauth2_scheme import get_current_user
from app.models.models import User, Organization
from app.services.dashboard_service import DashboardService
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/pdf", response_class=StreamingResponse)
async def generate_pdf_report(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Generate PDF emissions report (US-2.5)
    
    AC:
    - PDF generates in under 3 seconds
    - All charts render correctly in PDF
    - File size is under 5 MB (email-friendly)
    - Report includes all required sections
    """
    # Get user and organization
    user_result = await db.execute(select(User).where(User.id == current_user))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get dashboard data
    total_emissions = await DashboardService.get_total_emissions(
        db, org.id, start_date, end_date
    )
    scope_breakdown = await DashboardService.get_scope_breakdown(
        db, org.id, start_date, end_date
    )
    monthly_trend = await DashboardService.get_monthly_trend(
        db, org.id, months=12
    )
    category_breakdown = await DashboardService.get_category_breakdown(
        db, org.id, limit=10
    )
    
    # Determine date range string
    if start_date and end_date:
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    elif start_date:
        date_range = f"From {start_date.strftime('%Y-%m-%d')}"
    elif end_date:
        date_range = f"Until {end_date.strftime('%Y-%m-%d')}"
    else:
        date_range = "All Time"
    
    # Generate PDF
    pdf_buffer = await ReportService.generate_emissions_report(
        org_name=org.name,
        total_emissions=total_emissions,
        scope_breakdown=scope_breakdown,
        monthly_trend=monthly_trend,
        category_breakdown=category_breakdown,
        date_range=date_range
    )
    
    # Return as streaming response
    filename = f"emissions_report_{org.slug}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )