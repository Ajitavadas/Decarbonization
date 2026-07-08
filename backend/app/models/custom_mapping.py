"""
Custom Mapping model - Organizational memory for ERP integration
Maps internal codes to Climatiq emission factors
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, UniqueConstraint
from app.db.types import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class CustomMapping(Base):
    """
    Store organization-specific mappings from ERP codes to Climatiq factors
    
    Example: Internal code "LAPTOP-DELL" -> Climatiq activity "computer-equipment_manufacturing"
    """
    
    __tablename__ = "custom_mappings"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Internal identifier (from ERP, accounting system, etc.)
    internal_label = Column(String(255), nullable=False)
    internal_code = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)  # "electronics", "travel", "utilities"
    
    # Climatiq mapping
    climatiq_activity_id = Column(String(255), nullable=False)
    climatiq_region = Column(String(10), nullable=True)
    climatiq_year = Column(String(4), nullable=True)
    climatiq_source = Column(String(100), nullable=True)
    
    # Mapping quality
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0 (from Autopilot suggestions)
    mapping_method = Column(String(50), nullable=False)  # "manual", "autopilot", "bulk_import"
    
    # Additional parameters (stored as JSONB for flexibility)
    default_parameters = Column(JSONB, nullable=True)  # Default values for calculations
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="custom_mappings")
    
    created_by = Column(UUID, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one mapping per internal code per organization
    __table_args__ = (
        UniqueConstraint('organization_id', 'internal_label', name='uix_org_internal_label'),
    )
    
    def __repr__(self):
        return f"<CustomMapping {self.internal_label} -> {self.climatiq_activity_id}>"
