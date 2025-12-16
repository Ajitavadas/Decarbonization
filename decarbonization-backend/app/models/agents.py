from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models.models import Base
import uuid
from datetime import datetime, timezone

class AgentState(Base):
    __tablename__ = "agent_states"

    thread_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    state = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    current_node = Column(String(255), nullable=True)

    # We can add a relationship to User if needed, but keeping it simple for now
    # to avoid circular imports if we were to modify User model.
    # user = relationship("User", back_populates="agent_states")
