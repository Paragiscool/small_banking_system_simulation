from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user, verify_mtls, sandbox_error_injection
from ..governance import rate_limiter
import uuid
import json

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    dependencies=[Depends(sandbox_error_injection), Depends(rate_limiter("payments")), Depends(verify_mtls), Depends(get_current_user)]
)

@router.post("/domestic-payments", response_model=schemas.PaymentResponse)
def domestic_payment(
    request: schemas.PaymentRequest,
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
        # 2. Row-Level Locking (Pessimistic)
        # Assuming SQLite doesn't truly support FOR UPDATE in the same way Postgres does without specific PRAGMAs,
        # but we use the SQLAlchemy syntax for conceptual completeness (works well in Postgres/MySQL).
        
        sender_balance = db.query(models.Balance).filter(
            models.Balance.account_id == request.sender_account_id
        ).with_for_update().first()
        
        if not sender_balance:
            raise HTTPException(status_code=404, detail="Sender account not found")
            
        if sender_balance.available_balance < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient Funds")
            
        receiver_balance = db.query(models.Balance).filter(
            models.Balance.account_id == request.receiver_account_id
        ).with_for_update().first()
        
        if not receiver_balance:
            raise HTTPException(status_code=404, detail="Receiver account not found")
            
        # 3. Double-Entry Update
        transaction_id = str(uuid.uuid4())
        
        debit_entry = models.LedgerEntry(
            transaction_id=transaction_id,
            account_id=request.sender_account_id,
            amount=-request.amount,
            entry_type=models.EntryType.DEBIT
        )
        credit_entry = models.LedgerEntry(
            transaction_id=transaction_id,
            account_id=request.receiver_account_id,
            amount=request.amount,
            entry_type=models.EntryType.CREDIT
        )
        db.add(debit_entry)
        db.add(credit_entry)
        
        sender_balance.available_balance -= request.amount
        receiver_balance.available_balance += request.amount
        
        db.commit()
        
        # 4. Save response to Idempotency Key
        response_data = {"status": "AcceptedSettlementCompleted", "transaction_id": transaction_id}
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
