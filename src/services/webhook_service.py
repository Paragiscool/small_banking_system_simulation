import hmac
import hashlib
import json

def generate_hmac_signature(secret_key: str, payload_dict: dict) -> str:
    """
    Generate a SHA-256 HMAC signature for a given payload.
    """
    # Use compact JSON encoding to ensure signature reproducibility
    payload_bytes = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True).encode('utf-8')
    secret_bytes = secret_key.encode('utf-8')
    
    signature = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()
    return signature
