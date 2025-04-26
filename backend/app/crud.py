from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, delete
from . import models, schemas, cache
from uuid import UUID
from fastapi import HTTPException
from .models import DeliveryStatus
from typing import List

async def list_subscriptions(db: AsyncSession) -> List[models.Subscription]:
    """Get all subscriptions."""
    result = await db.execute(select(models.Subscription))
    return result.scalars().all()

async def create_subscription(db: AsyncSession, subscription: schemas.SubscriptionCreate) -> models.Subscription:
    db_subscription = models.Subscription(
        target_url=str(subscription.target_url),
        secret=subscription.secret,
        event_types=subscription.event_types
    )
    db.add(db_subscription)
    await db.commit()
    await db.refresh(db_subscription)
    
    # Cache the new subscription
    await cache.cache_subscription(db_subscription)
    
    return db_subscription

async def get_subscription(db: AsyncSession, subscription_id: UUID) -> models.Subscription:
    # Try to get from cache first
    cached_data = await cache.get_cached_subscription(subscription_id)
    if cached_data:
        return models.Subscription(**cached_data)
    
    # If not in cache, get from database
    result = await db.execute(
        select(models.Subscription).where(models.Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Cache the subscription for future requests
    await cache.cache_subscription(subscription)
    
    return subscription

async def update_subscription(
    db: AsyncSession, subscription_id: UUID, subscription: schemas.SubscriptionUpdate
) -> models.Subscription:
    db_subscription = await get_subscription(db, subscription_id)
    
    update_data = subscription.model_dump(exclude_unset=True)
    if "target_url" in update_data:
        update_data["target_url"] = str(update_data["target_url"])
    
    for field, value in update_data.items():
        setattr(db_subscription, field, value)
    
    await db.commit()
    await db.refresh(db_subscription)
    
    # Update cache with new data
    await cache.cache_subscription(db_subscription)
    
    return db_subscription

async def delete_subscription(db: AsyncSession, subscription_id: UUID) -> bool:
    """Delete a subscription and all its associated webhook deliveries."""
    # First delete all associated webhook deliveries
    await db.execute(
        delete(models.WebhookDelivery).where(models.WebhookDelivery.subscription_id == subscription_id)
    )
    
    # Then delete the subscription
    db_subscription = await get_subscription(db, subscription_id)
    await db.delete(db_subscription)
    await db.commit()
    
    # Invalidate cache
    await cache.invalidate_subscription_cache(subscription_id)
    
    return True

async def get_delivery(db: AsyncSession, delivery_id: UUID) -> models.WebhookDelivery:
    """Get a webhook delivery by ID."""
    result = await db.execute(
        select(models.WebhookDelivery).where(models.WebhookDelivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery

async def get_delivery_history(db: AsyncSession, delivery_id: UUID) -> schemas.DeliveryHistory:
    """Get the complete history of a webhook delivery including all attempts."""
    # Get all delivery attempts for this delivery ID
    result = await db.execute(
        select(models.WebhookDelivery)
        .where(models.WebhookDelivery.id == delivery_id)
        .order_by(models.WebhookDelivery.created_at)
    )
    attempts = result.scalars().all()
    
    if not attempts:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # Get the latest attempt for current status
    latest_attempt = attempts[-1]
    
    return schemas.DeliveryHistory(
        delivery_id=delivery_id,
        attempts=attempts,
        total_attempts=len(attempts),
        current_status=latest_attempt.status,
        first_attempt=attempts[0].created_at,
        last_attempt=latest_attempt.last_attempt
    )

async def get_subscription_delivery_history(
    db: AsyncSession,
    subscription_id: UUID,
    limit: int = 20
) -> schemas.SubscriptionDeliveryHistory:
    """Get recent delivery attempts for a specific subscription."""
    # Get recent deliveries
    result = await db.execute(
        select(models.WebhookDelivery)
        .where(models.WebhookDelivery.subscription_id == subscription_id)
        .order_by(models.WebhookDelivery.created_at.desc())
        .limit(limit)
    )
    recent_deliveries = result.scalars().all()
    
    if not recent_deliveries:
        raise HTTPException(status_code=404, detail="No deliveries found for this subscription")
    
    # Get total count and success rate
    stats_result = await db.execute(
        select(
            func.count().label("total"),
            func.sum(
                case(
                    (models.WebhookDelivery.status == DeliveryStatus.DELIVERED, 1),
                    else_=0
                )
            ).label("successful")
        )
        .where(models.WebhookDelivery.subscription_id == subscription_id)
    )
    stats = stats_result.first()
    total_count = stats.total
    success_rate = (stats.successful / total_count * 100) if total_count > 0 else 0
    
    return schemas.SubscriptionDeliveryHistory(
        subscription_id=subscription_id,
        recent_deliveries=recent_deliveries,
        total_count=total_count,
        success_rate=success_rate
    ) 