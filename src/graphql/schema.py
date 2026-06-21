import strawberry
from strawberry.types import Info
from typing import List, Optional
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..dependencies import get_current_user

def get_user_from_request(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated. Set Authorization header in GraphiQL.")
    return get_current_user(authorization=auth_header, x_client_cert_thumbprint=None)

@strawberry.type
class BalanceType:
    account_id: str
    available_balance: float
    booked_balance: float

@strawberry.type
class LedgerEntryType:
    entry_id: str
    transaction_id: str
    account_id: str
    amount: float
    entry_type: str
    status: str
    created_at: str

@strawberry.type
class AccountType:
    account_id: str
    user_id: str
    internal_account_number: str
    status: str
    currency: str
    
    @strawberry.field
    def balance(self, info: Info) -> Optional[BalanceType]:
        db: Session = info.context["db"]
        db_balance = db.query(models.Balance).filter(models.Balance.account_id == self.account_id).first()
        if db_balance:
            return BalanceType(
                account_id=db_balance.account_id,
                available_balance=db_balance.available_balance,
                booked_balance=db_balance.booked_balance
            )
        return None

    @strawberry.field
    def ledger_entries(self, info: Info) -> List[LedgerEntryType]:
        db: Session = info.context["db"]
        db_entries = db.query(models.LedgerEntry).filter(models.LedgerEntry.account_id == self.account_id).all()
        return [
            LedgerEntryType(
                entry_id=entry.entry_id,
                transaction_id=entry.transaction_id,
                account_id=entry.account_id,
                amount=entry.amount,
                entry_type=entry.entry_type.name,
                status=entry.status,
                created_at=entry.created_at.isoformat() if entry.created_at else ""
            ) for entry in db_entries
        ]

@strawberry.type
class Query:
    @strawberry.field
    def account(self, account_id: str, info: Info) -> Optional[AccountType]:
        db: Session = info.context["db"]
        request: Request = info.context["request"]
        user = get_user_from_request(request)
        
        db_account = db.query(models.Account).filter(models.Account.account_id == account_id, models.Account.user_id == user["sub"]).first()
        if db_account:
            return AccountType(
                account_id=db_account.account_id,
                user_id=db_account.user_id,
                internal_account_number=db_account.internal_account_number,
                status=db_account.status.name,
                currency=db_account.currency
            )
        return None

    @strawberry.field
    def accounts(self, info: Info) -> List[AccountType]:
        db: Session = info.context["db"]
        request: Request = info.context["request"]
        user = get_user_from_request(request)
        
        db_accounts = db.query(models.Account).filter(models.Account.user_id == user["sub"]).all()
        return [
            AccountType(
                account_id=acc.account_id,
                user_id=acc.user_id,
                internal_account_number=acc.internal_account_number,
                status=acc.status.name,
                currency=acc.currency
            ) for acc in db_accounts
        ]

    @strawberry.field
    def ledger_entries_by_transaction(self, transaction_id: str, info: Info) -> List[LedgerEntryType]:
        db: Session = info.context["db"]
        # In a real app we would ensure the transaction belongs to the user
        db_entries = db.query(models.LedgerEntry).filter(models.LedgerEntry.transaction_id == transaction_id).all()
        return [
            LedgerEntryType(
                entry_id=entry.entry_id,
                transaction_id=entry.transaction_id,
                account_id=entry.account_id,
                amount=entry.amount,
                entry_type=entry.entry_type.name,
                status=entry.status,
                created_at=entry.created_at.isoformat() if entry.created_at else ""
            ) for entry in db_entries
        ]

schema = strawberry.Schema(query=Query)

async def get_context(request: Request, db: Session = Depends(get_db)):
    return {"db": db, "request": request}
