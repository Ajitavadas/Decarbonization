import redis.asyncio as redis
from functools import wraps

cache = redis.from_url("redis://redis:6379")

def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Try cache
            cached_value = await cache.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
            
            # Compute and cache
            result = await func(*args, **kwargs)
            await cache.setex(cache_key, ttl, json.dumps(result))
            return result
        
        return wrapper
    return decorator