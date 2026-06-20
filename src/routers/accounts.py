from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user, verify_mtls, sandbox_error_injection
from ..governance import rate_limiter

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    dependencies=[Depends(sandbox_error_injection), Depends(rate_limiter("accounts")), Depends(verify_mtls), Depends(get_current_user)]
)

@router.get("", response_model=List[schemas.AccountResponse])
def get_accounts(db: Session = Depends(get_db)):
    accounts = db.query(models.Account).all()
    return accounts

@router.get("/{account_id}/balances", response_model=schemas.BalanceResponse)
def get_account_balances(account_id: str, db: Session = Depends(get_db)):
    balance = db.query(models.Balance).filter(models.Balance.account_id == account_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="Account balance not found")
    return balance
