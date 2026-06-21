import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from src.main import app
from src.database import Base, get_db
from src import models

# Use an in-memory SQLite database for testing, shared across threads
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the FastAPI dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_db():
    """Create fresh database tables for each test and populate seed data."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed Test Data
    account1_id = "test-account-1"
    account2_id = "test-account-2"
    
    acc1 = models.Account(account_id=account1_id, user_id="user-123", internal_account_number="test-1001", currency="USD")
    acc2 = models.Account(account_id=account2_id, user_id="user-456", internal_account_number="test-2002", currency="USD")
    account3_id = "test-account-3"
    acc3 = models.Account(account_id=account3_id, user_id="user-789", internal_account_number="test-3003", currency="EUR")
    db.add_all([acc1, acc2, acc3])
    
    bal1 = models.Balance(account_id=account1_id, available_balance=5000.0, booked_balance=5000.0)
    bal2 = models.Balance(account_id=account2_id, available_balance=150.0, booked_balance=150.0)
    bal3 = models.Balance(account_id=account3_id, available_balance=1000.0, booked_balance=1000.0)
    db.add_all([bal1, bal2, bal3])
    
    tpp = models.ThirdPartyProvider(
        client_id="tpp_test123",
        name="Pytest TPP",
        redirect_uris="http://localhost",
        mtls_cert_fingerprint="valid-cert-123",
        signing_cert_public_key="test-key"
    )
    db.add(tpp)
    
    rates = [
        models.ExchangeRate(from_currency="USD", to_currency="EUR", rate=0.92),
        models.ExchangeRate(from_currency="EUR", to_currency="USD", rate=1.08)
    ]
    db.add_all(rates)
    
    db.commit()
    
    yield db
    
    # Teardown
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Provide a TestClient that uses the overridden DB dependency."""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def access_token(client):
    token_res = client.post(
        "/oauth/token",
        data={
            "code": "test-auth-code",
            "client_id": "tpp_test123"
        },
        headers={"X-Client-Cert-Thumbprint": "valid-cert-123"}
    )
    return token_res.json()["access_token"]

@pytest.fixture
def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Client-Cert-Thumbprint": "valid-cert-123",
        "x-idempotency-key": str(uuid.uuid4())
    }
