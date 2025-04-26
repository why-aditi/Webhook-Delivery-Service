from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from . import crud, models, schemas, cache
from .database import engine, get_session, async_session_maker
from uuid import UUID
from .webhook_processor import process_webhook_delivery, create_delivery_record, retry_failed_deliveries
import asyncio

app = FastAPI(title="Webhook Delivery Service")

@app.on_event("startup")
async def startup():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    
    # Start background task for retrying failed deliveries
    asyncio.create_task(retry_failed_deliveries(async_session_maker))

@app.on_event("shutdown")
async def shutdown():
    # Close Redis connection
    await cache.close_redis()

@app.post("/subscriptions/", response_model=schemas.Subscription)
async def create_subscription(
    subscription: schemas.SubscriptionCreate,
    db: AsyncSession = Depends(get_session)
):
    """Create a new webhook subscription"""
    return await crud.create_subscription(db=db, subscription=subscription)

@app.get("/subscriptions/{subscription_id}", response_model=schemas.Subscription)
async def read_subscription(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """Get a specific subscription by ID"""
    return await crud.get_subscription(db=db, subscription_id=subscription_id)

@app.put("/subscriptions/{subscription_id}", response_model=schemas.Subscription)
async def update_subscription(
    subscription_id: UUID,
    subscription: schemas.SubscriptionUpdate,
    db: AsyncSession = Depends(get_session)
):
    """Update a subscription"""
    return await crud.update_subscription(
        db=db,
        subscription_id=subscription_id,
        subscription=subscription
    )

@app.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """Delete a subscription"""
    await crud.delete_subscription(db=db, subscription_id=subscription_id)
    return {"message": "Subscription deleted successfully"}

@app.post("/ingest/{subscription_id}", response_model=schemas.WebhookResponse, status_code=202)
async def ingest_webhook(
    subscription_id: UUID,
    payload: schemas.WebhookPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Ingest a webhook payload for delivery.
    Returns 202 Accepted response immediately and processes the webhook asynchronously.
    """
    # Verify subscription exists and get details
    subscription = await crud.get_subscription(db=db, subscription_id=subscription_id)
    
    # Verify event type is allowed for this subscription
    if payload.event_type not in subscription.event_types:
        raise HTTPException(
            status_code=400,
            detail=f"Event type '{payload.event_type}' not allowed for this subscription"
        )
    
    # Create delivery record
    delivery = await create_delivery_record(
        db=db,
        subscription_id=str(subscription_id),
        event_type=payload.event_type,
        payload=payload.data
    )
    
    # Queue the webhook delivery as a background task
    background_tasks.add_task(
        process_webhook_delivery,
        db=db,
        delivery_id=str(delivery.id),
        target_url=str(subscription.target_url),
        payload=payload.data,
        subscription_id=str(subscription_id),
        secret=subscription.secret
    )
    
    return {
        "message": "Webhook accepted for delivery",
        "subscription_id": subscription_id,
        "event_type": payload.event_type,
        "delivery_id": delivery.id  # Add delivery ID to response
    }

@app.get("/deliveries/{delivery_id}", response_model=schemas.WebhookDeliveryStatus)
async def get_delivery_status(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """Get the status of a webhook delivery"""
    return await crud.get_delivery(db=db, delivery_id=delivery_id)

@app.get("/deliveries/{delivery_id}/history", response_model=schemas.DeliveryHistory)
async def get_delivery_history(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    """
    Get the complete history of a webhook delivery including all attempts.
    This endpoint provides detailed information about all attempts made for a specific delivery.
    """
    return await crud.get_delivery_history(db=db, delivery_id=delivery_id)

@app.get("/subscriptions/{subscription_id}/deliveries", response_model=schemas.SubscriptionDeliveryHistory)
async def get_subscription_delivery_history(
    subscription_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session)
):
    """
    Get recent delivery attempts for a specific subscription.
    This endpoint provides analytics about recent deliveries including success rate.
    
    Parameters:
    - limit: Number of recent deliveries to return (default: 20, max: 100)
    """
    return await crud.get_subscription_delivery_history(
        db=db,
        subscription_id=subscription_id,
        limit=limit
    ) 