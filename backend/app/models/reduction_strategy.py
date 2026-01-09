"""
Reduction Strategy model - AI-generated reduction strategies with caching
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class ReductionStrategy(Base):
    """
    AI-generated reduction strategy (cached)
    
    Features:
    - Archetype-specific recommendations
    - Cached for 7 days to respect rate limits
    - Impact estimates (kg CO2e, cost, payback)
    - Difficulty ratings
    """
    
    __tablename__ = "reduction_strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Scope
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("reduction_targets.id"), nullable=True)
    
    # Strategy details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # "energy", "travel", "procurement", "operations", "facility"
    scope = Column(String(20), nullable=True)  # Which scope this strategy affects
    
    # Archetype context
    archetype = Column(String(50), nullable=True)  # Organization archetype when generated
    
    # Impact estimates
    estimated_reduction_kg = Column(Numeric(20, 6), nullable=True)  # kg CO2e per year
    estimated_reduction_pct = Column(Numeric(5, 2), nullable=True)  # % of target scope
    estimated_cost = Column(Numeric(15, 2), nullable=True)  # Implementation cost
    estimated_savings = Column(Numeric(15, 2), nullable=True)  # Annual savings
    payback_period_months = Column(Integer, nullable=True)
    
    # Difficulty and priority
    difficulty = Column(String(20), nullable=True)  # "easy", "medium", "hard"
    priority = Column(Integer, default=1)  # 1 = highest priority
    implementation_timeframe = Column(String(50), nullable=True)  # "immediate", "short-term", "medium-term", "long-term"
    
    # AI metadata
    model_used = Column(String(50), nullable=True)  # "llama-3.3-70b-versatile"
    prompt_hash = Column(String(64), nullable=True, index=True)  # For cache lookup
    source = Column(String(20), default="ai")  # "ai" or "manual"
    
    # Cache control (7 day TTL)
    expires_at = Column(DateTime, nullable=True)
    
    # Status tracking
    status = Column(String(30), default="suggested")  # "suggested", "considering", "in_progress", "completed", "rejected"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_strategy_org_target', 'organization_id', 'target_id'),
        Index('idx_strategy_cache', 'prompt_hash', 'expires_at'),
        Index('idx_strategy_archetype', 'organization_id', 'archetype'),
    )
    
    def __repr__(self):
        return f"<ReductionStrategy {self.title} ({self.category})>"
    
    @property
    def is_cached_valid(self) -> bool:
        """Check if cached strategy is still valid"""
        if not self.expires_at:
            return False
        return datetime.utcnow() < self.expires_at
    
    @classmethod
    def create_with_ttl(cls, days: int = 7, **kwargs):
        """Create a strategy with automatic TTL"""
        kwargs['expires_at'] = datetime.utcnow() + timedelta(days=days)
        return cls(**kwargs)
    
    def to_display_dict(self) -> dict:
        """Convert to frontend display format"""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "scope": self.scope,
            "difficulty": self.difficulty,
            "priority": self.priority,
            "implementation_timeframe": self.implementation_timeframe,
            "estimated_reduction_kg": float(self.estimated_reduction_kg) if self.estimated_reduction_kg else None,
            "estimated_reduction_pct": float(self.estimated_reduction_pct) if self.estimated_reduction_pct else None,
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost else None,
            "estimated_savings": float(self.estimated_savings) if self.estimated_savings else None,
            "payback_period_months": self.payback_period_months,
            "source": self.source,
            "status": self.status,
            "is_ai_generated": self.source == "ai",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
