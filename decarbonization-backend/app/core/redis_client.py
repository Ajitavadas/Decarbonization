import redis.asyncio as redis
from app.config import settings
from typing import Optional

# Global redis client
redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

async def get_redis_client():
    return redis_client

class RedisLock:
    """
    Simple ephemeral lock using Redis.
    Usage:
        async with RedisLock("my_resource_id", timeout=30):
            # do work
    """
    def __init__(self, key: str, timeout: int = 30):
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.redis = redis_client
        self.acquired = False

    async def __aenter__(self):
        # NX = Set if Not Exists
        # EX = Expire time in seconds
        self.acquired = await self.redis.set(self.key, "1", ex=self.timeout, nx=True)
        if not self.acquired:
             raise Exception(f"Could not acquire lock for {self.key}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            # Only delete if we were the ones who acquired it
            # (Though currently we don't check value, simple set/delete)
            await self.redis.delete(self.key)
