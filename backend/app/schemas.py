from pydantic import BaseModel, HttpUrl, UUID4
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import DeliveryStatus

class SubscriptionBase(BaseModel):
    target_url: HttpUrl
    secret: Optional[str] = None
    event_types: List[str]

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(SubscriptionBase):
    pass

class Subscription(SubscriptionBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WebhookPayload(BaseModel):
    event_type: str
    data: Dict[Any, Any]

class WebhookResponse(BaseModel):
    message: str
    subscription_id: UUID4
    event_type: str
    delivery_id: UUID4

class WebhookDeliveryStatus(BaseModel):
    id: UUID4
    subscription_id: UUID4
    event_type: str
    status: DeliveryStatus
    retry_count: int
    last_attempt: Optional[datetime]
    next_retry: Optional[datetime]
    response_status: Optional[int]
    response_body: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DeliveryAttempt(BaseModel):
    id: UUID4
    subscription_id: UUID4
    event_type: str
    status: DeliveryStatus
    retry_count: int
    last_attempt: Optional[datetime]
    response_status: Optional[int]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DeliveryHistory(BaseModel):
    delivery_id: UUID4
    attempts: List[DeliveryAttempt]
    total_attempts: int
    current_status: DeliveryStatus
    first_attempt: datetime
    last_attempt: Optional[datetime]

class SubscriptionDeliveryHistory(BaseModel):
    subscription_id: UUID4
    recent_deliveries: List[DeliveryAttempt]
    total_count: int
    success_rate: float  # Percentage of successful deliveries 