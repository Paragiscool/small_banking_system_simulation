from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
import uuid

router = APIRouter(prefix="/oauth", tags=["Auth"])

@router.post("/par", response_model=schemas.ParResponse)
def pushed_authorization_request(
    request_object: str = Form(...),
    db: Session = Depends(get_db)
):
    # Mocking the verification of JAR (JWT Secured Authorization Request)
    request_uri = f"urn:bank:req:{uuid.uuid4()}"
    return schemas.ParResponse(request_uri=request_uri, expires_in=90)

@router.post("/token", response_model=schemas.TokenResponse)
def token_exchange(
    code: str = Form(...),
    code_verifier: str = Form(...),
    client_id: str = Form(...),
    db: Session = Depends(get_db)
):
    # In a real scenario, we verify PKCE and the authorization code here.
    if code == "invalid-code":
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    # Generate mock token bound to certificate
    return schemas.TokenResponse(
        access_token="mock-valid-token",
        token_type="Bearer",
        expires_in=3600
    )
