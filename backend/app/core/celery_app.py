"""
Celery application configuration for async task processing
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "decarbonization_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.batch_processing",
        "app.tasks.reporting",
        "app.tasks.synchronization"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.BATCH_TIMEOUT_SECONDS,
    task_soft_time_limit=settings.BATCH_TIMEOUT_SECONDS - 30,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    "sync-emission-factors-nightly": {
        "task": "app.tasks.synchronization.sync_emission_factors",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "generate-monthly-reports": {
        "task": "app.tasks.reporting.generate_monthly_reports",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),  # 1st of month
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f"Request: {self.request!r}")
