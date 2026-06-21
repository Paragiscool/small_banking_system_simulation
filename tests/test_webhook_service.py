import pytest
from src.services.webhook_service import generate_hmac_signature

def test_hmac_signature_generation():
    secret_key = "my_super_secret_key"
    payload = {"transaction_id": "tx-1234", "status": "SETTLED"}
    
    signature = generate_hmac_signature(secret_key, payload)
    
    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA-256 hex digest length
    
    # Verify deterministic behavior (sorting works)
    signature2 = generate_hmac_signature(secret_key, payload)
    assert signature == signature2
    
    # Verify it changes with payload content
    payload3 = {"transaction_id": "tx-1234", "status": "PENDING"}
    signature3 = generate_hmac_signature(secret_key, payload3)
    assert signature != signature3
