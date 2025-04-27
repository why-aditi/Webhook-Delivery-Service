import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from app.webhook_processor import process_webhook_delivery, retry_failed_deliveries
from app import models, crud

@pytest.mark.asyncio
async def test_process_webhook_delivery_success():
    """Test successful webhook delivery."""
    # Mock session and dependencies
    session = AsyncMock(spec=AsyncSession)
    delivery_id = "test-delivery-id"
    target_url = "https://webhook-test.com/8044fa164b58ffc0f79d3cdd664160eb"
    payload = {"event": "test"}
    subscription_id = "test-sub-id"
    secret = "test-secret"
    
    # Mock the delivery retrieval
    delivery = models.WebhookDelivery(
        id=delivery_id,
        status=models.DeliveryStatus.PENDING,
        subscription_id=subscription_id,
        payload=payload,
        retry_count=0
    )
    crud.get_delivery = AsyncMock(return_value=delivery)
    
    # Mock aiohttp response
    mock_response = AsyncMock(spec=aiohttp.ClientResponse)
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="OK")
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        await process_webhook_delivery(
            session,
            delivery_id,
            target_url,
            payload,
            subscription_id,
            secret
        )
        
        # Verify attempt was created
        session.add.assert_called_once()
        assert isinstance(session.add.call_args[0][0], models.DeliveryAttempt)
        
        # Verify delivery status was updated
        assert delivery.status == models.DeliveryStatus.DELIVERED
        assert delivery.updated_at is not None

@pytest.mark.asyncio
async def test_process_webhook_delivery_failure():
    """Test failed webhook delivery."""
    session = AsyncMock(spec=AsyncSession)
    delivery_id = "test-delivery-id"
    target_url = "https://webhook-test.com/8044fa164b58ffc0f79d3cdd664160eb"
    payload = {"event": "test"}
    subscription_id = "test-sub-id"
    secret = "test-secret"
    
    # Mock the delivery retrieval
    delivery = models.WebhookDelivery(
        id=delivery_id,
        status=models.DeliveryStatus.PENDING,
        subscription_id=subscription_id,
        payload=payload,
        retry_count=0
    )
    crud.get_delivery = AsyncMock(return_value=delivery)
    
    # Mock aiohttp response with error
    mock_response = AsyncMock(spec=aiohttp.ClientResponse)
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Server Error")
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        await process_webhook_delivery(
            session,
            delivery_id,
            target_url,
            payload,
            subscription_id,
            secret
        )
        
        # Verify attempt was created
        session.add.assert_called_once()
        assert isinstance(session.add.call_args[0][0], models.DeliveryAttempt)
        
        # Verify delivery status was updated to failed
        assert delivery.status == models.DeliveryStatus.FAILED
        assert delivery.updated_at is not None

@pytest.mark.asyncio
async def test_retry_failed_deliveries():
    """Test retrying failed deliveries."""
    session = AsyncMock(spec=AsyncSession)
    session_maker = AsyncMock(return_value=session)
    
    # Mock failed deliveries
    failed_delivery = models.WebhookDelivery(
        id="test-delivery-id",
        status=models.DeliveryStatus.FAILED,
        retry_count=0,
        subscription_id="test-sub-id",
        payload={"event": "test"}
    )
    
    # Mock subscription
    subscription = models.Subscription(
        id="test-sub-id",
        target_url="https://webhook-test.com/8044fa164b58ffc0f79d3cdd664160eb",
        secret="test-secret"
    )
    crud.get_subscription = AsyncMock(return_value=subscription)
    
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [failed_delivery]
    session.execute.return_value = mock_result
    
    # Mock process_webhook_delivery
    with patch('app.webhook_processor.process_webhook_delivery') as mock_process:
        await retry_failed_deliveries(session_maker)
        
        # Verify delivery was updated
        assert failed_delivery.retry_count == 1
        assert failed_delivery.status == 'pending'
        assert failed_delivery.updated_at is not None
        
        # Verify process_webhook_delivery was called
        mock_process.assert_called_once_with(
            session,
            str(failed_delivery.id),
            str(subscription.target_url),
            failed_delivery.payload,
            str(subscription.id),
            subscription.secret
        )