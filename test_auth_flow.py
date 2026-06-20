import requests

# 1. Get a real JWT Token from the Auth endpoint
token_url = "http://127.0.0.1:8000/oauth/token"
token_payload = {
    "code": "test-auth-code",
    "client_id": "tpp_test123"
}
token_headers = {
    "X-Client-Cert-Thumbprint": "valid-cert-123"
}

print("Fetching real JWT Token...")
token_res = requests.post(token_url, data=token_payload, headers=token_headers)
if token_res.status_code != 200:
    print(f"Failed to get token: {token_res.text}")
    exit(1)
    
access_token = token_res.json().get("access_token")
print(f"Token acquired: {access_token[:20]}...\n")

# 2. Use the JWT Token to hit a protected endpoint
accounts_url = "http://127.0.0.1:8000/accounts"
auth_headers = {
    "Authorization": f"Bearer {access_token}",
    "X-Client-Cert-Thumbprint": "valid-cert-123"
}

print("Accessing /accounts with JWT and matching cert thumbprint...")
accounts_res = requests.get(accounts_url, headers=auth_headers)
print(f"Status: {accounts_res.status_code}")
print(f"Response: {accounts_res.json()}\n")

# 3. Test Sender-Constrained Failure (Wrong cert thumbprint)
bad_headers = {
    "Authorization": f"Bearer {access_token}",
    "X-Client-Cert-Thumbprint": "hacker-cert-999"
}

print("Accessing /accounts with wrong cert thumbprint (Sender-Constrained test)...")
bad_res = requests.get(accounts_url, headers=bad_headers)
print(f"Status: {bad_res.status_code}")
print(f"Response: {bad_res.json()}")
