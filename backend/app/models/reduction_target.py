"""
Reduction Target model - Emission reduction targets with interim milestones
"""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index, Integer, Boolean
from app.db.types import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class ReductionTarget(Base):
    """
    Emission reduction target for an organization
    
    Supports:
    - Absolute targets (reduce to X kg CO2e)
    - Percentage targets (reduce by X%)
    - Interim milestones (e.g., 2025: -10%, 2030: -30%)
    - Scope-specific or organization-wide targets
    """
    
    __tablename__ = "reduction_targets"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Organization scope
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=True)  # Optional project-specific
    
    # Target definition
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    target_type = Column(String(20), nullable=False)  # "absolute" | "percentage"
    scope = Column(String(20), nullable=True)  # "Scope 1", "Scope 2", "Scope 3", "all"
    
    # Baseline values
    baseline_year = Column(String(4), nullable=False)
    baseline_value = Column(Numeric(20, 6), nullable=False)  # kg CO2e
    
    # Final target
    target_year = Column(String(4), nullable=False)
    target_value = Column(Numeric(20, 6), nullable=False)  # kg CO2e for absolute, % for percentage
    
    # Interim milestones (JSONB for flexibility)
    # Format: [{"year": "2025", "value": 10.0, "achieved": false}, {"year": "2030", "value": 30.0, "achieved": false}]
    milestones = Column(JSONB, default=[])
    
    # Current tracking
    current_year = Column(String(4), nullable=True)
    current_value = Column(Numeric(20, 6), nullable=True)  # Latest calculated kg CO2e
    current_reduction_pct = Column(Numeric(12, 2), nullable=True)  # Current % reduction from baseline (can be very large)
    
    # Progress calculation
    progress_percentage = Column(Numeric(5, 2), nullable=True)  # 0-100 (progress toward final target)
    
    # Status
    status = Column(String(20), default="on_track")  # "on_track", "at_risk", "off_track", "achieved"
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_calculated_at = Column(DateTime, nullable=True)  # When progress was last calculated
    
    # Relationships
    organization = relationship("Organization", backref="reduction_targets")
    project = relationship("Project", backref="reduction_targets")
    
    # Indexes
    __table_args__ = (
        Index('idx_target_org_status', 'organization_id', 'status'),
        Index('idx_target_org_scope', 'organization_id', 'scope'),
    )
    
    def __repr__(self):
        return f"<ReductionTarget {self.name} ({self.target_type}: {self.target_value})>"
    
    @property
    def is_percentage_target(self) -> bool:
        """Check if this is a percentage-based target"""
        return self.target_type == "percentage"
    
    @property
    def target_absolute_value(self) -> Decimal:
        """Get the absolute target value in kg CO2e"""
        if self.is_percentage_target:
            # Convert percentage to absolute
            reduction = self.baseline_value * (self.target_value / 100)
            return self.baseline_value - reduction
        return self.target_value
    
    def calculate_progress(self, current_emissions: Decimal) -> dict:
        """
        Calculate progress toward target
        
        Returns:
            dict with progress_percentage, current_reduction_pct, status
        """
        if self.baseline_value == 0:
            return {"progress_percentage": 0, "current_reduction_pct": 0, "status": "on_track"}
        
        # Calculate current reduction percentage
        current_reduction_pct = ((self.baseline_value - current_emissions) / self.baseline_value) * 100
        
        # Calculate progress toward final target
        if self.is_percentage_target:
            # For percentage targets, compare reduction percentages
            if self.target_value == 0:
                progress = 0
            else:
                progress = (current_reduction_pct / self.target_value) * 100
        else:
            # For absolute targets, compare emissions values
            total_reduction_needed = self.baseline_value - self.target_value
            if total_reduction_needed == 0:
                progress = 100 if current_emissions <= self.target_value else 0
            else:
                actual_reduction = self.baseline_value - current_emissions
                progress = (actual_reduction / total_reduction_needed) * 100
        
        # Cap progress at 100%
        progress = min(max(progress, 0), 100)
        
        # Determine status based on progress and time
        import datetime as dt
        current_year = int(dt.datetime.now().year)
        target_year = int(self.target_year)
        baseline_year = int(self.baseline_year)
        
        years_total = target_year - baseline_year
        years_elapsed = current_year - baseline_year
        
        if years_total > 0 and years_elapsed > 0:
            expected_progress = (years_elapsed / years_total) * 100
            
            if progress >= 100:
                status = "achieved"
            elif progress >= expected_progress * 0.9:  # Within 10% of expected
                status = "on_track"
            elif progress >= expected_progress * 0.7:  # Within 30% of expected
                status = "at_risk"
            else:
                status = "off_track"
        else:
            status = "on_track"
        
        return {
            "progress_percentage": round(progress, 2),
            "current_reduction_pct": round(current_reduction_pct, 2),
            "status": status
        }
