"""
Data Analysis Router - US-4.2
Provides anomaly detection and forecasting endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.auth.oauth2_scheme import get_current_user
from app.models.models import User
from app.services.anomaly_service import AnomalyService
from app.services.forecasting_service import ForecastingService

router = APIRouter(prefix="/api/v1", tags=["analysis"])

@router.get("/anomalies")
async def detect_anomalies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detect emission anomalies (US-4.2)
    """
    user = current_user
    # Using AnomalyService.detect_anomalies
    # Assuming the service method signature wants (db, org_id)
    anomalies = await AnomalyService.detect_anomalies(db, user.organization_id)
    return anomalies

@router.get("/forecast")
async def get_forecast(
    months_ahead: int = Query(12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get emission forecast (US-4.3)
    """
    user = current_user
    # Using ForecastingService.generate_forecast
    forecast = await ForecastingService.generate_forecast(
        db, user.organization_id, months_ahead
    )
    return forecast
