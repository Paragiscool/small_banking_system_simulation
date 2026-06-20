import pytest

def test_tpp_registration(client):
    response = client.post("/portal/register", json={
        "app_name": "Pytest App",
        "redirect_uri": "http://localhost/callback"
    })
    assert response.status_code == 200
    data = response.json()
    assert "client_id" in data
    assert "client_secret" in data

def test_oauth_3_legged_flow(client):
    # 1. User grants consent -> Get authorization code
    consent_res = client.post("/consent/authorize", json={
        "client_id": "tpp_test123", # From seed data
        "user_id": "user-123",
        "permissions": '{"accounts": "read"}'
    })
    assert consent_res.status_code == 200
    auth_code = consent_res.json()["authorization_code"]
    
    # 2. TPP exchanges code for JWT
    token_res = client.post(
        "/oauth/token",
        data={
            "code": auth_code,
            "client_id": "tpp_test123"
        },
        headers={"X-Client-Cert-Thumbprint": "valid-cert-123"}
    )
    assert token_res.status_code == 200
    access_token = token_res.json()["access_token"]
    
    # 3. Access Protected API
    api_res = client.get(
        "/accounts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Client-Cert-Thumbprint": "valid-cert-123"
        }
    )
    assert api_res.status_code == 200
    accounts = api_res.json()
    assert len(accounts) > 0
    assert accounts[0]["account_id"] == "test-account-1"

def test_sender_constrained_token_rejection(client):
    # Use our backdoor "test-auth-code" to quickly get a JWT for the hacker test
    token_res = client.post(
        "/oauth/token",
        data={
            "code": "test-auth-code",
            "client_id": "tpp_test123"
        },
        headers={"X-Client-Cert-Thumbprint": "valid-cert-123"}
    )
    access_token = token_res.json()["access_token"]
    
    # Attempt to access with WRONG cert thumbprint
    api_res = client.get(
        "/accounts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Client-Cert-Thumbprint": "hacker-cert-999" # Mismatch!
        }
    )
    assert api_res.status_code == 401
    assert "Token not bound to this client certificate" in api_res.json()["detail"]
