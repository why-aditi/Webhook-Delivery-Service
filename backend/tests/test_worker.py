import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio

from app.worker import cleanup_old_logs, process_pending_deliveries, main
from app import models, crud
from app.webhook_processor import process_webhook_delivery, retry_failed_deliveries

@pytest.mark.asyncio
async def test_cleanup_old_logs():
    """Test cleanup of old delivery logs."""
    session = AsyncMock(spec=AsyncSession)
    session_maker = AsyncMock(return_value=session)
    
    # Mock old delivery attempts
    old_attempt = models.DeliveryAttempt(
        id="old-attempt",
        delivery_id="old-delivery",
        created_at=datetime.utcnow() - timedelta(days=31)
    )
    
    # Mock old delivery
    old_delivery = models.Delivery(
        id="old-delivery",
        created_at=datetime.utcnow() - timedelta(days=31)
    )
    
    # Mock database queries
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [old_attempt]
    session.execute.return_value = mock_result
    
    await cleanup_old_logs(days_to_keep=30)
    
    # Verify old records were deleted
    session.delete.assert_called()
    assert session.delete.call_count == 2  # One for attempt, one for delivery
    session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_process_pending_deliveries():
    """Test processing of pending deliveries."""
    session = AsyncMock(spec=AsyncSession)
    session_maker = AsyncMock(return_value=session)
    
    # Mock pending delivery
    pending_delivery = models.Delivery(
        id="pending-delivery",
        status='pending',
        subscription_id="test-sub-id",
        payload={"event": "test"}
    )
    
    # Mock subscription
    subscription = models.Subscription(
        id="test-sub-id",
        target_url="https://example.com/webhook",
        secret="test-secret"
    )
    crud.get_subscription = AsyncMock(return_value=subscription)
    
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [pending_delivery]
    session.execute.return_value = mock_result
    
    # Mock process_webhook_delivery
    with patch('app.webhook_processor.process_webhook_delivery') as mock_process:
        await process_pending_deliveries()
        
        # Verify process_webhook_delivery was called
        mock_process.assert_called_once_with(
            session,
            str(pending_delivery.id),
            str(subscription.target_url),
            pending_delivery.payload,
            str(subscription.id),
            subscription.secret
        )

@pytest.mark.asyncio
async def test_worker_main_loop():
    """Test the main worker loop."""
    # Mock the worker functions
    with patch('app.worker.process_pending_deliveries') as mock_process, \
         patch('app.worker.retry_failed_deliveries') as mock_retry, \
         patch('app.worker.cleanup_old_logs') as mock_cleanup, \
         patch('asyncio.sleep') as mock_sleep:
        
        # Set up the sleep to break the loop after one iteration
        mock_sleep.side_effect = [None, Exception("Break loop")]
        
        # Run the main loop
        with pytest.raises(Exception, match="Break loop"):
            await main()
        
        # Verify functions were called
        mock_process.assert_called_once()
        mock_retry.assert_called_once()
        mock_cleanup.assert_called_once()
        assert mock_sleep.call_count == 2  # Initial sleep and the one that breaks the loop

@pytest.mark.asyncio
async def test_worker_error_handling():
    """Test error handling in the worker loop."""
    # Mock the worker functions to raise an error
    with patch('app.worker.process_pending_deliveries', side_effect=Exception("Test error")), \
         patch('asyncio.sleep') as mock_sleep:
        
        # Set up the sleep to break the loop after one iteration
        mock_sleep.side_effect = [None, Exception("Break loop")]
        
        # Run the main loop
        with pytest.raises(Exception, match="Break loop"):
            await main()
        
        # Verify sleep was called after error
        assert mock_sleep.call_count == 2  # Initial sleep and the one that breaks the loop 