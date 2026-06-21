from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class AccountResponse(BaseModel):
    account_id: str
    status: str
    currency: str

    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    account_id: str
    available_balance: float
    booked_balance: float

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    sender_account_id: str
    receiver_account_id: str
    amount: float

class PaymentResponse(BaseModel):
    status: str
    transaction_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class ParResponse(BaseModel):
    request_uri: str
    expires_in: int

class VirtualCardCreate(BaseModel):
    account_id: str
    daily_limit: Optional[float] = 1000.0

class VirtualCardResponse(BaseModel):
    card_id: str
    account_id: str
    card_number: str
    cvv: str
    expiry_date: str
    status: str
    daily_limit: float

class VirtualCardStatusUpdate(BaseModel):
    status: str

class ChargeRequest(BaseModel):
    merchant_name: str
    amount: float
    currency: str = "USD"
