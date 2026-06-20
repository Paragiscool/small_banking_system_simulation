from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Enum, Integer
from sqlalchemy.orm import relationship
import enum
import datetime
import uuid
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ConsentStatus(enum.Enum):
    AWAITING_AUTHORISATION = "AWAITING_AUTHORISATION"
    AUTHORISED = "AUTHORISED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class AccountStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"

class EntryType(enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class ThirdPartyProvider(Base):
    __tablename__ = "third_party_providers"
    client_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    redirect_uris = Column(String, nullable=False) # JSON string
    mtls_cert_fingerprint = Column(String, nullable=False)
    signing_cert_public_key = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Consent(Base):
    __tablename__ = "consents"
    consent_id = Column(String, primary_key=True, default=generate_uuid)
    client_id = Column(String, ForeignKey("third_party_providers.client_id"))
    user_id = Column(String, nullable=True) # Set when user approves
    permissions = Column(String, nullable=False) # JSON string
    status = Column(Enum(ConsentStatus), default=ConsentStatus.AWAITING_AUTHORISATION)
    expiration_date = Column(DateTime, nullable=True)

class AuthorizationCode(Base):
    __tablename__ = "authorization_codes"
    code = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey("third_party_providers.client_id"))
    consent_id = Column(String, ForeignKey("consents.consent_id"))
    user_id = Column(String, nullable=True)
    code_challenge = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

class Account(Base):
    __tablename__ = "accounts"
    account_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    internal_account_number = Column(String, unique=True, nullable=False)
    status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE)
    currency = Column(String, default="USD")

class Balance(Base):
    __tablename__ = "balances"
    account_id = Column(String, ForeignKey("accounts.account_id"), primary_key=True)
    available_balance = Column(Float, default=0.0)
    booked_balance = Column(Float, default=0.0)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    entry_id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, index=True, nullable=False)
    account_id = Column(String, ForeignKey("accounts.account_id"))
    amount = Column(Float, nullable=False)
    entry_type = Column(Enum(EntryType), nullable=False)
    status = Column(String, default="BOOKED")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    idempotency_key = Column(String, primary_key=True)
    client_id = Column(String, nullable=False)
    request_path = Column(String, nullable=False)
    response_body = Column(String, nullable=True) # JSON string
    response_status = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
