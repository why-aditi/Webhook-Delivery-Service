import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiohttp
from aiohttp import web

from app.database import async_session_maker, init_db
from app import models, crud
from app.webhook_processor import process_webhook_delivery
from app.worker import process_pending_deliveries, cleanup_old_logs, retry_failed_deliveries

@pytest.fixture
async def test_app():
    """Create a test aiohttp application."""
    app = web.Application()
    return app

@pytest.fixture
async def test_client(test_app):
    """Create a test client."""
    return aiohttp.ClientSession()

@pytest.fixture
async def db_session():
    """Create a test database session."""
    await init_db()
    async with async_session_maker() as session:
        yield session
        await session.rollback()

@pytest.mark.asyncio
async def test_webhook_delivery_flow(db_session: AsyncSession, test_client: aiohttp.ClientSession):
    """Test the complete webhook delivery flow."""
    # Create a test subscription
    subscription = models.Subscription(
        target_url="http://test-server/webhook",
        secret="test-secret",
        event_types=["test_event"],
        created_at=datetime.utcnow()
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # Create a test delivery
    delivery = models.WebhookDelivery(
        subscription_id=subscription.id,
        event_type="test_event",
        payload={"event": "test"},
        status=models.DeliveryStatus.PENDING,
        created_at=datetime.utcnow()
    )
    db_session.add(delivery)
    await db_session.commit()
    
    # Process the delivery
    await process_webhook_delivery(
        db_session,
        str(delivery.id),
        subscription.target_url,
        delivery.payload,
        str(subscription.id),
        subscription.secret
    )
    
    # Verify delivery status was updated
    await db_session.refresh(delivery)
    assert delivery.status in [models.DeliveryStatus.DELIVERED, models.DeliveryStatus.FAILED]
    assert delivery.last_attempt is not None

@pytest.mark.asyncio
async def test_retry_mechanism(db_session: AsyncSession):
    """Test the retry mechanism for failed deliveries."""
    # Create a test subscription
    subscription = models.Subscription(
        target_url="http://test-server/webhook",
        secret="test-secret",
        event_types=["test_event"],
        created_at=datetime.utcnow()
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # Create a failed delivery
    delivery = models.WebhookDelivery(
        subscription_id=subscription.id,
        event_type="test_event",
        payload={"event": "test"},
        status=models.DeliveryStatus.FAILED,
        retry_count=0,
        created_at=datetime.utcnow()
    )
    db_session.add(delivery)
    await db_session.commit()
    
    # Process retries
    await retry_failed_deliveries(async_session_maker)
    
    # Verify delivery was updated
    await db_session.refresh(delivery)
    assert delivery.retry_count == 1
    assert delivery.status == "pending"

@pytest.mark.asyncio
async def test_cleanup_old_logs(db_session: AsyncSession):
    """Test cleanup of old delivery logs."""
    # Create old delivery and attempt
    old_delivery = models.WebhookDelivery(
        subscription_id=subscription.id,
        event_type="test_event",
        payload={"event": "test"},
        status=models.DeliveryStatus.DELIVERED,
        created_at=datetime.utcnow() - timedelta(days=31)
    )
    db_session.add(old_delivery)
    await db_session.commit()
    
    # Note: DeliveryAttempt model is not defined in the current schema
    # Removing this test case as it's not part of the current model structure
    # Run cleanup
    await cleanup_old_logs(days_to_keep=30)
    
    # Verify old records were deleted
    stmt = select(models.WebhookDelivery).where(
        models.WebhookDelivery.id == old_delivery.id
    )
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_pending_deliveries_processing(db_session: AsyncSession):
    """Test processing of pending deliveries."""
    # Create a test subscription
    subscription = models.Subscription(
        target_url="http://test-server/webhook",
        secret="test-secret",
        event_types=["test_event"],
        created_at=datetime.utcnow()
    )
    db_session.add(subscription)
    await db_session.commit()
    
    # Create multiple pending deliveries
    for i in range(3):
        delivery = models.WebhookDelivery(
            subscription_id=subscription.id,
            event_type="test_event",
            payload={"event": f"test_{i}"},
            status=models.DeliveryStatus.PENDING,
            created_at=datetime.utcnow()
        )
        db_session.add(delivery)
    await db_session.commit()
    
    # Process pending deliveries
    await process_pending_deliveries()
    
    # Verify all deliveries were processed
    stmt = select(models.WebhookDelivery).where(
        models.WebhookDelivery.subscription_id == subscription.id
    )
    result = await db_session.execute(stmt)
    deliveries = result.scalars().all()
    
    for delivery in deliveries:
        assert delivery.status in ['success', 'failed']
        assert delivery.updated_at is not None