import pytest
import uuid

def test_api_rate_limiting(client):
    # Get a JWT
    token_res = client.post(
        "/oauth/token",
        data={
            "code": "test-auth-code",
            "client_id": "tpp_test123"
        },
        headers={"X-Client-Cert-Thumbprint": "valid-cert-123"}
    )
    access_token = token_res.json()["access_token"]
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Client-Cert-Thumbprint": "valid-cert-123"
    }

    from src.governance import LIMITS
    limit = LIMITS.get("accounts", 300)
    
    # We will fire limit + 2 requests
    success_count = 0
    blocked_count = 0
    
    for i in range(limit + 2):
        res = client.get("/accounts", headers=headers)
        if res.status_code == 200:
            success_count += 1
        elif res.status_code == 429:
            blocked_count += 1
            
    assert blocked_count >= 1, "Rate limiter failed to block requests!"
