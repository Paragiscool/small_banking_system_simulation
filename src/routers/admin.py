from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .. import models
from ..database import get_db
import logging
import httpx

logger = logging.getLogger(__name__)

from ..dependencies import RoleChecker

router = APIRouter(
    prefix="/admin",
    tags=["Bank Admin Dashboard"],
    dependencies=[Depends(RoleChecker(["admin:approve"]))]
)

class ApproveTransactionRequest(BaseModel):
    transaction_id: str

def fire_webhook(webhook_url: str, transaction_id: str, status: str):
    if not webhook_url:
        return
    try:
        payload = {"transaction_id": transaction_id, "status": status}
        httpx.post(webhook_url, json=payload, timeout=5.0)
        logger.info(f"Webhook fired to {webhook_url} for tx {transaction_id}")
    except Exception as e:
        logger.error(f"Failed to fire webhook: {str(e)}")

@router.post("/approve-transaction")
async def approve_transaction(
    request: ApproveTransactionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Find the credit and debit entries for this transaction
    entries = db.query(models.LedgerEntry).filter(
        models.LedgerEntry.transaction_id == request.transaction_id
    ).all()
    
    if not entries or len(entries) != 2:
        raise HTTPException(status_code=404, detail="Transaction not found or incomplete")
        
    credit_entry = next((e for e in entries if e.entry_type == models.EntryType.CREDIT), None)
    debit_entry = next((e for e in entries if e.entry_type == models.EntryType.DEBIT), None)
    
    if not credit_entry or not debit_entry:
        raise HTTPException(status_code=400, detail="Invalid ledger state")
        
    if credit_entry.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail="Transaction is not pending review")
        
    # Lock the receiver's balance to update it
    receiver_balance = db.query(models.Balance).filter(
        models.Balance.account_id == credit_entry.account_id
    ).with_for_update().first()
    
    if not receiver_balance:
        raise HTTPException(status_code=404, detail="Receiver account not found")
        
    # Settle the transaction
    credit_entry.status = "SETTLED"
    debit_entry.status = "SETTLED"
    
    # Release funds to the receiver
    receiver_balance.available_balance += credit_entry.amount
    receiver_balance.booked_balance += credit_entry.amount
    
    db.commit()
    
    # Invalidate Cache
    from ..cache import invalidate_cache
    from .websockets import manager
    
    await invalidate_cache(f"balance_{credit_entry.account_id}")
    
    # Fire Webhook and WebSocket to notify that the transaction is finally approved!
    mock_webhook_url = "http://127.0.0.1:8000/sandbox/mock-webhook"
    background_tasks.add_task(fire_webhook, mock_webhook_url, request.transaction_id, "SETTLED")
    
    background_tasks.add_task(
        manager.broadcast_to_account,
        credit_entry.account_id,
        {"type": "PAYMENT_RECEIVED", "transaction_id": request.transaction_id, "amount": credit_entry.amount, "status": "SETTLED"}
    )
    
    return {"status": "success", "message": f"Transaction {request.transaction_id} approved and funds settled."}
