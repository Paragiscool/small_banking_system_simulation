import os
import json
import redis.asyncio as redis
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def get_cache(key: str) -> Optional[Any]:
    """
    Retrieve an item from the cache.
    Returns None if the key doesn't exist or has expired.
    """
    val = await redis_client.get(key)
    if val:
        return json.loads(val)
    return None

async def set_cache(key: str, value: Any, ttl_seconds: Optional[int] = 300) -> None:
    """
    Store an item in the cache with an optional Time-To-Live (TTL) in seconds.
    Default TTL is 5 minutes (300 seconds).
    """
    await redis_client.set(key, json.dumps(jsonable_encoder(value)), ex=ttl_seconds)

async def invalidate_cache(key: str) -> None:
    """
    Instantly destroy a cached item. This is the hardest problem in Computer Science!
    """
    await redis_client.delete(key)

async def clear_all_cache() -> None:
    """
    Wipe the entire cache. Useful for testing.
    """
    await redis_client.flushdb()
