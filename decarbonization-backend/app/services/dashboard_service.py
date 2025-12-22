from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, desc
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
import uuid
import logging

from app.models.models import EmissionEvent, CalculationLedger

logger = logging.getLogger(__name__)

class DashboardService:
    """Service for dashboard data aggregation from calculation_ledger"""
    
    @staticmethod
    async def get_total_emissions(
        db: AsyncSession,
        org_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """Get total CO2e emissions in tonnes"""
        query = select(func.sum(CalculationLedger.result_kg_co2e)).where(
            CalculationLedger.organization_id == org_id
        )
        
        if start_date:
            query = query.where(CalculationLedger.calculation_timestamp >= start_date)
        if end_date:
            query = query.where(CalculationLedger.calculation_timestamp <= end_date)
        
        result = await db.execute(query)
        total_kg = result.scalar() or 0.0
        return round(float(total_kg) / 1000.0, 3)
    
    @staticmethod
    async def get_scope_breakdown(
        db: AsyncSession,
        org_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get emissions breakdown by scope (tonnes)"""
        query = select(
            EmissionEvent.scope,
            func.sum(CalculationLedger.result_kg_co2e).label('total')
        ).join(CalculationLedger, EmissionEvent.id == CalculationLedger.emission_event_id).where(
            CalculationLedger.organization_id == org_id
        ).group_by(EmissionEvent.scope)
        
        if start_date:
            query = query.where(CalculationLedger.calculation_timestamp >= start_date)
        if end_date:
            query = query.where(CalculationLedger.calculation_timestamp <= end_date)
        
        result = await db.execute(query)
        breakdown = {row.scope: round(float(row.total) / 1000.0, 3) for row in result}
        
        # Ensure all scopes represented
        for scope in ["Scope 1", "Scope 2", "Scope 3"]:
            if scope not in breakdown:
                breakdown[scope] = 0.0
        
        return breakdown
    
    @staticmethod
    async def get_monthly_trend(
        db: AsyncSession,
        org_id: uuid.UUID,
        months: int = 12
    ) -> List[Dict]:
        """Get monthly trend with scope breakdown in tonnes"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=months*30)
        
        query = select(
            extract('year', CalculationLedger.calculation_timestamp).label('year'),
            extract('month', CalculationLedger.calculation_timestamp).label('month'),
            EmissionEvent.scope,
            func.sum(CalculationLedger.result_kg_co2e).label('total')
        ).join(EmissionEvent, CalculationLedger.emission_event_id == EmissionEvent.id).where(
            and_(
                CalculationLedger.organization_id == org_id,
                CalculationLedger.calculation_timestamp >= start_date,
                CalculationLedger.calculation_timestamp <= end_date
            )
        ).group_by('year', 'month', EmissionEvent.scope).order_by('year', 'month')
        
        result = await db.execute(query)
        
        # Format: { "2024-01": { "Scope 1": 10, "Scope 2": 20 }, ... }
        trend_map = {}
        for row in result:
            date_key = f"{int(row.year)}-{int(row.month):02d}"
            if date_key not in trend_map:
                trend_map[date_key] = {"date": date_key, "Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0}
            
            scope_key = row.scope if row.scope in ["Scope 1", "Scope 2", "Scope 3"] else "Scope 3"
            trend_map[date_key][scope_key] += round(float(row.total) / 1000.0, 3)
            
        return sorted(trend_map.values(), key=lambda x: x["date"])

    @staticmethod
    async def get_category_breakdown(
        db: AsyncSession,
        org_id: uuid.UUID,
        scope: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get emissions breakdown by category"""
        query = (
            select(
                EmissionEvent.scope_3_category.label("category"),
                func.sum(CalculationLedger.result_kg_co2e).label("total"),
                func.count(CalculationLedger.id).label("count")
            )
            .join(CalculationLedger, EmissionEvent.id == CalculationLedger.emission_event_id)
            .where(CalculationLedger.organization_id == org_id)
        )
        
        if scope:
            query = query.where(EmissionEvent.scope == f"Scope {scope}")
            
        result = await db.execute(
            query.group_by(EmissionEvent.scope_3_category)
            .order_by(desc("total"))
            .limit(limit)
        )
        return [
            {
                "category": row.category or "Other",
                "emissions_tonnes": round(float(row.total) / 1000.0, 3),
                "transaction_count": row.count
            }
            for row in result
        ]

    @staticmethod
    async def get_recent_activity(
        db: AsyncSession,
        org_id: uuid.UUID,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent calculation activity"""
        query = (
            select(
                CalculationLedger.id,
                CalculationLedger.result_kg_co2e,
                CalculationLedger.calculation_timestamp,
                EmissionEvent.description,
                EmissionEvent.scope,
                EmissionEvent.scope_3_category
            )
            .join(EmissionEvent, CalculationLedger.emission_event_id == EmissionEvent.id)
            .where(CalculationLedger.organization_id == org_id)
            .order_by(desc(CalculationLedger.calculation_timestamp))
            .limit(limit)
        )
        
        result = await db.execute(query)
        activities = []
        for r in result.mappings():
            activities.append({
                "id": str(r["id"]),
                "amount": float(r["result_kg_co2e"] / 1000),
                "date": r["calculation_timestamp"].isoformat(),
                "description": r["description"],
                "scope": r["scope"],
                "category": r["scope_3_category"]
            })
        return activities