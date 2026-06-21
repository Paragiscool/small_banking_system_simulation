from fastapi import Request, HTTPException
import time
import os
import redis.asyncio as redis

# Define limits
LIMITS = {
    "accounts": 300, # 300 per minute
    "payments": 60   # 60 per minute
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def rate_limiter(category: str):
    """
    Dependency to enforce rate limiting based on a Fixed Window (1 minute).
    """
    async def _rate_limit_dependency(request: Request):
        client_identifier = request.client.host
        
        current_time = int(time.time())
        window_start = current_time - (current_time % 60) # Start of current minute
        
        limit = LIMITS.get(category, 60)
        key = f"ratelimit:{category}:{client_identifier}:{window_start}"
        
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, 60, nx=True) # Only set expiration if key has no TTL (Redis 7+ feature)
            results = await pipe.execute()
            
        count = results[0]
        remaining = max(0, limit - count)
        
        if count > limit:
            raise HTTPException(
                status_code=429,
                detail="Too Many Requests",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window_start + 60),
                    "Retry-After": str(window_start + 60 - current_time)
                }
            )
            
        # Add headers to request state to be injected into response later
        request.state.ratelimit_limit = limit
        request.state.ratelimit_remaining = remaining
        request.state.ratelimit_reset = window_start + 60
        
        return True
    
    return _rate_limit_dependency
