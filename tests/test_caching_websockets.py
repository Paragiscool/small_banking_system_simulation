import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.cache import clear_all_cache, get_cache

def test_cache_hit_and_invalidation(client, auth_headers):
    # Ensure cache is clean
    clear_all_cache()
    
    response = client.get("/accounts", headers=auth_headers)
    assert response.status_code == 200
    accounts = response.json()
    account_id = accounts[0]["account_id"]
    
    # Check that accounts were cached
    assert get_cache("all_accounts") is not None
    
    # 1. First fetch - should query DB and populate cache
    response = client.get(f"/accounts/{account_id}/balances", headers=auth_headers)
    assert response.status_code == 200
    initial_balance = response.json()["available_balance"]
    
    # Verify cache is set
    cached_balance = get_cache(f"balance_{account_id}")
    assert cached_balance is not None
    assert cached_balance.available_balance == initial_balance

    # 2. Make a payment to invalidate the cache
    receiver_id = accounts[1]["account_id"]
    payment_payload = {
        "sender_account_id": account_id,
        "receiver_account_id": receiver_id,
        "amount": 50.0
    }
    
    res = client.post("/payments/domestic-payments", json=payment_payload, headers=auth_headers)
    assert res.status_code == 200
    
    # 3. Verify cache is invalidated
    assert get_cache(f"balance_{account_id}") is None
    assert get_cache(f"balance_{receiver_id}") is None
    
    # 4. Fetch again - should get new balance and set cache
    response = client.get(f"/accounts/{account_id}/balances", headers=auth_headers)
    assert response.status_code == 200
    new_balance = response.json()["available_balance"]
    assert new_balance == initial_balance - 50.0
    
    assert get_cache(f"balance_{account_id}") is not None

def test_websocket_notification(client, auth_headers):
    response = client.get("/accounts", headers=auth_headers)
    accounts = response.json()
    sender_id = accounts[0]["account_id"]
    receiver_id = accounts[1]["account_id"]
    
    # Use the TestClient context manager for websockets
    with client.websocket_connect(f"/ws/{sender_id}") as websocket:
        # Make a payment to trigger the broadcast
        payment_payload = {
            "sender_account_id": sender_id,
            "receiver_account_id": receiver_id,
            "amount": 10.0
        }
        res = client.post("/payments/domestic-payments", json=payment_payload, headers=auth_headers)
        assert res.status_code == 200
        
        # Wait for and receive the WebSocket message
        data = websocket.receive_json()
        assert data["type"] == "PAYMENT_SENT"
        assert data["amount"] == 10.0
        assert "transaction_id" in data
