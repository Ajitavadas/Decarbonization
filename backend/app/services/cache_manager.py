"""
Redis cache manager for emission factors and API responses
"""

import json
import hashlib
from typing import Optional, Any, Dict
import redis.asyncio as redis

from app.core.config import settings


class CacheManager:
    """
    Redis-based caching for Climatiq API responses
    
    Benefits:
    - Reduces external API calls
    - Lowers costs
    - Improves response time
    - 24-hour TTL for emission factors (they don't change frequently)
    """
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.ttl = settings.EMISSION_FACTOR_CACHE_TTL
        self._redis: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if self._redis is None:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis
    
    def _generate_cache_key(
        self,
        activity_id: str,
        region: Optional[str] = None,
        year: Optional[int] = None,
        version: str = "^28",
        **kwargs
    ) -> str:
        """
        Generate deterministic cache key from parameters
        
        Pattern: climatiq:factor:{activity_id}:{region}:{year}:{version}:{params_hash}
        """
        # Create deterministic params hash
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        
        key_parts = [
            "climatiq",
            "factor",
            activity_id,
            region or "global",
            str(year) if year else "latest",
            version,
            params_hash
        ]
        
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached value
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            r = await self.get_redis()
            value = await r.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            # Cache failures should not break the application
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached value with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)
            
        Returns:
            Success boolean
        """
        try:
            r = await self.get_redis()
            ttl = ttl or self.ttl
            
            await r.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
            
        except Exception as e:
            # Cache failures should not break the application
            print(f"Cache set error: {e}")
            return False
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cache-aside pattern: check cache, fetch if miss, store result
        
        Args:
            key: Cache key
            fetch_func: Async function to call on cache miss
            *args, **kwargs: Arguments to pass to fetch_func
            
        Returns:
            Cached or fetched value
        """
        # Check cache first
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Cache miss - fetch from source
        result = await fetch_func(*args, **kwargs)
        
        # Store in cache for future requests
        await self.set(key, result)
        
        return result
    
    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "climatiq:factor:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            r = await self.get_redis()
            keys = await r.keys(pattern)
            
            if keys:
                return await r.delete(*keys)
            return 0
            
        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()


# Global cache instance
cache_manager = CacheManager()
