"""
Baseline Builder Service
Calculates seasonal baseline profiles for anomaly detection.

Runs as a batch job (weekly) to build P10/P50/P90 percentile bands
for each activity type per month. This enables seasonal awareness
in anomaly detection.

100% deterministic - NO LLM calls.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.activity import EmissionActivity
from app.models.project import Project
from app.models.activity_baseline import ActivityBaseline

logger = logging.getLogger(__name__)

# Activity types that recur monthly and benefit from seasonal baselines
RECURRING_ACTIVITY_TYPES = [
    "electricity",
    "heating",
    "stationary_combustion",
    "fuel",
    "natural_gas",
    "water",
    "waste"
]


class BaselineBuilder:
    """
    Builds seasonal baseline profiles from historical emission data.
    
    Features:
    - P10/P50/P90 percentile bands per activity type per month
    - Minimum sample requirement for reliability
    - Automatic updates via batch job
    """
    
    MIN_SAMPLES = 3  # Minimum data points needed for baseline
    
    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id
    
    def build_all_baselines(self) -> Dict[str, int]:
        """
        Build baselines for all recurring activity types.
        
        Returns dict of activity_type -> count of baselines created/updated.
        """
        results = {}
        
        for activity_type in RECURRING_ACTIVITY_TYPES:
            count = self.build_baselines_for_type(activity_type)
            results[activity_type] = count
            logger.info(f"Built {count} monthly baselines for {activity_type}")
        
        return results
    
    def build_baselines_for_type(self, activity_type: str) -> int:
        """Build baselines for a specific activity type."""
        count = 0
        
        for month in range(1, 13):
            baseline = self._calculate_monthly_baseline(activity_type, month)
            
            if baseline:
                self._upsert_baseline(baseline)
                count += 1
        
        self.db.commit()
        return count
    
    def _calculate_monthly_baseline(
        self,
        activity_type: str,
        month: int
    ) -> Optional[Dict]:
        """Calculate percentile bands for a specific activity type and month."""
        
        # Get all historical values for this activity type in this month
        values = self.db.query(EmissionActivity.co2e_kg).join(Project).filter(
            Project.organization_id == self.organization_id,
            EmissionActivity.activity_type == activity_type,
            extract('month', EmissionActivity.activity_date) == month,
            EmissionActivity.co2e_kg > 0
        ).all()
        
        values = [float(v[0]) for v in values if v[0]]
        
        if len(values) < self.MIN_SAMPLES:
            return None
        
        # Calculate percentiles
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        p10 = self._percentile(sorted_values, 10)
        p50 = self._percentile(sorted_values, 50)
        p90 = self._percentile(sorted_values, 90)
        
        return {
            "organization_id": self.organization_id,
            "activity_type": activity_type,
            "month": month,
            "p10": Decimal(str(p10)),
            "p50": Decimal(str(p50)),
            "p90": Decimal(str(p90)),
            "sample_count": n,
            "last_calculated": datetime.utcnow()
        }
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted list."""
        if not sorted_values:
            return 0
        
        n = len(sorted_values)
        idx = (percentile / 100) * (n - 1)
        lower = int(idx)
        upper = min(lower + 1, n - 1)
        weight = idx - lower
        
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    def _upsert_baseline(self, baseline_data: Dict):
        """Insert or update a baseline record."""
        existing = self.db.query(ActivityBaseline).filter(
            ActivityBaseline.organization_id == baseline_data["organization_id"],
            ActivityBaseline.activity_type == baseline_data["activity_type"],
            ActivityBaseline.month == baseline_data["month"]
        ).first()
        
        if existing:
            # Update existing
            existing.p10 = baseline_data["p10"]
            existing.p50 = baseline_data["p50"]
            existing.p90 = baseline_data["p90"]
            existing.sample_count = baseline_data["sample_count"]
            existing.last_calculated = baseline_data["last_calculated"]
        else:
            # Create new
            baseline = ActivityBaseline(**baseline_data)
            self.db.add(baseline)
    
    def get_baseline(
        self,
        activity_type: str,
        month: int
    ) -> Optional[ActivityBaseline]:
        """Get baseline for a specific activity type and month."""
        return self.db.query(ActivityBaseline).filter(
            ActivityBaseline.organization_id == self.organization_id,
            ActivityBaseline.activity_type == activity_type,
            ActivityBaseline.month == month
        ).first()
    
    def get_all_baselines(self) -> List[ActivityBaseline]:
        """Get all baselines for organization."""
        return self.db.query(ActivityBaseline).filter(
            ActivityBaseline.organization_id == self.organization_id
        ).order_by(
            ActivityBaseline.activity_type,
            ActivityBaseline.month
        ).all()


def create_baseline_builder(db: Session, organization_id: UUID) -> BaselineBuilder:
    """Factory function for BaselineBuilder."""
    return BaselineBuilder(db, organization_id)
