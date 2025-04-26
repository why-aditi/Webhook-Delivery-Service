import json
from typing import Optional, Dict, Any
from redis.asyncio import Redis
import os
from dotenv import load_dotenv
from uuid import UUID
from . import models
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Global redis client
redis: Optional[Redis] = None
CACHE_ENABLED = False

# Get Redis configuration from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Default 1 hour TTL

async def init_redis():
    global redis, CACHE_ENABLED
    try:
        redis = Redis(host='localhost', port=6379, decode_responses=True)
        await redis.ping()
        CACHE_ENABLED = True
        logger.info("Redis cache initialized successfully")
    except Exception as e:
        logger.warning(f"Redis cache initialization failed: {e}. Running without cache.")
        CACHE_ENABLED = False
        redis = None

def subscription_cache_key(subscription_id: UUID) -> str:
    """Generate Redis key for subscription cache."""
    return f"subscription:{subscription_id}"

async def cache_subscription(subscription: models.Subscription) -> None:
    """
    Cache subscription details in Redis.
    
    Args:
        subscription: Subscription model instance
    """
    if not CACHE_ENABLED:
        return
    
    try:
        cache_data = {
            "id": str(subscription.id),
            "target_url": subscription.target_url,
            "secret": subscription.secret,
            "event_types": subscription.event_types
        }
        
        await redis.setex(
            subscription_cache_key(subscription.id),
            CACHE_TTL,
            json.dumps(cache_data)
        )
    except Exception as e:
        logger.error(f"Error caching subscription: {e}")

async def get_cached_subscription(subscription_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get subscription details from cache.
    
    Args:
        subscription_id: UUID of the subscription
    
    Returns:
        Dictionary with subscription details if found, None otherwise
    """
    if not CACHE_ENABLED:
        return None
        
    try:
        data = await redis.get(subscription_cache_key(subscription_id))
        if data:
            return json.loads(data)
    except Exception as e:
        logger.error(f"Error getting cached subscription: {e}")
    return None

async def invalidate_subscription_cache(subscription_id: UUID) -> None:
    """
    Remove subscription from cache.
    
    Args:
        subscription_id: UUID of the subscription to remove
    """
    if not CACHE_ENABLED:
        return
        
    try:
        await redis.delete(subscription_cache_key(subscription_id))
    except Exception as e:
        logger.error(f"Error invalidating subscription cache: {e}")

async def close_redis():
    """Close Redis connection."""
    global redis, CACHE_ENABLED
    if redis:
        await redis.close()
        redis = None
    CACHE_ENABLED = False

    logger.info("Redis connection closed") 