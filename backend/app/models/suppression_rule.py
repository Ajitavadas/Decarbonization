"""
Suppression Rule Model - Rules to temporarily suppress certain audit findings
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Boolean, Text
from app.db.types import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class SuppressionRule(Base):
    """
    Rules to suppress specific audit findings.
    
    Suppression Rules allow organizations to temporarily suppress
    certain types of findings that have been reviewed and determined
    to be acceptable or not actionable.
    """
    
    __tablename__ = "suppression_rules"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Rule matching
    rule_id = Column(String(100), nullable=False)  # Matches finding.rule_id
    condition = Column(JSONB, nullable=True)  # Optional additional conditions
    scope = Column(String(50), nullable=True)  # Optional scope restriction
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=True)
    
    # Rule parameters
    confidence_weight = Column(Numeric(5, 2), default=1.0)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    requires_revalidation = Column(Boolean, default=False)
    
    # Audit
    created_by = Column(UUID, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_revalidated = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", backref="suppression_rules")
    project = relationship("Project", backref="suppression_rules")
    creator = relationship("User", backref="suppression_rules")
    
    def matches(self, finding: Dict[str, Any]) -> bool:
        """
        Check if this suppression rule matches a finding.
        
        Args:
            finding: Finding dict from detector
            
        Returns:
            True if finding should be suppressed
        """
        # Basic rule_id match
        if finding.get("rule_id") != self.rule_id:
            return False
        
        # Check scope if specified
        if self.scope:
            evidence = finding.get("evidence", {})
            finding_scope = evidence.get("scope") or finding.get("scope")
            if finding_scope and finding_scope != self.scope:
                return False
        
        # Check additional conditions
        if self.condition:
            evidence = finding.get("evidence", {})
            for key, expected_value in self.condition.items():
                if evidence.get(key) != expected_value:
                    return False
        
        return True
    
    def __repr__(self):
        return f"<SuppressionRule {self.rule_id} org={self.organization_id}>"
