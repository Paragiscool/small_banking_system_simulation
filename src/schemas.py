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
