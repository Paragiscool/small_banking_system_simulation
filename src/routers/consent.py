from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import secrets
from ..database import get_db
from .. import models
from pydantic import BaseModel

router = APIRouter(prefix="/consent", tags=["Consent Management"])

class ConsentRequest(BaseModel):
    client_id: str
    user_id: str
    permissions: str

class ConsentResponse(BaseModel):
    authorization_code: str
    redirect_uri: str
    message: str

@router.post("/authorize", response_model=ConsentResponse)
def authorize_tpp(
    request: ConsentRequest,
    db: Session = Depends(get_db)
):
    # 1. Verify TPP exists
    tpp = db.query(models.ThirdPartyProvider).filter(models.ThirdPartyProvider.client_id == request.client_id).first()
    if not tpp:
        raise HTTPException(status_code=404, detail="Third Party Provider not found")

    # 2. Create Consent Record
    new_consent = models.Consent(
        client_id=request.client_id,
        user_id=request.user_id,
        permissions=request.permissions,
        status=models.ConsentStatus.AUTHORISED,
        expiration_date=datetime.utcnow() + timedelta(days=90)
    )
    db.add(new_consent)
    db.flush() # Get the consent_id

    # 3. Generate Authorization Code
    auth_code = secrets.token_urlsafe(32)
    new_auth_code = models.AuthorizationCode(
        code=auth_code,
        client_id=request.client_id,
        consent_id=new_consent.consent_id,
        user_id=request.user_id,
        code_challenge="mock-challenge", # Simplified for demo
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(new_auth_code)
    db.commit()

    return ConsentResponse(
        authorization_code=auth_code,
        redirect_uri=tpp.redirect_uri if hasattr(tpp, "redirect_uri") else "http://localhost:3000/callback",
        message="Consent granted successfully."
    )
