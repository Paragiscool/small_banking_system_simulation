from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict
import uuid
import secrets
from ..database import get_db
from ..models import ThirdPartyProvider

router = APIRouter(prefix="/portal", tags=["Developer Portal"])

from typing import Dict, Optional

# ...

class RegisterTPPRequest(BaseModel):
    app_name: str
    redirect_uri: str
    webhook_url: Optional[str] = None

class RegisterTPPResponse(BaseModel):
    client_id: str
    client_secret: str
    message: str

@router.post("/register", response_model=RegisterTPPResponse)
def register_tpp(request: RegisterTPPRequest, db: Session = Depends(get_db)):
    # Generate unique credentials
    client_id = f"tpp_{uuid.uuid4().hex[:12]}"
    client_secret = secrets.token_urlsafe(32)
    
    new_tpp = ThirdPartyProvider(
        client_id=client_id,
        name=request.app_name,
        redirect_uris=request.redirect_uri,
        mtls_cert_fingerprint="mock-fingerprint",
        signing_cert_public_key="mock-public-key",
        webhook_url=request.webhook_url
    )
    
    db.add(new_tpp)
    db.commit()
    
    return RegisterTPPResponse(
        client_id=client_id,
        client_secret=client_secret,
        message="Registration successful. Keep your client_secret safe!"
    )
