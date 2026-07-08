"""
Project model for organizing emission activities
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Text
from app.db.types import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Project(Base):
    """Reporting project model"""
    
    __tablename__ = "projects"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Reporting period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Reporting year (for convenience)
    reporting_year = Column(String(4), nullable=False, index=True)
    
    # Relationships
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="projects")
    
    activities = relationship("EmissionActivity", back_populates="project", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Project {self.name} ({self.reporting_year})>"
