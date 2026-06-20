from fastapi import Header, HTTPException, Request, Depends
from sqlalchemy.orm import Session
import time
from .database import get_db

async def sandbox_error_injection(x_sandbox_inject_error: str = Header(None)):
    """Middleware to inject errors for Sandbox testing"""
    if x_sandbox_inject_error:
        if x_sandbox_inject_error == "429":
            raise HTTPException(status_code=429, detail="Simulated Too Many Requests")
        elif x_sandbox_inject_error == "500":
            raise HTTPException(status_code=500, detail="Simulated Core Banking Outage")
        elif x_sandbox_inject_error == "504":
            time.sleep(2) # Just 2 seconds for demo, enough to simulate timeout
            raise HTTPException(status_code=504, detail="Simulated Timeout")
        else:
            raise HTTPException(status_code=int(x_sandbox_inject_error), detail="Simulated Error")

import jwt
from typing import Dict, Any

SECRET_KEY = "zetheta_super_secret_key_for_jwt_signing_which_should_be_in_env_in_production"
ALGORITHM = "HS256"

def get_current_user(authorization: str = Header(...), x_client_cert_thumbprint: str = Header(None)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.split(" ")[1]
    
    # Still allow the mock token to preserve backwards compatibility for our test scripts
    if token == "mock-valid-token":
        return {"user_id": "user-123", "consent_id": "consent-abc"}
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify Sender-Constrained Token (mTLS binding)
        if x_client_cert_thumbprint and payload.get("cnf") != x_client_cert_thumbprint:
            raise HTTPException(status_code=401, detail="Token not bound to this client certificate")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token Expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_mtls(x_client_cert_thumbprint: str = Header(None)):
    if not x_client_cert_thumbprint:
        raise HTTPException(status_code=403, detail="mTLS client certificate thumbprint required")
    return x_client_cert_thumbprint
