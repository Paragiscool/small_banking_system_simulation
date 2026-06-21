# Webhook & Celery Architecture Guide

This document explains the outbound webhook system implemented in the Open Banking Architecture. It details how we use Celery and Redis to safely execute third-party network requests without blocking our core database transactions, and how we use HMAC to secure them.

---

## 1. The Core Paradigm: Webhooks vs. WebSockets
While **WebSockets** are used for *internal/client-facing* real-time UI updates (keeping a persistent connection open to a browser), **Webhooks** are for *external/server-to-server* communication.

When a payment completes, our bank needs to notify a Third-Party Provider (TPP) (like a budgeting app). Instead of the TPP polling our database, our server acts like a client and makes an HTTP POST request to a URL provided by the TPP (their "Webhook Destination").

---

## 2. Pillar 1: The Asynchronous Guard (Celery + Redis)

### The Problem: The Slow Consumer
If we execute an outbound HTTP request inside our main `POST /payments` endpoint, and the TPP's server is offline or takes 10 seconds to respond, our endpoint hangs for 10 seconds. This blocks our server threads and database connections, leading to a massive system crash under load.

### The Solution: Task Queues
We use **Celery** (a task queue) and **Redis** (a message broker) to decouple the heavy lifting.

1. **FastAPI (The Producer)**: Finishes the database transaction and drops a tiny "task message" into Redis. It instantly returns a `200 OK` to the user.
2. **Redis (The Broker)**: Holds the task securely in memory.
3. **Celery Worker (The Consumer)**: An independent background process running on our server picks up the task from Redis, looks up the Webhook URL, and makes the slow HTTP request.

### Implementation in Code (`src/worker.py`)
We define our background task using the `@celery_app.task` decorator:
```python
from celery import Celery
import httpx

celery_app = Celery("webhooks", broker="redis://localhost:6379/0")

@celery_app.task(bind=True, max_retries=5)
def dispatch_webhook(self, tpp_id: str, event_type: str, payload_dict: dict):
    # 1. Look up the destination URL from the DB
    # 2. Make the request
    try:
        httpx.post(url, json=payload_dict)
    except httpx.HTTPError as exc:
        # Exponential backoff retry logic if TPP is down!
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

In `src/routers/payments.py`, we trigger it asynchronously by calling `.delay()`:
```python
dispatch_webhook.delay(
    tpp_id="mock-client",
    event_type="payment.completed",
    payload_dict={"transaction_id": tx_id}
)
```

---

## 3. Pillar 2: The Cryptographic Vault (HMAC)

### The Problem: Spoofing
Webhooks are sent over the open internet. If a hacker finds out the TPP's destination URL, they could send a fake POST request saying *"Transfer $1,000,000"*. How does the TPP know the request actually came from our bank?

### The Solution: HMAC-SHA256 Signatures
We sign the payload using a `secret_key` that is known *only* to our bank and the TPP.

### Implementation in Code (`src/services/webhook_service.py`)
We serialize the payload into a deterministic JSON string (using `sort_keys=True` so the order of keys never changes), and hash it:

```python
import hmac
import hashlib
import json

def generate_hmac_signature(secret_key: str, payload_dict: dict) -> str:
    # 1. Deterministic JSON serialization
    payload_bytes = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True).encode('utf-8')
    secret_bytes = secret_key.encode('utf-8')
    
    # 2. Hash using SHA-256
    signature = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()
    return signature
```
We then pass this hash in the headers of our webhook request:
```python
headers = {
    "Content-Type": "application/json",
    "X-Webhook-Signature": signature
}
httpx.post(url, content=payload_bytes, headers=headers)
```
The TPP receives the request, runs the exact same HMAC algorithm using their copy of the `secret_key`, and checks if their hash matches our `X-Webhook-Signature`.

---

## 📚 Learning Resources

To master these concepts for interviews and future projects, check out these high-quality resources:

1. **Understanding Webhooks Architecture**
   - *Video:* [What is a Webhook? (Fireship)](https://www.youtube.com/watch?v=41NOoqJwqYE)
   - *Video:* [System Design: Webhooks (ByteByteGo)](https://www.youtube.com/watch?v=E-yAIOii21M)
   - *Reading:* [Stripe's Guide to Webhook Best Practices](https://stripe.com/docs/webhooks/best-practices)

2. **Celery & Redis**
   - *Video:* [Intro to Celery and Task Queues (Pretty Printed)](https://www.youtube.com/watch?v=FjItoIT4R6M)
   - *Reading:* [Official Celery "First Steps" Tutorial](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html)

3. **HMAC & API Security**
   - *Video:* [HMAC Explained Simply](https://www.youtube.com/watch?v=hZ7jX2G_5nU)
   - *Reading:* [Twilio's Guide to Securing Webhooks](https://www.twilio.com/docs/usage/webhooks/webhooks-security)
