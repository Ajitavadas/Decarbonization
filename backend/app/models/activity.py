"""
Emission Activity model - Core ledger for all carbon activities
Polymorphic JSONB storage for different activity types
"""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index
from app.db.types import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class EmissionActivity(Base):
    """
    Central polymorphic activity table for all emission calculations
    
    Uses JSONB for flexible storage of activity-specific data while
    maintaining structured fields for common attributes
    """
    
    __tablename__ = "emission_activities"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Activity classification
    activity_type = Column(String(50), nullable=False, index=True)  # travel, freight, energy, procurement
    sub_type = Column(String(50), nullable=True)  # electricity, fuel, air, road, etc.
    
    # Scope classification (auto-assigned)
    scope = Column(String(10), nullable=False, index=True)  # Scope 1, Scope 2, Scope 3
    
    # Activity date
    activity_date = Column(DateTime, nullable=False, index=True)
    
    # Emission results
    co2e_kg = Column(Numeric(20, 6), nullable=False)  # Result in kg CO2e
    co2e_unit = Column(String(10), default="kg")
    calculation_method = Column(String(20), default="ipcc_ar6_gwp100")  # ar4, ar5, ar6
    
    # Constituent gases (optional detailed breakdown)
    constituent_gases = Column(JSONB, nullable=True)  # {"co2": 100, "ch4": 0.5, "n2o": 0.1}
    
    # Raw input data (JSONB for auditability)
    input_data = Column(JSONB, nullable=False)  # Complete Climatiq request payload
    
    # Climatiq metadata
    emission_factor_id = Column(String(255), nullable=True, index=True)
    source_dataset = Column(String(100), nullable=True)
    data_version = Column(String(20), nullable=True)
    region = Column(String(10), nullable=True)
    year = Column(String(4), nullable=True)
    
    # Additional metadata
    description = Column(String(500), nullable=True)
    content_hash = Column(String(64), nullable=True, unique=True, index=True)  # SHA256 hash for deduplication
    tags = Column(JSONB, default=[])  # ["business-travel", "client-meeting"]
    
    # Relationships
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="activities")
    
    batch_job_id = Column(UUID, ForeignKey("batch_jobs.id"), nullable=True)
    batch_job = relationship("BatchJob", back_populates="activities")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_activity_project_date', 'project_id', 'activity_date'),
        Index('idx_activity_scope_type', 'scope', 'activity_type'),
        Index('idx_input_data_gin', 'input_data', postgresql_using='gin'),  # GIN index for JSONB queries
    )
    
    def __repr__(self):
        return f"<EmissionActivity {self.activity_type} - {self.co2e_kg} kg CO2e>"
