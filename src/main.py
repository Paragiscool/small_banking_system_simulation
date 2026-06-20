from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, accounts, payments, sandbox, portal, consent, analytics
from . import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Open Banking API Gateway (Sandbox)",
    description="A prototype Core Banking System with FAPI and Double-Entry Ledger",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
import logging
from fastapi import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_monitor")

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    process_time_ms = round(process_time * 1000, 2)
    
    # Log the monitoring data
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Latency: {process_time_ms}ms"
    )
    
    # Inject standard headers
    response.headers["X-Response-Time"] = f"{process_time_ms}ms"
    
    # Inject rate limit headers if they were set by the rate limiter dependency
    if hasattr(request.state, "ratelimit_limit"):
        response.headers["X-RateLimit-Limit"] = str(request.state.ratelimit_limit)
        response.headers["X-RateLimit-Remaining"] = str(request.state.ratelimit_remaining)
        response.headers["X-RateLimit-Reset"] = str(request.state.ratelimit_reset)
        
    return response

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(payments.router)
app.include_router(sandbox.router)
app.include_router(portal.router)
app.include_router(consent.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Open Banking API Gateway Prototype. Visit /docs for Swagger UI."}
