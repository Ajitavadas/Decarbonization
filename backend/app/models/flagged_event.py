"""
FlaggedEvent model - Audit findings from the Carbon Accounting Auditor Agent
Stores detected gaps, anomalies, and archetype mismatches per organization
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, Integer, Numeric
from app.db.types import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class FlaggedEvent(Base):
    """
    Audit finding from the Carbon Accounting Auditor Agent
    
    Stores detected issues including:
    - Data gaps (missing months, missing scopes)
    - Anomalies (statistical outliers, implausible values)
    - Archetype mismatches (fingerprint violations)
    """
    
    __tablename__ = "flagged_events"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Organization scope (always required for isolation)
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    
    # Optional linkage to specific project or activity
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=True)
    activity_id = Column(UUID, ForeignKey("emission_activities.id"), nullable=True)
    
    # Classification
    flag_type = Column(String(50), nullable=False, index=True)  # "gap", "anomaly", "archetype_mismatch"
    severity = Column(String(20), nullable=False, index=True)   # "info", "warning", "critical"
    rule_id = Column(String(100), nullable=False)  # e.g., "temporal_gap_electricity", "outlier_zscore"
    
    # Human-readable details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    
    # Supporting evidence (JSONB for flexibility)
    evidence = Column(JSONB, nullable=True)  # Raw data that triggered the flag
    
    # Status tracking
    status = Column(String(30), default="open", nullable=False, index=True)  # "open", "acknowledged", "resolved", "false_positive"
    resolved_by = Column(UUID, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Confidence scoring (composable formula, no AI required)
    confidence_score = Column(Integer, nullable=True)  # 0-100
    confidence_breakdown = Column(JSONB, nullable=True)  # {"completeness": 40, "detection_method": 25, "historical_match": 20, "activity_count": 15}
    
    # AI-generated explanation (cached)
    ai_explanation = Column(Text, nullable=True)
    ai_explanation_model = Column(String(50), nullable=True)  # Which model generated it
    ai_explanation_at = Column(DateTime, nullable=True)
    
    # AI Classification (from enhanced AI analysis)
    # A=data quality issue, B=operational anomaly, C=seasonal variation, D=high-emission needing mitigation
    ai_verdict = Column(String(1), nullable=True)  # A, B, C, or D
    ai_verdict_explanation = Column(Text, nullable=True)  # Detailed explanation from AI
    required_evidence = Column(JSONB, nullable=True)  # ["Check SCADA sensor X", "Verify invoice Y"]
    co2e_90d_estimate = Column(Numeric(20, 6), nullable=True)  # Estimated CO2 impact if unresolved for 90 days
    ai_confidence = Column(String(1), nullable=True)  # H, M, or L
    immediate_action = Column(Text, nullable=True)  # What to do now
    next_action = Column(Text, nullable=True)  # What to do in 3-6 weeks
    
    # Audit metadata
    audit_run_id = Column(UUID, nullable=True)  # Groups findings from same audit run
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="flagged_events")
    project = relationship("Project", backref="flagged_events")
    activity = relationship("EmissionActivity", backref="flagged_events")
    resolver = relationship("User", backref="resolved_flags")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_flagged_org_status', 'organization_id', 'status'),
        Index('idx_flagged_org_type', 'organization_id', 'flag_type'),
        Index('idx_flagged_audit_run', 'audit_run_id'),
    )
    
    def __repr__(self):
        return f"<FlaggedEvent {self.flag_type}:{self.severity} - {self.title[:50]}>"
