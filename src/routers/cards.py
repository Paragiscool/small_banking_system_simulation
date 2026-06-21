from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import random

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/cards",
    tags=["Virtual Cards"]
)

def generate_virtual_card_details():
    # Generate 16 digit card number
    card_number = "4" + "".join([str(random.randint(0, 9)) for _ in range(15)])
    # Generate 3 digit CVV
    cvv = "".join([str(random.randint(0, 9)) for _ in range(3)])
    # Generate Expiry Date 3 years from now
    from datetime import datetime, timedelta
    expiry_date = (datetime.now() + timedelta(days=365*3)).strftime("%m/%y")
    return card_number, cvv, expiry_date

@router.post("/", response_model=schemas.VirtualCardResponse, status_code=status.HTTP_201_CREATED)
def issue_virtual_card(card_request: schemas.VirtualCardCreate, db: Session = Depends(get_db)):
    """
    Issue a new virtual debit card for a given account.
    """
    # Verify account exists
    account = db.query(models.Account).filter(models.Account.account_id == card_request.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    card_number, cvv, expiry_date = generate_virtual_card_details()
    
    new_card = models.VirtualCard(
        account_id=card_request.account_id,
        card_number=card_number,
        cvv=cvv,
        expiry_date=expiry_date,
        daily_limit=card_request.daily_limit
    )
    
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    
    return schemas.VirtualCardResponse(
        card_id=new_card.card_id,
        account_id=new_card.account_id,
        card_number=new_card.card_number,
        cvv=new_card.cvv,
        expiry_date=new_card.expiry_date,
        status=new_card.status.name,
        daily_limit=new_card.daily_limit
    )

@router.put("/{card_id}/status", response_model=schemas.VirtualCardResponse)
def update_card_status(card_id: str, status_update: schemas.VirtualCardStatusUpdate, db: Session = Depends(get_db)):
    """
    Freeze or unfreeze a virtual card.
    """
    card = db.query(models.VirtualCard).filter(models.VirtualCard.card_id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
        
    try:
        new_status = models.VirtualCardStatus(status_update.status.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status. Must be ACTIVE, FROZEN, or CANCELED.")
        
    card.status = new_status
    db.commit()
    db.refresh(card)
    
    return schemas.VirtualCardResponse(
        card_id=card.card_id,
        account_id=card.account_id,
        card_number=card.card_number,
        cvv=card.cvv,
        expiry_date=card.expiry_date,
        status=card.status.name,
        daily_limit=card.daily_limit
    )

@router.post("/{card_id}/charge")
def simulate_merchant_charge(card_id: str, charge: schemas.ChargeRequest, db: Session = Depends(get_db)):
    """
    Simulate a merchant charging the virtual card.
    """
    card = db.query(models.VirtualCard).filter(models.VirtualCard.card_id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
        
    if card.status != models.VirtualCardStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Transaction declined: Card is {card.status.name}")
        
    if charge.amount > card.daily_limit:
        raise HTTPException(status_code=400, detail="Transaction declined: Exceeds daily limit")
        
    # Debit the account
    balance = db.query(models.Balance).filter(models.Balance.account_id == card.account_id).with_for_update().first()
    if not balance:
        raise HTTPException(status_code=404, detail="Linked account balance not found")
        
    if balance.available_balance < charge.amount:
        raise HTTPException(status_code=400, detail="Transaction declined: Insufficient funds")
        
    # Process the charge
    balance.available_balance -= charge.amount
    balance.booked_balance -= charge.amount
    
    tx_id = f"CARD-{str(uuid.uuid4())[:8]}"
    entry = models.LedgerEntry(
        transaction_id=tx_id,
        account_id=card.account_id,
        amount=charge.amount,
        entry_type=models.EntryType.DEBIT,
        status="BOOKED"
    )
    db.add(entry)
    db.commit()
    
    return {
        "status": "APPROVED",
        "merchant": charge.merchant_name,
        "amount": charge.amount,
        "transaction_id": tx_id
    }
