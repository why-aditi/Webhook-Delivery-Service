import httpx
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from . import models, cache
from .models import DeliveryStatus
import asyncio
import math
from .logging_config import setup_logging, log_delivery_attempt

# Set up structured logging
logger = setup_logging()

# Configuration
MAX_RETRIES = 5  # Maximum number of retry attempts
BASE_DELAY = 10  # Base delay in seconds
MAX_DELAY = 900  # Maximum delay (15 minutes) in seconds
REQUEST_TIMEOUT = 10.0  # seconds

def calculate_next_retry_delay(retry_count: int) -> int:
    """
    Calculate the next retry delay using exponential backoff with jitter.
    Delays: 10s, 30s, 1m, 5m, 15m
    """
    # Exponential backoff: BASE_DELAY * (2 ^ retry_count)
    delay = min(BASE_DELAY * (2 ** retry_count), MAX_DELAY)
    
    # Add jitter (±20% randomization to prevent thundering herd)
    jitter = delay * 0.2 * (hash(str(datetime.utcnow())) % 100) / 100
    final_delay = delay + jitter
    
    return min(int(final_delay), MAX_DELAY)

async def create_delivery_record(
    db: AsyncSession,
    subscription_id: str,
    event_type: str,
    payload: Dict[Any, Any]
) -> models.WebhookDelivery:
    """Create a new webhook delivery record."""
    delivery = models.WebhookDelivery(
        subscription_id=subscription_id,
        event_type=event_type,
        payload=payload,
        status=DeliveryStatus.PENDING
    )
    db.add(delivery)
    await db.commit()
    await db.refresh(delivery)
    
    log_delivery_attempt(
        logger=logger,
        delivery_id=str(delivery.id),
        subscription_id=subscription_id,
        target_url="pending",
        attempt_number=0,
        status="pending",
        extra_data={"event_type": event_type}
    )
    
    return delivery

async def process_webhook_delivery(
    db: AsyncSession,
    delivery_id: str,
    target_url: str,
    payload: Dict[Any, Any],
    subscription_id: str,
    secret: Optional[str] = None
) -> bool:
    """Process a webhook delivery with retry logic and status tracking."""
    try:
        # Get delivery record
        delivery = await db.get(models.WebhookDelivery, delivery_id)
        if not delivery:
            log_delivery_attempt(
                logger=logger,
                delivery_id=delivery_id,
                subscription_id=subscription_id,
                target_url=target_url,
                attempt_number=0,
                status="error",
                error_details="Delivery record not found"
            )
            return False

        # Update status to in progress
        delivery.status = DeliveryStatus.IN_PROGRESS
        delivery.last_attempt = datetime.utcnow()
        await db.commit()
        
        current_attempt = delivery.retry_count + 1
        
        log_delivery_attempt(
            logger=logger,
            delivery_id=delivery_id,
            subscription_id=subscription_id,
            target_url=target_url,
            attempt_number=current_attempt,
            status="in_progress"
        )

        # Try to get subscription details from cache first
        cached_subscription = await cache.get_cached_subscription(UUID(subscription_id))
        if cached_subscription:
            target_url = cached_subscription["target_url"]
            secret = cached_subscription["secret"]

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Webhook-Delivery-Service/1.0",
            "X-Webhook-ID": str(subscription_id),
            "X-Delivery-ID": str(delivery_id),
            "X-Retry-Count": str(delivery.retry_count)
        }

        if secret:
            signature = generate_signature(payload, secret)
            headers["X-Webhook-Signature"] = signature

        # Attempt delivery
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    str(target_url),
                    json=payload,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )

                delivery.response_status = response.status_code
                delivery.response_body = response.text[:1000]  # Limit response body size
                
                if 200 <= response.status_code < 300:
                    delivery.status = DeliveryStatus.DELIVERED
                    await db.commit()
                    
                    log_delivery_attempt(
                        logger=logger,
                        delivery_id=delivery_id,
                        subscription_id=subscription_id,
                        target_url=target_url,
                        attempt_number=current_attempt,
                        status="delivered",
                        response_code=response.status_code
                    )
                    return True
                
                # Handle non-2xx responses
                error_msg = f"Target URL returned {response.status_code}: {response.text[:200]}"
                raise httpx.HTTPError(error_msg)

            except httpx.TimeoutException as e:
                error_msg = f"Timeout after {REQUEST_TIMEOUT}s: {str(e)}"
                log_delivery_attempt(
                    logger=logger,
                    delivery_id=delivery_id,
                    subscription_id=subscription_id,
                    target_url=target_url,
                    attempt_number=current_attempt,
                    status="failed",
                    error_details=error_msg
                )
                raise

            except httpx.HTTPError as e:
                error_msg = f"HTTP Error: {str(e)}"
                log_delivery_attempt(
                    logger=logger,
                    delivery_id=delivery_id,
                    subscription_id=subscription_id,
                    target_url=target_url,
                    attempt_number=current_attempt,
                    status="failed",
                    response_code=response.status_code if 'response' in locals() else None,
                    error_details=error_msg
                )
                raise

            except httpx.NetworkError as e:
                error_msg = f"Network Error: {str(e)}"
                log_delivery_attempt(
                    logger=logger,
                    delivery_id=delivery_id,
                    subscription_id=subscription_id,
                    target_url=target_url,
                    attempt_number=current_attempt,
                    status="failed",
                    error_details=error_msg
                )
                raise

    except Exception as e:
        if not delivery.error_message:
            delivery.error_message = str(e)[:500]  # Limit error message size
        
        delivery.status = DeliveryStatus.FAILED
        delivery.retry_count += 1

        if delivery.retry_count < MAX_RETRIES:
            # Calculate next retry time using exponential backoff
            delay = calculate_next_retry_delay(delivery.retry_count - 1)
            delivery.next_retry = datetime.utcnow() + timedelta(seconds=delay)
            
            log_delivery_attempt(
                logger=logger,
                delivery_id=delivery_id,
                subscription_id=subscription_id,
                target_url=target_url,
                attempt_number=current_attempt,
                status="retry_scheduled",
                error_details=str(e),
                extra_data={
                    "next_retry": delivery.next_retry.isoformat(),
                    "retry_delay": delay
                }
            )
        else:
            delivery.status = DeliveryStatus.MAX_RETRIES_EXCEEDED
            delivery.next_retry = None
            
            log_delivery_attempt(
                logger=logger,
                delivery_id=delivery_id,
                subscription_id=subscription_id,
                target_url=target_url,
                attempt_number=current_attempt,
                status="max_retries_exceeded",
                error_details=str(e)
            )

        await db.commit()
        return False

def generate_signature(payload: Dict[Any, Any], secret: str) -> str:
    """Generate HMAC SHA256 signature for the payload using the secret."""
    payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return signature

async def retry_failed_deliveries(session_maker: async_sessionmaker):
    """Background task to retry failed webhook deliveries."""
    while True:
        try:
            async with session_maker() as db:
                # Find deliveries that need retry
                now = datetime.utcnow()
                stmt = (
                    models.WebhookDelivery.__table__.select()
                    .where(
                        models.WebhookDelivery.status == DeliveryStatus.FAILED,
                        models.WebhookDelivery.retry_count < MAX_RETRIES,
                        models.WebhookDelivery.next_retry <= now
                    )
                )
                result = await db.execute(stmt)
                deliveries = result.fetchall()

                for delivery in deliveries:
                    # Get subscription details
                    subscription = await db.get(models.Subscription, delivery.subscription_id)
                    if subscription:
                        await process_webhook_delivery(
                            db=db,
                            delivery_id=delivery.id,
                            target_url=subscription.target_url,
                            payload=delivery.payload,
                            subscription_id=subscription.id,
                            secret=subscription.secret
                        )

        except Exception as e:
            logger.error(f"Error in retry_failed_deliveries: {str(e)}")

        # Wait before next retry check
        await asyncio.sleep(5)  # Check every 5 seconds 