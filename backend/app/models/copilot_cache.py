"""
Copilot Cache model - LLM response caching for rate-limit management
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class CopilotCache(Base):
    """
    Cache for LLM responses to reduce API calls
    
    Golden Rule: Every LLM output must be cacheable and replayable.
    Expected to reduce LLM usage by 60-80%.
    
    TTL: 7 days by default
    """
    
    __tablename__ = "copilot_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Cache key (SHA256 hash of query + context)
    query_hash = Column(String(64), unique=True, index=True, nullable=False)
    
    # Query metadata
    query_type = Column(String(50), nullable=False)  # "anomaly_explain", "copilot_qa", "report_summary", "strategy"
    model_used = Column(String(50), nullable=False)  # "llama-3.1-8b-instant" or "llama-3.3-70b-versatile"
    
    # Content
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    
    # Scope
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Cache management
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # TTL: 7 days default
    hit_count = Column(Integer, default=0)  # Track cache hits
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_cache_org_type', 'organization_id', 'query_type'),
        Index('idx_cache_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<CopilotCache {self.query_type} ({self.query_hash[:8]}...)>"
    
    @property
    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        return datetime.utcnow() < self.expires_at
    
    def record_hit(self) -> None:
        """Record a cache hit"""
        self.hit_count += 1
        self.last_accessed_at = datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        query_hash: str,
        query_type: str,
        model_used: str,
        prompt: str,
        response: str,
        organization_id,
        ttl_days: int = 7
    ):
        """Create a cache entry with TTL"""
        return cls(
            query_hash=query_hash,
            query_type=query_type,
            model_used=model_used,
            prompt=prompt,
            response=response,
            organization_id=organization_id,
            expires_at=datetime.utcnow() + timedelta(days=ttl_days)
        )
