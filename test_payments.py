import requests
import uuid

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def get_auth_token():
    # 1. Get a real JWT Token
    token_url = f"{BASE_URL}/oauth/token"
    token_payload = {
        "code": "test-auth-code",
        "client_id": "tpp_test123"
    }
    token_headers = {
        "X-Client-Cert-Thumbprint": "valid-cert-123"
    }
    
    token_res = requests.post(token_url, data=token_payload, headers=token_headers)
    if token_res.status_code != 200:
        raise Exception(f"Failed to get token: {token_res.text}")
        
    return token_res.json().get("access_token")

def test_ledger():
    access_token = get_auth_token()
    auth_headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Client-Cert-Thumbprint": "valid-cert-123",
        "x-idempotency-key": str(uuid.uuid4())
    }
    
    print("Fetching Accounts...")
    accounts_res = requests.get(f"{BASE_URL}/accounts", headers=auth_headers)
    accounts = accounts_res.json()
    if len(accounts) < 2:
        raise Exception("Need at least 2 accounts to test payments")
        
    sender = accounts[0]['account_id']
    receiver = accounts[1]['account_id']
    
    # 1. Attempt Overdraft (Should fail)
    print("\nAttempting to send $1,000,000 (Insufficient Funds Test)...")
    overdraft_payload = {
        "sender_account_id": sender,
        "receiver_account_id": receiver,
        "amount": 1000000.0
    }
    
    auth_headers["x-idempotency-key"] = str(uuid.uuid4()) # New key for new request
    res1 = requests.post(f"{BASE_URL}/payments/domestic-payments", json=overdraft_payload, headers=auth_headers)
    print(f"Status: {res1.status_code} - {res1.text}")
    assert res1.status_code == 400
    
    # 2. Attempt Valid Payment
    print("\nAttempting valid $50 payment...")
    valid_payload = {
        "sender_account_id": sender,
        "receiver_account_id": receiver,
        "amount": 50.0
    }
    
    auth_headers["x-idempotency-key"] = str(uuid.uuid4())
    res2 = requests.post(f"{BASE_URL}/payments/domestic-payments", json=valid_payload, headers=auth_headers)
    print(f"Status: {res2.status_code} - {res2.text}")
    assert res2.status_code == 200
    
    # 3. Test Idempotency (Sending same key should return same transaction without deducting again)
    print("\nRe-sending exact same request (Idempotency Test)...")
    res3 = requests.post(f"{BASE_URL}/payments/domestic-payments", json=valid_payload, headers=auth_headers)
    print(f"Status: {res3.status_code} - {res3.text}")
    assert res3.status_code == 200
    assert res3.json() == res2.json()

if __name__ == "__main__":
    test_ledger()
    print("\nAll Ledger tests passed successfully!")
