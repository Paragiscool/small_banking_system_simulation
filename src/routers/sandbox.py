from fastapi import APIRouter, Form, HTTPException
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sandbox", tags=["Sandbox"])

@router.post("/authenticate")
def simulate_sca(username: str = Form(...), otp: str = Form(...)):
    # Simple simulated authentication for sandbox
    if username == "testuser" and otp == "000000":
        return {"status": "authenticated", "authorization_code": "mock-auth-code"}
    
    raise HTTPException(status_code=401, detail="Invalid Sandbox Credentials. Use testuser / 000000")

@router.post("/mock-webhook")
def receive_mock_webhook(payload: dict):
    # This acts as the receiving end on the TPP's server
    logger.info(f"[SANDBOX WEBHOOK RECEIVER] Received Webhook Payload: {payload}")
    return {"status": "received"}
