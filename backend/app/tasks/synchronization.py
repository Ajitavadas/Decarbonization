"""
Synchronization tasks
Keep local data synced with Climatiq
"""

from app.core.celery_app import celery_app
from app.services.cache_manager import cache_manager


@celery_app.task(name="app.tasks.synchronization.sync_emission_factors")
async def sync_emission_factors():
    """
    Sync emission factors from Climatiq
    
    Scheduled to run nightly at 2 AM
    Invalidates cache to ensure fresh data
    """
    try:
        # Invalidate emission factor cache
        invalidated = await cache_manager.invalidate("climatiq:factor:*")
        
        return {
            "status": "completed",
            "cache_keys_invalidated": invalidated,
            "message": "Emission factors cache refreshed"
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}
