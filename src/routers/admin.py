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

@router.post("/reject-transaction")
async def reject_transaction(
    request: ApproveTransactionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
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
        
    # Lock the sender's balance to refund it
    sender_balance = db.query(models.Balance).filter(
        models.Balance.account_id == debit_entry.account_id
    ).with_for_update().first()
    
    if not sender_balance:
        raise HTTPException(status_code=404, detail="Sender account not found")
        
    credit_entry.status = "REJECTED"
    debit_entry.status = "REJECTED"
    
    # Refund sender (debit_entry.amount is negative)
    sender_balance.available_balance += abs(debit_entry.amount)
    sender_balance.booked_balance += abs(debit_entry.amount)
    
    db.commit()
    
    from ..cache import invalidate_cache
    from .websockets import manager
    
    await invalidate_cache(f"balance_{debit_entry.account_id}")
    
    background_tasks.add_task(
        manager.broadcast_to_account,
        debit_entry.account_id,
        {"type": "PAYMENT_REJECTED", "transaction_id": request.transaction_id, "amount": abs(debit_entry.amount), "status": "REJECTED"}
    )
    
    return {"status": "success", "message": f"Transaction {request.transaction_id} rejected and funds refunded."}

@router.get("/fraud-queue")
async def get_fraud_queue(db: Session = Depends(get_db)):
    """
    Returns a list of all transactions that are currently flagged for review.
    Because double-entry means 2 rows per tx, we group them by transaction_id.
    """
    pending_entries = db.query(models.LedgerEntry).filter(
        models.LedgerEntry.status == "PENDING_REVIEW"
    ).all()
    
    transactions = {}
    for entry in pending_entries:
        if entry.entry_type == models.EntryType.DEBIT:
            transactions[entry.transaction_id] = {
                "transaction_id": entry.transaction_id,
                "account_id": entry.account_id,
                "amount": abs(entry.amount),
                "status": entry.status,
                "created_at": entry.created_at
            }
            
    return {"fraud_queue": list(transactions.values())}

@router.get("/verify-ledger/{account_id}")
async def verify_ledger(account_id: str, db: Session = Depends(get_db)):
    """
    Cryptographically verifies the immutable hash chain for a specific account.
    If an admin has tampered with any historical transaction, this will catch it.
    """
    entries = db.query(models.LedgerEntry).filter(
        models.LedgerEntry.account_id == account_id
    ).order_by(models.LedgerEntry.sequence_number.asc()).all()
    
    if not entries:
        return {"status": "success", "message": "No ledger entries found for this account.", "is_valid": True}
        
    from ..services.ledger_security import generate_ledger_hash
    
    expected_previous_hash = "0"
    expected_sequence_number = 1
    
    for entry in entries:
        # 0. Check for sequence gaps
        if entry.sequence_number != expected_sequence_number:
            raise HTTPException(
                status_code=500,
                detail=f"CRITICAL: Ledger tampered! Sequence gap detected. Expected sequence {expected_sequence_number}, got {entry.sequence_number}."
            )
            
        # 1. Verify the link to the previous block
        if entry.previous_hash != expected_previous_hash:
            raise HTTPException(
                status_code=500, 
                detail=f"CRITICAL: Ledger tampered! Chain broken at sequence {entry.sequence_number}. Expected previous_hash {expected_previous_hash}, got {entry.previous_hash}"
            )
            
        # 2. Verify the current block's integrity
        computed_hash = generate_ledger_hash(
            entry.previous_hash, entry.account_id, entry.amount, 
            entry.entry_type.value, entry.transaction_id
        )
        
        if entry.current_hash != computed_hash:
            raise HTTPException(
                status_code=500, 
                detail=f"CRITICAL: Ledger tampered! Invalid data at sequence {entry.sequence_number}. Computed hash {computed_hash} does not match stored hash {entry.current_hash}."
            )
            
        expected_previous_hash = entry.current_hash
        expected_sequence_number += 1
        
    return {
        "status": "success", 
        "message": f"Cryptographic ledger verified successfully. {len(entries)} blocks intact.", 
        "is_valid": True,
        "latest_hash": expected_previous_hash
    }
