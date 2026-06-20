import requests

BASE_URL = "http://127.0.0.1:8000"

def test_full_oauth_flow():
    print("--- Phase 5: Complete 3-Legged OAuth 2.0 Flow Test ---\n")
    
    # 1. TPP Registration (Simulating Developer Portal)
    print("1. Registering new TPP (Third Party Provider)...")
    reg_res = requests.post(f"{BASE_URL}/portal/register", json={
        "app_name": "Test Finance App",
        "redirect_uri": "http://localhost/callback"
    })
    assert reg_res.status_code == 200, "Registration failed"
    tpp_data = reg_res.json()
    client_id = tpp_data["client_id"]
    print(f"   Success! Client ID: {client_id}")
    
    # 2. User Consent (Simulating the Bank Consent HTML Screen)
    print("\n2. Simulating User granting Consent via Bank UI...")
    consent_res = requests.post(f"{BASE_URL}/consent/authorize", json={
        "client_id": client_id,
        "user_id": "user-123",
        "permissions": '{"accounts": "read"}'
    })
    assert consent_res.status_code == 200, f"Consent failed: {consent_res.text}"
    consent_data = consent_res.json()
    auth_code = consent_data["authorization_code"]
    print(f"   Success! Authorization Code generated: {auth_code[:10]}...")
    
    # 3. Token Exchange (Simulating TPP Backend trading Code for JWT)
    print("\n3. TPP exchanging Authorization Code for JWT...")
    token_res = requests.post(
        f"{BASE_URL}/oauth/token", 
        data={
            "code": auth_code,
            "client_id": client_id
        },
        headers={"X-Client-Cert-Thumbprint": "valid-cert-123"}
    )
    assert token_res.status_code == 200, f"Token exchange failed: {token_res.text}"
    access_token = token_res.json()["access_token"]
    print(f"   Success! Acquired JWT: {access_token[:20]}...")
    
    # 4. API Access (Simulating TPP Backend calling Core API)
    print("\n4. Accessing Protected Core API with JWT...")
    api_res = requests.get(
        f"{BASE_URL}/accounts", 
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Client-Cert-Thumbprint": "valid-cert-123"
        }
    )
    assert api_res.status_code == 200, "API Access failed"
    print(f"   Success! Retrieved Accounts: {api_res.json()}")

if __name__ == "__main__":
    test_full_oauth_flow()
    print("\nAll OAuth 2.0 flow tests passed successfully!")
