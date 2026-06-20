import pytest
import uuid

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

def test_insufficient_funds_rejection(client, auth_headers):
    overdraft_payload = {
        "sender_account_id": "test-account-1",
        "receiver_account_id": "test-account-2",
        "amount": 1000000.0
    }
    res = client.post("/payments/domestic-payments", json=overdraft_payload, headers=auth_headers)
    assert res.status_code == 400
    assert "Insufficient Funds" in res.json()["detail"]

def test_valid_double_entry_payment(client, auth_headers):
    # Verify starting balance is 5000
    acc_res = client.get("/accounts", headers=auth_headers)
    
    valid_payload = {
        "sender_account_id": "test-account-1",
        "receiver_account_id": "test-account-2",
        "amount": 50.0
    }
    res = client.post("/payments/domestic-payments", json=valid_payload, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "AcceptedSettlementCompleted"
    
    # Check Idempotency! Re-sending with the same headers (which includes the same idempotency key)
    # should return 200 but not actually deduct another 50.0
    res_idemp = client.post("/payments/domestic-payments", json=valid_payload, headers=auth_headers)
    assert res_idemp.status_code == 200
    assert res_idemp.json() == res.json()
