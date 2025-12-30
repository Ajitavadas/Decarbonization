"""
Organization model for multi-tenancy
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Organization(Base):
    """Organization/Tenant model"""
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    country = Column(String(2), nullable=True)  # ISO 3166-1 Alpha-2
    
    # Configuration settings
    settings = Column(JSON, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    custom_mappings = relationship("CustomMapping", back_populates="organization", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Organization {self.name}>"
