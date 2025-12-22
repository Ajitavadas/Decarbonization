from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, Boolean, ForeignKey, Index, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class Organization(Base):
    """Organization model from schema.sql"""
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_name = Column(String(255), unique=True, nullable=False)
    industry = Column(String(10))  # NAICS code
    countries = Column(ARRAY(Text), default=[])
    headcount = Column(Integer)
    annual_revenue = Column(DECIMAL(15, 2))
    is_public_company = Column(Boolean, default=False)
    listing_status = Column(String(50)) # public, private, subsidiary
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True))
    
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    emission_events = relationship("EmissionEvent", back_populates="organization")
    calculation_ledgers = relationship("CalculationLedger", back_populates="organization")

class User(Base):
    """User model from schema.sql"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(512))
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50)) # admin, auditor, analyst, viewer
    permissions = Column(JSON)
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="users")

class EmissionFactor(Base):
    """EmissionFactor model from schema.sql"""
    __tablename__ = "emission_factors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(Text, nullable=False)
    region = Column(String(20), nullable=False)
    region_name = Column(String(255))
    country_name = Column(String(255))
    year = Column(Integer, nullable=False)
    scope = Column(String(20), nullable=False) # Scope 1, Scope 2, Scope 3
    sector = Column(String(100))
    category = Column(String(255))
    industry_code = Column(String(10))
    
    factor_value = Column(Numeric(12, 8), nullable=False)
    factor_value_co2 = Column(Numeric(12, 8))
    factor_value_ch4 = Column(Numeric(12, 8))
    factor_value_n2o = Column(Numeric(12, 8))
    
    activity_unit = Column(String(50), nullable=False)
    emissions_unit = Column(String(50))
    emissions_type = Column(String(100))
    
    calculation_method = Column(String(100))
    ghg_protocol_method = Column(String(100))
    gwp_version = Column(String(50))
    
    data_source_version = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

class EmissionEvent(Base):
    """EmissionEvent model from schema.sql (Phase 1)"""
    __tablename__ = "emission_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    # emission_source_id is required in schema but let's make it optional or handle if not present
    # For simplicity of import, we might need to create sources or link them
    activity_date = Column(DateTime(timezone=True), nullable=False)
    
    activity_value = Column(DECIMAL(15, 2), nullable=False)
    activity_unit_raw = Column(String(50))
    activity_unit_normalized = Column(String(50), nullable=False)
    activity_value_normalized = Column(DECIMAL(15, 2), nullable=False)
    
    source_type = Column(String(50)) # primary_supplier, secondary_benchmark, estimated
    scope = Column(String(20)) # Scope 1, Scope 2, Scope 3
    scope_3_category = Column(String(20))
    
    activity_id_matched = Column(String(255), ForeignKey("emission_factors.activity_id"))
    confidence_score = Column(Numeric(3, 2))
    needs_review = Column(Boolean, default=False)
    verified_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    organization = relationship("Organization", back_populates="emission_events")
    calculation_ledger = relationship("CalculationLedger", back_populates="emission_event", uselist=False)

class CalculationLedger(Base):
    """CalculationLedger model from schema.sql (Phase 2)"""
    __tablename__ = "calculation_ledger"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(String(100))
    calculation_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    emission_event_id = Column(UUID(as_uuid=True), ForeignKey("emission_events.id", ondelete="RESTRICT"), nullable=False)
    
    activity_value = Column(Numeric(15, 2))
    activity_unit_normalized = Column(String(50))
    
    emission_factor_id = Column(UUID(as_uuid=True), ForeignKey("emission_factors.id"), nullable=True)
    emission_factor_value = Column(Numeric(12, 8))
    
    result_kg_co2e = Column(DECIMAL(15, 2))
    result_kg_total = Column(DECIMAL(15, 2))
    
    fell_back_to_climatiq = Column(Boolean, default=False)
    
    calculated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    organization = relationship("Organization", back_populates="calculation_ledgers")
    emission_event = relationship("EmissionEvent", back_populates="calculation_ledger")

class AuditTrail(Base):
    """AuditTrail model from schema.sql"""
    __tablename__ = "audit_trail"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(100))
    resource_type = Column(String(100))
    resource_id = Column(UUID(as_uuid=True))
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    action_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# FlaggedEvent for Phase 2
class FlaggedEvent(Base):
    __tablename__ = "flagged_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(String(500), nullable=False)
    details = Column(JSON)
    status = Column(String(50), default="open")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))