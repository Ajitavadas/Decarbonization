# app/models/models.py
"""
SQLAlchemy ORM models for the Decarbonization Platform
- User: Authentication and user management
- EmissionTransaction: Carbon emission records
- EmissionFactor: Standard emission conversion factors
- AuditLog: Audit trail for compliance
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships - specify foreign_keys to avoid ambiguity
    emission_transactions = relationship(
        "EmissionTransaction", 
        foreign_keys="EmissionTransaction.created_by_user_id",
        back_populates="created_by_user"
    )
    verified_transactions = relationship(
        "EmissionTransaction",
        foreign_keys="EmissionTransaction.verified_by_user_id",
        back_populates="verified_by_user"
    )
    audit_logs = relationship("AuditLog", back_populates="user")
    organization = relationship("Organization", back_populates="users")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_users_email_org", "email", "organization_id"),
        Index("idx_users_is_active", "is_active"),
    )


class Organization(Base):
    """Organization model for multi-tenancy support"""
    __tablename__ = "organizations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    emission_transactions = relationship("EmissionTransaction", back_populates="organization")
    emission_factors = relationship("EmissionFactor", back_populates="organization")
    audit_logs = relationship("AuditLog", back_populates="organization")


class EmissionTransaction(Base):
    """Model for individual emission transactions"""
    __tablename__ = "emission_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Transaction details
    description = Column(String(500), nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Emission classification (Scope 1/2/3)
    scope = Column(Integer, nullable=False, index=True)  # 1, 2, or 3
    category = Column(String(100), nullable=False, index=True)  # e.g., "Fuel", "Electricity", "Business Travel"
    
    # Activity data
    activity_value = Column(Float, nullable=False)
    activity_unit = Column(String(50), nullable=False)  # e.g., "kWh", "liters", "kg"
    
    # Emission factor and calculation
    emission_factor_id = Column(String(36), ForeignKey("emission_factors.id"), nullable=True)
    emission_factor_value = Column(Float, nullable=False)  # CO2e per unit
    
    # Calculated emissions
    co2e_kg = Column(Float, nullable=False, index=True)  # Total CO2e in kilograms
    co2e_tonnes = Column(Float, nullable=False)  # Total CO2e in metric tonnes
    
    # AI Classification Fields
    ai_scope_prediction = Column(Integer, nullable=True, index=True)
    ai_confidence_score = Column(Float, nullable=True, index=True)
    ai_needs_review = Column(Boolean, default=False, index=True)
    
    # Metadata
    supplier_name = Column(String(255), nullable=True, index=True)
    project_id = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Audit trail
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    verified_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    manager_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships - explicitly specify foreign_keys to avoid ambiguity
    organization = relationship("Organization", back_populates="emission_transactions")
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="emission_transactions"
    )
    verified_by_user = relationship(
        "User",
        foreign_keys=[verified_by_user_id],
        back_populates="verified_transactions" #back_populates="verified_classifications
    )
    emission_factor = relationship("EmissionFactor", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index("idx_emission_org_date", "organization_id", "transaction_date"),
        Index("idx_emission_org_scope", "organization_id", "scope"),
        Index("idx_emission_org_category", "organization_id", "category"),
        Index("idx_ai_needs_review_org", "organization_id", "ai_needs_review"),
        Index("idx_verified_by_org", "organization_id", "verified_at"),
    )


class EmissionFactor(Base):
    """Model for standard emission conversion factors"""
    __tablename__ = "emission_factors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)  # NULL = global factor
    
    # Factor details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=False)  # e.g., "EPA", "IPCC", "GHG Protocol"
    
    # Classification
    scope = Column(Integer, nullable=False, index=True)  # 1, 2, or 3
    category = Column(String(100), nullable=False, index=True)  # e.g., "Fuel", "Electricity", "Scope 3 - Waste"
    subcategory = Column(String(100), nullable=True, index=True)  # e.g., "Gasoline", "Coal", "Grid"
    
    # Factor value and unit
    factor_value = Column(Float, nullable=False)  # CO2e value
    factor_unit = Column(String(50), nullable=False)  # e.g., "kg CO2e/kWh", "kg CO2e/liter"
    
    # Geographic/regional info
    region = Column(String(100), nullable=True, index=True)  # e.g., "US-West", "EU", "Global"
    country = Column(String(100), nullable=True, index=True)
    
    # Versioning and dates
    version = Column(String(50), nullable=False, default="1.0")
    effective_date = Column(DateTime(timezone=True), nullable=False, index=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="emission_factors")
    transactions = relationship("EmissionTransaction", back_populates="emission_factor")
    
    # Indexes
    __table_args__ = (
        Index("idx_factor_scope_category", "scope", "category"),
        Index("idx_factor_region_active", "region", "is_active"),
    )


class AuditLog(Base):
    """Model for audit logging and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Action details
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    resource_type = Column(String(100), nullable=False, index=True)  # "User", "EmissionTransaction", etc.
    resource_id = Column(String(36), nullable=True, index=True)
    
    # Change details
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Additional context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    organization = relationship("Organization", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_org_date", "organization_id", "created_at"),
        Index("idx_audit_user_date", "user_id", "created_at"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
    )
