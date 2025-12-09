"""
Dashboard Service - US-2.3
Provides data aggregation for carbon dashboard
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
import logging

from app.models.models import EmissionTransaction

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard data aggregation (US-2.3)"""
    
    @staticmethod
    async def get_total_emissions(
        db: AsyncSession,
        org_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """Get total CO2e emissions for organization"""
        query = select(func.sum(EmissionTransaction.co2e_tonnes)).where(
            EmissionTransaction.organization_id == org_id
        )
        
        if start_date:
            query = query.where(EmissionTransaction.transaction_date >= start_date)
        if end_date:
            query = query.where(EmissionTransaction.transaction_date <= end_date)
        
        result = await db.execute(query)
        total = result.scalar() or 0.0
        return round(total, 3)
    
    @staticmethod
    async def get_scope_breakdown(
        db: AsyncSession,
        org_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[int, float]:
        """
        Get emissions breakdown by scope
        
        AC: Pie chart accurately represents Scope breakdown
        """
        query = select(
            EmissionTransaction.scope,
            func.sum(EmissionTransaction.co2e_tonnes).label('total')
        ).where(
            EmissionTransaction.organization_id == org_id
        ).group_by(EmissionTransaction.scope)
        
        if start_date:
            query = query.where(EmissionTransaction.transaction_date >= start_date)
        if end_date:
            query = query.where(EmissionTransaction.transaction_date <= end_date)
        
        result = await db.execute(query)
        breakdown = {row.scope: round(row.total, 3) for row in result}
        
        # Ensure all scopes are represented
        for scope in [1, 2, 3]:
            if scope not in breakdown:
                breakdown[scope] = 0.0
        
        return breakdown
    
    @staticmethod
    async def get_monthly_trend(
        db: AsyncSession,
        org_id: str,
        months: int = 12
    ) -> List[Dict]:
        """
        Get 12-month emissions trend
        
        AC: 12-month trend is visible and accurate
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=months*30)
        
        query = select(
            extract('year', EmissionTransaction.transaction_date).label('year'),
            extract('month', EmissionTransaction.transaction_date).label('month'),
            func.sum(EmissionTransaction.co2e_tonnes).label('total')
        ).where(
            and_(
                EmissionTransaction.organization_id == org_id,
                EmissionTransaction.transaction_date >= start_date,
                EmissionTransaction.transaction_date <= end_date
            )
        ).group_by('year', 'month').order_by('year', 'month')
        
        result = await db.execute(query)
        trend = [
            {
                "year": int(row.year),
                "month": int(row.month),
                "date": f"{int(row.year)}-{int(row.month):02d}",
                "emissions_tonnes": round(row.total, 3)
            }
            for row in result
        ]
        
        return trend
    
    @staticmethod
    async def get_category_breakdown(
        db: AsyncSession,
        org_id: str,
        scope: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get top emission categories"""
        query = select(
            EmissionTransaction.category,
            func.sum(EmissionTransaction.co2e_tonnes).label('total'),
            func.count(EmissionTransaction.id).label('count')
        ).where(
            EmissionTransaction.organization_id == org_id
        )
        
        if scope:
            query = query.where(EmissionTransaction.scope == scope)
        
        query = query.group_by(EmissionTransaction.category).order_by(
            func.sum(EmissionTransaction.co2e_tonnes).desc()
        ).limit(limit)
        
        result = await db.execute(query)
        return [
            {
                "category": row.category,
                "emissions_tonnes": round(row.total, 3),
                "transaction_count": row.count
            }
            for row in result
        ]