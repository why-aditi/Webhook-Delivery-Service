import asyncio
import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import models, crud
from .database import async_session_maker

async def create_delivery_record(
    session: AsyncSession,
    subscription_id: str,
    event_type: str,
    payload: dict
) -> models.WebhookDelivery:
    """Create a new webhook delivery record."""
    delivery = models.WebhookDelivery(
        subscription_id=subscription_id,
        event_type=event_type,
        payload=payload,
        status=models.DeliveryStatus.PENDING,
        retry_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(delivery)
    await session.commit()
    await session.refresh(delivery)
    return delivery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/webhook_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def process_webhook_delivery(
    session: AsyncSession,
    delivery_id: str,
    target_url: str,
    payload: dict,
    subscription_id: str,
    secret: str
) -> None:
    """Process a single webhook delivery."""
    try:
        # Get the delivery
        delivery = await crud.get_delivery(session, delivery_id)
        if not delivery:
            logger.error(f"Delivery {delivery_id} not found")
            return

        # Update delivery status to in progress
        delivery.status = models.DeliveryStatus.IN_PROGRESS
        delivery.retry_count += 1
        delivery.last_attempt = datetime.utcnow()
        await session.commit()
        
        # Generate signature
        payload_str = json.dumps(payload)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Send webhook
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Id': delivery_id,
            'X-Webhook-Subscription-Id': subscription_id
        }
        
        async with aiohttp.ClientSession() as client:
            async with client.post(
                target_url,
                json=payload,
                headers=headers,
                timeout=30
            ) as response:
                status_code = response.status
                response_text = await response.text()
                
                # Update delivery status
                delivery.status = models.DeliveryStatus.DELIVERED if 200 <= status_code < 300 else models.DeliveryStatus.FAILED
                delivery.response_status = status_code
                delivery.response_body = response_text
                delivery.updated_at = datetime.utcnow()
                
                if delivery.status == models.DeliveryStatus.FAILED and delivery.retry_count >= 3:
                    delivery.status = models.DeliveryStatus.MAX_RETRIES_EXCEEDED
                
                await session.commit()
                
                logger.info(
                    f"Webhook delivery {delivery_id} to {target_url} "
                    f"completed with status {status_code}"
                )
                
    except Exception as e:
        logger.error(f"Error processing webhook delivery {delivery_id}: {e}")
        
        # Update delivery status
        delivery = await crud.get_delivery(session, delivery_id)
        if delivery:
            delivery.status = models.DeliveryStatus.FAILED
            delivery.error_message = str(e)
            delivery.updated_at = datetime.utcnow()
            
            if delivery.retry_count >= 3:
                delivery.status = models.DeliveryStatus.MAX_RETRIES_EXCEEDED
            
            await session.commit()

async def retry_failed_deliveries(session_maker) -> None:
    """Retry failed webhook deliveries."""
    async with session_maker() as session:
        # Get failed deliveries that haven't been retried too many times
        stmt = select(models.WebhookDelivery).where(
            models.WebhookDelivery.status == models.DeliveryStatus.FAILED,
            models.WebhookDelivery.retry_count < 3
        )
        result = await session.execute(stmt)
        failed_deliveries = result.scalars().all()
        
        for delivery in failed_deliveries:
            # Increment retry count
            delivery.retry_count += 1
            delivery.status = models.DeliveryStatus.PENDING
            delivery.updated_at = datetime.utcnow()
            
            # Get subscription
            subscription = await crud.get_subscription(session, delivery.subscription_id)
            if subscription:
                # Process delivery
                await process_webhook_delivery(
                    session,
                    str(delivery.id),
                    str(subscription.target_url),
                    delivery.payload,
                    str(subscription.id),
                    subscription.secret
                )
            
            await session.commit()
            
            logger.info(
                f"Retried delivery {delivery.id} (attempt {delivery.retry_count})"
            )