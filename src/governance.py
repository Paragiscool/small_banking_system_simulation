from fastapi import Request, HTTPException
import time
from collections import defaultdict

# In-memory store: { "client_id_or_ip": { "endpoint_category": {"timestamp": int, "count": int} } }
RATE_LIMITS_STORE = defaultdict(lambda: defaultdict(lambda: {"timestamp": 0, "count": 0}))

# Define limits
LIMITS = {
    "accounts": 300, # 300 per minute
    "payments": 60   # 60 per minute
}

def rate_limiter(category: str):
    """
    Dependency to enforce rate limiting based on a Fixed Window (1 minute).
    """
    def _rate_limit_dependency(request: Request):
        # We'll use the client IP for the sandbox, or a mock client_id
        client_identifier = request.client.host
        
        current_time = int(time.time())
        window_start = current_time - (current_time % 60) # Start of current minute
        
        record = RATE_LIMITS_STORE[client_identifier][category]
        
        # If the window has passed, reset
        if record["timestamp"] < window_start:
            record["timestamp"] = window_start
            record["count"] = 0
            
        record["count"] += 1
        
        limit = LIMITS.get(category, 60)
        remaining = max(0, limit - record["count"])
        
        if record["count"] > limit:
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
            
        # Add headers to request state to be injected into response later (FastAPI specific logic usually requires middleware for outbound headers, but this shows intent)
        request.state.ratelimit_limit = limit
        request.state.ratelimit_remaining = remaining
        request.state.ratelimit_reset = window_start + 60
        
        return True
    
    return _rate_limit_dependency
