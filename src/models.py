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
    webhook_url = Column(String, nullable=True)
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

from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Enum, Integer, UniqueConstraint

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (UniqueConstraint('account_id', 'sequence_number', name='uix_account_sequence'),)
    entry_id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, index=True, nullable=False)
    account_id = Column(String, ForeignKey("accounts.account_id"))
    amount = Column(Float, nullable=False)
    entry_type = Column(Enum(EntryType), nullable=False)
    status = Column(String, default="BOOKED")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    sequence_number = Column(Integer, nullable=False, default=1)
    previous_hash = Column(String, nullable=False, default="0")
    current_hash = Column(String, nullable=False, default="0")

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    idempotency_key = Column(String, primary_key=True)
    client_id = Column(String, nullable=False)
    request_path = Column(String, nullable=False)
    response_body = Column(String, nullable=True) # JSON string
    response_status = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class VirtualCardStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CANCELED = "CANCELED"

class VirtualCard(Base):
    __tablename__ = "virtual_cards"
    card_id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    card_number = Column(String, unique=True, nullable=False)
    cvv = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False) # e.g., "12/28"
    status = Column(Enum(VirtualCardStatus), default=VirtualCardStatus.ACTIVE)
    daily_limit = Column(Float, default=1000.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    id = Column(String, primary_key=True, default=generate_uuid)
    from_currency = Column(String, nullable=False, index=True)
    to_currency = Column(String, nullable=False, index=True)
    rate = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    tpp_id = Column(String, nullable=False)
    destination_url = Column(String, nullable=False)
    secret_key = Column(String, nullable=False)  # Used for signing HMAC
    is_active = Column(Boolean, default=True)
    subscribed_events = Column(String, nullable=False) # JSON array or comma separated
