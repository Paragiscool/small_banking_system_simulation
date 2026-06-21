from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user, verify_mtls, sandbox_error_injection, RoleChecker
from ..governance import rate_limiter
import uuid
import json
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    dependencies=[Depends(sandbox_error_injection), Depends(rate_limiter("payments")), Depends(verify_mtls), Depends(RoleChecker(["write:payments"]))]
)

def fire_webhook(webhook_url: str, transaction_id: str, status: str):
    if not webhook_url:
        return
    try:
        # In a real system, we'd use a robust task queue like Celery. 
        # BackgroundTasks is perfect for this simulation.
        payload = {"transaction_id": transaction_id, "status": status}
        # Fire and forget POST request
        httpx.post(webhook_url, json=payload, timeout=5.0)
        logger.info(f"Webhook fired to {webhook_url} for tx {transaction_id}")
    except Exception as e:
        logger.error(f"Failed to fire webhook: {str(e)}")

# ...

@router.post("/domestic-payments", response_model=schemas.PaymentResponse)
async def domestic_payment(
    request: schemas.PaymentRequest,
    background_tasks: BackgroundTasks,
    x_idempotency_key: str = Header(...),
    db: Session = Depends(get_db)
):
    # 1. Check Idempotency Key
    idemp_record = db.query(models.IdempotencyKey).filter(
        models.IdempotencyKey.idempotency_key == x_idempotency_key
    ).first()
    
    if idemp_record:
        if idemp_record.response_body:
            response_data = json.loads(idemp_record.response_body)
            return schemas.PaymentResponse(**response_data)
        else:
            raise HTTPException(status_code=409, detail="Payment already in progress")
            
    # Save the key as in-progress
    new_idemp = models.IdempotencyKey(
        idempotency_key=x_idempotency_key,
        client_id="mock-client",
        request_path="/payments/domestic-payments"
    )
    db.add(new_idemp)
    db.commit()

    try:
        # 2. Row-Level Locking & FX Conversion
        sender_account = db.query(models.Account).filter(models.Account.account_id == request.sender_account_id).first()
        receiver_account = db.query(models.Account).filter(models.Account.account_id == request.receiver_account_id).first()
        
        if not sender_account or not receiver_account:
            raise HTTPException(status_code=404, detail="Account not found")
            
        # Ensure consistent lock order to prevent deadlocks in PostgreSQL
        accounts_to_lock = sorted([request.sender_account_id, request.receiver_account_id])
        
        balances = {}
        for acc_id in accounts_to_lock:
            bal = db.query(models.Balance).filter(
                models.Balance.account_id == acc_id
            ).with_for_update().first()
            if not bal:
                raise HTTPException(status_code=404, detail=f"Balance not found for account {acc_id}")
            balances[acc_id] = bal
            
        sender_balance = balances[request.sender_account_id]
        receiver_balance = balances[request.receiver_account_id]
        
        if sender_balance.available_balance < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient Funds")
            
        # FX Conversion Logic
        sender_currency = sender_account.currency
        receiver_currency = receiver_account.currency
        receiver_amount = request.amount
        
        if sender_currency != receiver_currency:
            exchange_rate = db.query(models.ExchangeRate).filter(
                models.ExchangeRate.from_currency == sender_currency,
                models.ExchangeRate.to_currency == receiver_currency
            ).first()
            if not exchange_rate:
                raise HTTPException(status_code=400, detail=f"No exchange rate found for {sender_currency} to {receiver_currency}")
            receiver_amount = round(request.amount * exchange_rate.rate, 2)
            
        # 3. Fraud Engine & Double-Entry Update
        transaction_id = str(uuid.uuid4())
        
        is_fraud_flagged = request.amount > 10000.0
        tx_status = "PENDING_REVIEW" if is_fraud_flagged else "SETTLED"
        
        debit_entry = models.LedgerEntry(
            transaction_id=transaction_id,
            account_id=request.sender_account_id,
            amount=-request.amount,
            entry_type=models.EntryType.DEBIT,
            status=tx_status
        )
        credit_entry = models.LedgerEntry(
            transaction_id=transaction_id,
            account_id=request.receiver_account_id,
            amount=receiver_amount,
            entry_type=models.EntryType.CREDIT,
            status=tx_status
        )
        db.add(debit_entry)
        db.add(credit_entry)
        
        # Always deduct from sender, but only add to receiver if NOT flagged for fraud
        sender_balance.available_balance -= request.amount
        sender_balance.booked_balance -= request.amount
        
        if not is_fraud_flagged:
            receiver_balance.available_balance += receiver_amount
            receiver_balance.booked_balance += receiver_amount
        
        db.commit()
        
        # Invalidate Cache
        from ..cache import invalidate_cache
        from .websockets import manager
        
        await invalidate_cache(f"balance_{request.sender_account_id}")
        await invalidate_cache(f"balance_{request.receiver_account_id}")
        
        # 4. Trigger Asynchronous Webhook & WebSockets
        mock_webhook_url = "http://127.0.0.1:8000/sandbox/mock-webhook"
        background_tasks.add_task(fire_webhook, mock_webhook_url, transaction_id, tx_status)
        
        background_tasks.add_task(
            manager.broadcast_to_account,
            request.sender_account_id,
            {"type": "PAYMENT_SENT", "transaction_id": transaction_id, "amount": request.amount, "status": tx_status}
        )
        if not is_fraud_flagged:
            background_tasks.add_task(
                manager.broadcast_to_account,
                request.receiver_account_id,
                {"type": "PAYMENT_RECEIVED", "transaction_id": transaction_id, "amount": receiver_amount, "status": tx_status}
            )
        
        # 5. Save response to Idempotency Key
        response_status_str = "AcceptedPendingReview" if is_fraud_flagged else "AcceptedSettlementCompleted"
        response_data = {"status": response_status_str, "transaction_id": transaction_id}
        
        idemp_record = db.query(models.IdempotencyKey).filter(
            models.IdempotencyKey.idempotency_key == x_idempotency_key
        ).first()
        idemp_record.response_body = json.dumps(response_data)
        idemp_record.response_status = 200
        db.commit()
        
        return response_data
        
    except Exception as e:
        db.rollback()
        # Clean up idempotency key on failure so it can be retried
        db.query(models.IdempotencyKey).filter(
            models.IdempotencyKey.idempotency_key == x_idempotency_key
        ).delete()
        db.commit()
        raise e
