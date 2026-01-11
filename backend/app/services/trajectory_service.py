"""
Trajectory Service
Predicts whether reduction targets will be achieved based on historical trends.

Design: 100% deterministic - NO LLM calls. Uses linear regression with confidence gating.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.activity import EmissionActivity
from app.models.reduction_target import ReductionTarget
from app.models.project import Project

logger = logging.getLogger(__name__)


class TrajectoryService:
    """
    Predicts target achievement based on historical emission trends.
    
    Features:
    - Linear regression with R² confidence scoring
    - Projection clamped to non-negative values
    - Confidence gating (warns when data is unstable)
    - Required annual reduction calculation
    """
    
    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id
    
    def predict(self, target: ReductionTarget) -> Dict[str, Any]:
        """
        Predict if a reduction target will be achieved at current rate.
        
        Args:
            target: The reduction target to analyze
            
        Returns:
            Prediction dict with projected values and confidence
        """
        # Get historical yearly emissions
        historical = self._get_yearly_emissions(
            start_year=int(target.baseline_year),
            end_year=datetime.now().year,
            scope=target.scope
        )
        
        if len(historical) < 2:
            return {
                "status": "insufficient_data",
                "confidence": "low",
                "message": "Need at least 2 years of data for trajectory prediction",
                "data_points": len(historical)
            }
        
        # Perform linear regression
        years = list(historical.keys())
        emissions = list(historical.values())
        
        try:
            slope, intercept, r_squared = self._linear_regression(years, emissions)
        except Exception as e:
            logger.warning(f"Regression failed: {e}")
            return {
                "status": "calculation_error",
                "confidence": "low",
                "message": "Unable to calculate trend"
            }
        
        # Confidence gating based on R²
        if r_squared < 0.4:
            return {
                "status": "unstable_pattern",
                "confidence": "low",
                "message": "Emission pattern too variable for reliable projection",
                "r_squared": round(r_squared, 2),
                "suggestion": "Your emissions vary significantly year to year. Consider reviewing data quality."
            }
        
        # Project to target year
        target_year = int(target.target_year)
        projected = max(0, slope * target_year + intercept)  # Clamp non-negative
        
        # Calculate target emissions based on type
        target_emissions = self._calculate_target_emissions(target)
        
        gap = projected - target_emissions
        on_track = gap <= 0
        
        # Calculate required annual reduction
        current_year = datetime.now().year
        current_emissions = emissions[-1] if emissions else 0
        years_remaining = target_year - current_year
        
        if years_remaining > 0:
            required_annual = (current_emissions - target_emissions) / years_remaining
        else:
            required_annual = 0
        
        # Determine status
        if on_track:
            status = "on_track"
            message = "At current rate, you're projected to meet this target"
        else:
            pct_gap = abs(gap / target_emissions) * 100 if target_emissions > 0 else 0
            if pct_gap < 20:
                status = "at_risk"
                message = f"Projected to miss target by {pct_gap:.0f}%. Acceleration needed."
            else:
                status = "off_track"
                message = f"Projected to miss target by {pct_gap:.0f}%. Significant action required."
        
        return {
            "status": status,
            "confidence": "high" if r_squared > 0.7 else "medium",
            "message": message,
            "projection": {
                "target_year": target_year,
                "projected_emissions": round(projected, 0),
                "target_emissions": round(target_emissions, 0),
                "gap": round(gap, 0),
                "on_track": on_track
            },
            "trend": {
                "direction": "decreasing" if slope < 0 else "increasing",
                "annual_change": round(slope, 0),
                "r_squared": round(r_squared, 2)
            },
            "action_required": {
                "required_annual_reduction": round(required_annual, 0),
                "years_remaining": years_remaining
            },
            "historical": {str(y): round(e, 0) for y, e in zip(years, emissions)}
        }
    
    def _get_yearly_emissions(
        self,
        start_year: int,
        end_year: int,
        scope: Optional[str] = None
    ) -> Dict[int, float]:
        """Get yearly emission totals"""
        query = self.db.query(
            extract('year', EmissionActivity.activity_date).label('year'),
            func.sum(EmissionActivity.co2e_kg).label('total')
        ).join(Project).filter(
            Project.organization_id == self.organization_id,
            extract('year', EmissionActivity.activity_date) >= start_year,
            extract('year', EmissionActivity.activity_date) <= end_year
        )
        
        if scope and scope != "all":
            query = query.filter(EmissionActivity.scope == scope)
        
        query = query.group_by(
            extract('year', EmissionActivity.activity_date)
        ).order_by(
            extract('year', EmissionActivity.activity_date)
        )
        
        results = query.all()
        return {int(year): float(total) for year, total in results if total}
    
    def _linear_regression(
        self,
        x: List[int],
        y: List[float]
    ) -> tuple[float, float, float]:
        """
        Simple linear regression: y = slope * x + intercept
        Returns (slope, intercept, r_squared)
        """
        n = len(x)
        if n < 2:
            raise ValueError("Need at least 2 data points")
        
        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        # Calculate slope and intercept
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        if denominator == 0:
            raise ValueError("Cannot calculate regression with constant x values")
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate R² (coefficient of determination)
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((yi - ypi) ** 2 for yi, ypi in zip(y, y_pred))
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return slope, intercept, max(0, r_squared)  # Clamp R² to non-negative
    
    def _calculate_target_emissions(self, target: ReductionTarget) -> float:
        """Calculate target emissions based on target type"""
        baseline = float(target.baseline_value) if target.baseline_value else 0
        target_value = float(target.target_value) if target.target_value else 0
        
        if target.target_type == "percentage":
            # Target value is percentage reduction (e.g., 30%)
            return baseline * (1 - target_value / 100)
        else:
            # Absolute target value
            return target_value
    
    def get_all_target_trajectories(self) -> List[Dict[str, Any]]:
        """Get trajectory predictions for all active targets"""
        targets = self.db.query(ReductionTarget).filter(
            ReductionTarget.organization_id == self.organization_id,
            ReductionTarget.is_active == True
        ).all()
        
        results = []
        for target in targets:
            prediction = self.predict(target)
            results.append({
                "target_id": str(target.id),
                "target_name": target.name,
                "target_year": target.target_year,
                **prediction
            })
        
        return results


def create_trajectory_service(db: Session, organization_id: UUID) -> TrajectoryService:
    """Factory function for TrajectoryService"""
    return TrajectoryService(db, organization_id)
