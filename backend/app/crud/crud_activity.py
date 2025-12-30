"""
CRUD operations for Emission Activities
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date

from app.crud.base import CRUDBase
from app.models.activity import EmissionActivity


class CRUDActivity(CRUDBase[EmissionActivity]):
    """CRUD operations for emission activities"""
    
    def get_by_project(
        self,
        db: Session,
        *,
        project_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[EmissionActivity]:
        """Get activities for a specific project"""
        return (
            db.query(self.model)
            .filter(EmissionActivity.project_id == project_id)
            .order_by(EmissionActivity.activity_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_scope(
        self,
        db: Session,
        *,
        project_id: str,
        scope: str
    ) -> List[EmissionActivity]:
        """Get activities filtered by scope"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    EmissionActivity.project_id == project_id,
                    EmissionActivity.scope == scope
                )
            )
            .all()
        )
    
    def get_by_date_range(
        self,
        db: Session,
        *,
        project_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[EmissionActivity]:
        """Get activities within date range"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    EmissionActivity.project_id == project_id,
                    EmissionActivity.activity_date >= start_date,
                    EmissionActivity.activity_date <= end_date
                )
            )
            .all()
        )
    
    def get_total_emissions(
        self,
        db: Session,
        *,
        project_id: str,
        scope: Optional[str] = None
    ) -> float:
        """Calculate total CO2e for project (optionally filtered by scope)"""
        query = db.query(func.sum(EmissionActivity.co2e_kg)).filter(
            EmissionActivity.project_id == project_id
        )
        
        if scope:
            query = query.filter(EmissionActivity.scope == scope)
        
        result = query.scalar()
        return float(result) if result else 0.0
    
    def get_emissions_by_scope(
        self,
        db: Session,
        *,
        project_id: str
    ) -> Dict[str, float]:
        """Get emissions breakdown by scope"""
        results = (
            db.query(
                EmissionActivity.scope,
                func.sum(EmissionActivity.co2e_kg).label("total")
            )
            .filter(EmissionActivity.project_id == project_id)
            .group_by(EmissionActivity.scope)
            .all()
        )
        
        return {scope: float(total) for scope, total in results}
    
    def get_emissions_by_activity_type(
        self,
        db: Session,
        *,
        project_id: str
    ) -> Dict[str, float]:
        """Get emissions breakdown by activity type"""
        results = (
            db.query(
                EmissionActivity.activity_type,
                func.sum(EmissionActivity.co2e_kg).label("total")
            )
            .filter(EmissionActivity.project_id == project_id)
            .group_by(EmissionActivity.activity_type)
            .all()
        )
        
        return {activity_type: float(total) for activity_type, total in results}
    
    def get_emissions_timeline(
        self,
        db: Session,
        *,
        project_id: str,
        group_by: str = "month"  # day, month, year
    ) -> List[Dict[str, Any]]:
        """Get emissions over time for charting"""
        if group_by == "month":
            date_trunc = func.date_trunc('month', EmissionActivity.activity_date)
        elif group_by == "day":
            date_trunc = func.date_trunc('day', EmissionActivity.activity_date)
        else:
            date_trunc = func.date_trunc('year', EmissionActivity.activity_date)
        
        results = (
            db.query(
                date_trunc.label("period"),
                func.sum(EmissionActivity.co2e_kg).label("total_co2e")
            )
            .filter(EmissionActivity.project_id == project_id)
            .group_by("period")
            .order_by("period")
            .all()
        )
        
        return [
            {
                "period": period.isoformat(),
                "total_co2e": float(total_co2e)
            }
            for period, total_co2e in results
        ]


# Create CRUD instance
crud_activity = CRUDActivity(EmissionActivity)
