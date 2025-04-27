import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from . import crud, models, schemas
from .database import async_session_maker
from .webhook_processor import process_webhook_delivery, retry_failed_deliveries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def cleanup_old_logs(days_to_keep: int = 30):
    """Clean up delivery logs older than specified days."""
    async with async_session_maker() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete old deliveries
        stmt = select(models.WebhookDelivery).where(
            models.WebhookDelivery.created_at < cutoff_date
        )
        result = await session.execute(stmt)
        old_deliveries = result.scalars().all()
        
        for delivery in old_deliveries:
            await session.delete(delivery)
        
        await session.commit()
        logger.info(f"Cleaned up {len(old_deliveries)} old deliveries")

async def process_pending_deliveries():
    """Process any pending webhook deliveries."""
    async with async_session_maker() as session:
        stmt = select(models.WebhookDelivery).where(
            models.WebhookDelivery.status == models.DeliveryStatus.PENDING
        )
        result = await session.execute(stmt)
        pending_deliveries = result.scalars().all()
        
        for delivery in pending_deliveries:
            subscription = await crud.get_subscription(session, delivery.subscription_id)
            if subscription:
                await process_webhook_delivery(
                    session,
                    str(delivery.id),
                    str(subscription.target_url),
                    delivery.payload,
                    str(subscription.id),
                    subscription.secret
                )

async def main():
    """Main worker loop."""
    logger.info("Starting worker...")
    
    while True:
        try:
            # Process pending deliveries
            await process_pending_deliveries()
            
            # Retry failed deliveries
            await retry_failed_deliveries(async_session_maker)
            
            # Clean up old logs
            await cleanup_old_logs()
            
            # Sleep for a short interval
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
            await asyncio.sleep(5)  # Sleep on error to prevent tight loop

if __name__ == "__main__":
    asyncio.run(main())