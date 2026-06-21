import pytest

def test_fx_conversion_payment(client, auth_headers):
    # Retrieve the seeded accounts
    response = client.get("/accounts", headers=auth_headers)
    assert response.status_code == 200
    accounts = response.json()
    
    usd_account = next((acc for acc in accounts if acc["currency"] == "USD"), None)
    eur_account = next((acc for acc in accounts if acc["currency"] == "EUR"), None)
    
    assert usd_account
    assert eur_account
    
    sender_id = usd_account["account_id"]
    receiver_id = eur_account["account_id"]
    
    # 1. Check receiver's initial balance
    response = client.get(f"/accounts/{receiver_id}/balances", headers=auth_headers)
    assert response.status_code == 200
    initial_receiver_balance = response.json()["available_balance"]

    # 2. Make $1000 payment from USD to EUR
    payment_payload = {
        "sender_account_id": sender_id,
        "receiver_account_id": receiver_id,
        "amount": 1000.0,
        "currency": "USD"
    }
    
    headers = auth_headers.copy()
    headers["x-idempotency-key"] = "test-fx-payment-123"
    
    response = client.post("/payments/domestic-payments", json=payment_payload, headers=headers)
    assert response.status_code == 200
    
    # 3. Check receiver's balance again (1000 USD * 0.92 = 920.0 EUR)
    response = client.get(f"/accounts/{receiver_id}/balances", headers=auth_headers)
    assert response.status_code == 200
    final_receiver_balance = response.json()["available_balance"]
    
    assert final_receiver_balance == initial_receiver_balance + 920.0

def test_virtual_card_issuance_and_charge(client, auth_headers):
    response = client.get("/accounts", headers=auth_headers)
    accounts = response.json()
    account_id = accounts[0]["account_id"]
    
    # 1. Issue a virtual card
    card_payload = {"account_id": account_id, "daily_limit": 500.0}
    response = client.post("/cards/", json=card_payload, headers=auth_headers)
    assert response.status_code == 201
    card = response.json()
    card_id = card["card_id"]
    
    assert card["status"] == "ACTIVE"
    assert card["daily_limit"] == 500.0
    
    # 2. Simulate Merchant Charge (Valid)
    charge_payload = {"merchant_name": "Amazon", "amount": 100.0}
    response = client.post(f"/cards/{card_id}/charge", json=charge_payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    
    # 3. Simulate Merchant Charge (Exceeds Limit)
    charge_payload = {"merchant_name": "Apple Store", "amount": 600.0}
    response = client.post(f"/cards/{card_id}/charge", json=charge_payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Exceeds daily limit" in response.json()["detail"]
    
    # 4. Freeze Card
    response = client.put(f"/cards/{card_id}/status", json={"status": "FROZEN"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "FROZEN"
    
    # 5. Simulate Merchant Charge (Frozen)
    charge_payload = {"merchant_name": "Netflix", "amount": 15.0}
    response = client.post(f"/cards/{card_id}/charge", json=charge_payload, headers=auth_headers)
    assert response.status_code == 400
    assert "FROZEN" in response.json()["detail"]

def test_daily_interest_job(client):
    # APScheduler runs asynchronously, but we can call the job function directly to test logic
    from src.jobs import calculate_daily_interest
    from src.database import SessionLocal
    from src import models
    
    db = SessionLocal()
    # Get a random active account
    account = db.query(models.Account).filter(models.Account.status == models.AccountStatus.ACTIVE).first()
    balance = db.query(models.Balance).filter(models.Balance.account_id == account.account_id).first()
    initial_booked = balance.booked_balance
    
    # Manually execute the job
    calculate_daily_interest()
    
    # Refresh and assert
    db.refresh(balance)
    expected_interest = round(initial_booked * 0.0005, 2)
    assert balance.booked_balance == initial_booked + expected_interest
    db.close()
