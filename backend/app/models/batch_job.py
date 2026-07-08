"""
Batch Job model for tracking async batch processing
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from app.db.types import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class BatchJob(Base):
    """
    Track status of asynchronous batch processing jobs
    """
    
    __tablename__ = "batch_jobs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Job metadata
    job_type = Column(String(50), nullable=False)  # batch_estimate, batch_import, report_generation
    status = Column(String(20), nullable=False, default="queued", index=True)  # queued, processing, completed, failed
    
    # File information
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    
    # Progress tracking
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    # Error tracking
    error_log = Column(JSONB, default=[])  # [{"row": 5, "error": "Invalid region"}]
    error_message = Column(String(1000), nullable=True)
    
    # Results (optional)
    results = Column(JSONB, nullable=True)
    
    # Celery task tracking
    celery_task_id = Column(String(255), nullable=True, unique=True, index=True)
    
    # Relationships
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=True)
    project = relationship("Project")
    
    activities = relationship("EmissionActivity", back_populates="batch_job")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<BatchJob {self.job_type} - {self.status}>"
    
    @property
    def progress_percentage(self) -> float:
        """Calculate job progress percentage"""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
