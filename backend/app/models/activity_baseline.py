"""
Activity Baseline Model
Monthly baseline profiles for seasonal anomaly awareness.

Stores P10/P50/P90 percentile bands per activity type per month,
enabling detection of seasonal anomalies (e.g., high heating in summer).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ActivityBaseline(Base):
    """
    Monthly baseline profiles for activity types.
    
    Used by anomaly detector to:
    - Understand seasonal patterns
    - Detect out-of-season anomalies
    - Contextualize findings
    """
    
    __tablename__ = "activity_baselines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Activity classification
    activity_type = Column(String(50), nullable=False, index=True)  # electricity, heating, fuel
    month = Column(Integer, nullable=False)  # 1-12
    
    # Percentile bands (kg CO2e)
    p10 = Column(Numeric(20, 6), nullable=True)   # 10th percentile (low end)
    p50 = Column(Numeric(20, 6), nullable=True)   # Median (typical value)
    p90 = Column(Numeric(20, 6), nullable=True)   # 90th percentile (high end)
    
    # Metadata
    sample_count = Column(Integer, default=0)  # Number of data points used
    last_calculated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="activity_baselines")
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'activity_type', 'month', 
                         name='uq_baseline_org_type_month'),
    )
    
    def __repr__(self):
        return f"<ActivityBaseline {self.activity_type} month={self.month} p50={self.p50}>"
    
    def is_above_normal(self, value: float) -> bool:
        """Check if value is above P90"""
        if self.p90 is None:
            return False
        return value > float(self.p90)
    
    def is_below_normal(self, value: float) -> bool:
        """Check if value is below P10"""
        if self.p10 is None:
            return False
        return value < float(self.p10)
    
    def get_range_description(self) -> str:
        """Get human-readable range description"""
        if self.p10 is None or self.p90 is None:
            return "Insufficient data"
        return f"{float(self.p10):,.0f} - {float(self.p90):,.0f} kg CO₂e"
