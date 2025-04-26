import json
from typing import Optional, Dict, Any
from redis import asyncio as aioredis
import os
from dotenv import load_dotenv
from uuid import UUID
from . import models

load_dotenv()

# Get Redis configuration from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Default 1 hour TTL

# Create Redis connection pool
redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

def subscription_cache_key(subscription_id: UUID) -> str:
    """Generate Redis key for subscription cache."""
    return f"subscription:{subscription_id}"

async def cache_subscription(subscription: models.Subscription) -> None:
    """
    Cache subscription details in Redis.
    
    Args:
        subscription: Subscription model instance
    """
    cache_data = {
        "id": str(subscription.id),
        "target_url": subscription.target_url,
        "secret": subscription.secret,
        "event_types": subscription.event_types
    }
    
    key = subscription_cache_key(subscription.id)
    await redis.setex(
        key,
        CACHE_TTL,
        json.dumps(cache_data)
    )

async def get_cached_subscription(subscription_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get subscription details from cache.
    
    Args:
        subscription_id: UUID of the subscription
    
    Returns:
        Dictionary with subscription details if found, None otherwise
    """
    key = subscription_cache_key(subscription_id)
    data = await redis.get(key)
    
    if data:
        return json.loads(data)
    return None

async def invalidate_subscription_cache(subscription_id: UUID) -> None:
    """
    Remove subscription from cache.
    
    Args:
        subscription_id: UUID of the subscription to remove
    """
    key = subscription_cache_key(subscription_id)
    await redis.delete(key)

async def close_redis():
    """Close Redis connection."""
    await redis.close() 