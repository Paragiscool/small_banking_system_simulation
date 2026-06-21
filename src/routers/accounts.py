from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user, verify_mtls, sandbox_error_injection, RoleChecker
from ..governance import rate_limiter

from ..cache import get_cache, set_cache

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    dependencies=[Depends(sandbox_error_injection), Depends(rate_limiter("accounts")), Depends(verify_mtls), Depends(RoleChecker(["read:balance"]))]
)

@router.get("", response_model=List[schemas.AccountResponse])
async def get_accounts(db: Session = Depends(get_db)):
    cached_accounts = await get_cache("all_accounts")
    if cached_accounts:
        return cached_accounts
        
    accounts = db.query(models.Account).all()
    await set_cache("all_accounts", accounts, ttl_seconds=300)
    return accounts

@router.get("/{account_id}/balances", response_model=schemas.BalanceResponse)
async def get_account_balances(account_id: str, db: Session = Depends(get_db)):
    cache_key = f"balance_{account_id}"
    cached_balance = await get_cache(cache_key)
    if cached_balance:
        return cached_balance
        
    balance = db.query(models.Balance).filter(models.Balance.account_id == account_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="Account balance not found")
        
    await set_cache(cache_key, balance, ttl_seconds=60)
    return balance

import csv
import io
from fastapi.responses import StreamingResponse

@router.get("/{account_id}/statement")
def get_account_statement(account_id: str, db: Session = Depends(get_db)):
    """
    Generate an immutable CSV statement of all ledger entries for this account.
    """
    entries = db.query(models.LedgerEntry).filter(
        models.LedgerEntry.account_id == account_id
    ).order_by(models.LedgerEntry.created_at.desc()).all()
    
    if not entries:
        raise HTTPException(status_code=404, detail="No transactions found for this account")
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Transaction ID", "Date", "Type", "Amount", "Status"])
    
    # Write rows
    for entry in entries:
        writer.writerow([
            entry.transaction_id,
            entry.created_at.isoformat(),
            entry.entry_type.name,
            f"{entry.amount:.2f}",
            entry.status
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=statement_{account_id}.csv"}
    )
