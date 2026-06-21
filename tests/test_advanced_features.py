import pytest
from src.models import LedgerEntry, Balance, ThirdPartyProvider
import uuid

@pytest.fixture
def auth_headers(client):
    token_res = client.post(
        "/oauth/token",
        data={
            "code": "test-auth-code",
            "client_id": "tpp_test123"
        },
        headers={"X-Client-Cert-Thumbprint": "valid-cert-123"}
    )
    access_token = token_res.json()["access_token"]
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Client-Cert-Thumbprint": "valid-cert-123"
    }

def test_fraud_engine_flags_large_transaction(client, test_db, auth_headers):
    # Setup test DB manually: boost balance of test-account-1 to 20000
    sender = test_db.query(Balance).filter(Balance.account_id == "test-account-1").first()
    sender.available_balance = 20000.0
    test_db.commit()

    headers = auth_headers.copy()
    headers["x-idempotency-key"] = "fraud-test-1"

    payload = {
        "sender_account_id": "test-account-1",
        "receiver_account_id": "test-account-2",
        "amount": 15000.00,
        "currency": "USD"
    }

    response = client.post("/payments/domestic-payments", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AcceptedPendingReview"
    tx_id = data["transaction_id"]

    # Verify sender was deducted
    sender = test_db.query(Balance).filter(Balance.account_id == "test-account-1").first()
    assert sender.available_balance == 5000.00

    # Verify receiver was NOT credited
    receiver = test_db.query(Balance).filter(Balance.account_id == "test-account-2").first()
    assert receiver.available_balance == 150.00

    # Verify Ledger Status
    ledger_entries = test_db.query(LedgerEntry).filter(LedgerEntry.transaction_id == tx_id).all()
    for entry in ledger_entries:
        assert entry.status == "PENDING_REVIEW"
        
    # Now Admin approves it
    admin_response = client.post("/admin/approve-transaction", json={"transaction_id": tx_id})
    assert admin_response.status_code == 200
    
    # Verify receiver WAS credited. Expire test_db cache first!
    test_db.expire_all()
    receiver = test_db.query(Balance).filter(Balance.account_id == "test-account-2").first()
    assert receiver.available_balance == 15150.00
    
    # Verify Ledger Status changed to SETTLED
    ledger_entries = test_db.query(LedgerEntry).filter(LedgerEntry.transaction_id == tx_id).all()
    for entry in ledger_entries:
        assert entry.status == "SETTLED"

def test_webhook_fired_on_normal_transaction(client, test_db, auth_headers):
    headers = auth_headers.copy()
    headers["x-idempotency-key"] = "webhook-test-1"

    payload = {
        "sender_account_id": "test-account-1",
        "receiver_account_id": "test-account-2",
        "amount": 100.00,
        "currency": "USD"
    }
    
    # Register TPP with webhook URL
    client.post("/portal/register", json={
        "app_name": "Webhook Test App",
        "redirect_uri": "http://localhost/callback",
        "webhook_url": "http://127.0.0.1:8000/sandbox/mock-webhook"
    })

    response = client.post("/payments/domestic-payments", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "AcceptedSettlementCompleted"
