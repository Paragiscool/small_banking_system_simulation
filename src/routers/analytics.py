from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    # 1. Total Payments Processed
    total_debits = db.query(func.sum(models.LedgerEntry.amount)).filter(
        models.LedgerEntry.entry_type == models.EntryType.CREDIT # Use CREDIT side to get positive sum of all payments
    ).scalar() or 0.0
    
    # 2. Total Active Consents
    active_consents = db.query(models.Consent).filter(
        models.Consent.status == models.ConsentStatus.AUTHORISED
    ).count()
    
    # 3. Total API Traffic (Proxy using Idempotency Keys)
    total_api_calls = db.query(models.IdempotencyKey).count()
    
    # 4. Recent Transactions
    recent_txs = db.query(models.LedgerEntry).filter(
        models.LedgerEntry.entry_type == models.EntryType.CREDIT
    ).order_by(models.LedgerEntry.created_at.desc()).limit(5).all()
    
    recent_transactions_list = [
        {
            "transaction_id": tx.transaction_id,
            "account_id": tx.account_id,
            "amount": f"${tx.amount:,.2f}",
            "date": tx.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for tx in recent_txs
    ]
    
    return {
        "metrics": {
            "total_volume_processed": total_debits,
            "active_user_consents": active_consents,
            "total_api_calls": total_api_calls
        },
        "recent_transactions": recent_transactions_list
    }
