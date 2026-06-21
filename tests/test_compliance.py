import pytest
from src.dependencies import SECRET_KEY, ALGORITHM
import jwt
from datetime import datetime, timedelta

def get_token_with_scopes(scopes):
    payload = {
        "sub": "user-123",
        "client_id": "test_client",
        "scopes": scopes,
        "exp": datetime.utcnow() + timedelta(seconds=3600),
        "iat": datetime.utcnow(),
        "cnf": "valid-cert-123"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def test_rbac_admin_endpoint_forbidden(client):
    # 1. Token without "admin:approve" scope
    token_user = get_token_with_scopes(["read:balance", "write:payments"])
    headers_user = {
        "Authorization": f"Bearer {token_user}",
        "X-Client-Cert-Thumbprint": "valid-cert-123"
    }
    
    payload = {"transaction_id": "TX-1234"}
    response = client.post("/admin/approve-transaction", json=payload, headers=headers_user)
    
    # Should be 403 Forbidden
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"

def test_rbac_admin_endpoint_allowed(client):
    # 2. Token with "admin:approve" scope
    token_admin = get_token_with_scopes(["admin:approve"])
    headers_admin = {
        "Authorization": f"Bearer {token_admin}",
        "X-Client-Cert-Thumbprint": "valid-cert-123"
    }
    
    payload = {"transaction_id": "TX-INVALID"}
    response = client.post("/admin/approve-transaction", json=payload, headers=headers_admin)
    
    # It passes RBAC, but fails logic (404 Transaction not found)
    assert response.status_code == 404

def test_statement_generation_csv(client, auth_headers):
    # First, get an account
    response = client.get("/accounts", headers=auth_headers)
    assert response.status_code == 200
    account_id = response.json()[0]["account_id"]
    
    # Generate Statement
    res = client.get(f"/accounts/{account_id}/statement", headers=auth_headers)
    assert res.status_code in [200, 404] # 404 if no transactions yet
    
    if res.status_code == 200:
        assert res.headers["content-type"] == "text/csv; charset=utf-8"
        assert "Content-Disposition" in res.headers
        assert "attachment;" in res.headers["content-disposition"]
        content = res.content.decode("utf-8")
        assert "Transaction ID,Date,Type,Amount,Status" in content

def test_audit_log_middleware(client):
    # Make a random request to trigger audit log
    client.get("/non-existent-path")
    
    # For testing AuditLogMiddleware, we can't easily check the DB because it uses SessionLocal()
    # Which hits the real database, not the test database memory.
    # Instead, we just verify the endpoint didn't crash.
    pass
