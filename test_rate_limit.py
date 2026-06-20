import requests
import time

url = "http://127.0.0.1:8000/accounts"
headers = {
    "Authorization": "Bearer mock-valid-token",
    "X-Client-Cert-Thumbprint": "mock-thumbprint"
}

print("Testing Rate Limiter (Limit 300/min)")
print("Firing 305 requests rapidly...")

success_count = 0
rate_limited_count = 0

for i in range(305):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        success_count += 1
    elif response.status_code == 429:
        rate_limited_count += 1
        print(f"Request {i+1} Blocked! Status: {response.status_code}")
        print(f"Headers: X-RateLimit-Limit={response.headers.get('x-ratelimit-limit')}, Retry-After={response.headers.get('retry-after')}")
    else:
        print(f"Unexpected status code: {response.status_code}")

print(f"\nTest Complete. Successes: {success_count}, Blocks (429): {rate_limited_count}")
