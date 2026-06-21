import os
import json
import httpx
import logging
from celery import Celery
from .database import SessionLocal
from .models import WebhookSubscription
from .services.webhook_service import generate_hmac_signature

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "webhooks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(bind=True, max_retries=5)
def dispatch_webhook(self, tpp_id: str, event_type: str, payload_dict: dict):
    db = SessionLocal()
    try:
        # 1. Look up the WebhookSubscription from the database
        subscription = db.query(WebhookSubscription).filter(
            WebhookSubscription.tpp_id == tpp_id,
            WebhookSubscription.is_active == True
        ).first()
        
        if not subscription:
            logger.info(f"No active webhook subscription found for TPP {tpp_id}")
            return
            
        # Optional: check if event_type is in subscribed_events
        if event_type not in subscription.subscribed_events:
            logger.info(f"TPP {tpp_id} is not subscribed to {event_type}")
            return

        # 2. Serialize the payload to JSON
        payload_bytes = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True)
        
        # 3. Generate the HMAC signature using the secret_key
        signature = generate_hmac_signature(subscription.secret_key, payload_dict)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event_type
        }
        
        # 4. Make an HTTP POST request to the destination_url
        logger.info(f"Dispatching webhook to {subscription.destination_url} for event {event_type}")
        response = httpx.post(
            subscription.destination_url,
            content=payload_bytes,
            headers=headers,
            timeout=10.0
        )
        response.raise_for_status()
        logger.info(f"Successfully delivered webhook. Status: {response.status_code}")
        
    except httpx.HTTPError as exc:
        logger.warning(f"HTTP Error delivering webhook: {exc}. Retrying...")
        # Exponential backoff retry logic
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error(f"Unexpected error in webhook delivery: {exc}")
        raise exc
    finally:
        db.close()
