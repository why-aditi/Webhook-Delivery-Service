import logging
import json
from datetime import datetime
from typing import Any, Dict
import sys

class WebhookDeliveryFormatter(logging.Formatter):
    """Custom formatter for webhook delivery logs with JSON output"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Extract the base log record info
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name
        }
        
        # Add extra fields if they exist
        if hasattr(record, "delivery_data"):
            log_data.update(record.delivery_data)
        
        # Add message
        log_data["message"] = record.getMessage()
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging():
    """Configure logging with both file and console handlers"""
    # Create logger
    logger = logging.getLogger("webhook_service")
    logger.setLevel(logging.INFO)
    
    # Create console handler with a higher log level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(WebhookDeliveryFormatter())
    
    # Create file handler for all logs
    file_handler = logging.FileHandler("logs/webhook_delivery.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(WebhookDeliveryFormatter())
    
    # Create file handler specifically for errors
    error_file_handler = logging.FileHandler("logs/webhook_errors.log")
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(WebhookDeliveryFormatter())
    
    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    
    return logger

def log_delivery_attempt(
    logger: logging.Logger,
    delivery_id: str,
    subscription_id: str,
    target_url: str,
    attempt_number: int,
    status: str,
    response_code: int = None,
    error_details: str = None,
    extra_data: Dict[str, Any] = None
):
    """
    Log a webhook delivery attempt with structured data.
    
    Args:
        logger: Logger instance
        delivery_id: Unique identifier for the delivery
        subscription_id: ID of the subscription
        target_url: Target URL for delivery
        attempt_number: Attempt number (1 for initial, 2+ for retries)
        status: Current status of the delivery
        response_code: HTTP status code if received
        error_details: Error message if failed
        extra_data: Additional data to include in the log
    """
    log_data = {
        "delivery_data": {
            "delivery_id": delivery_id,
            "subscription_id": subscription_id,
            "target_url": target_url,
            "attempt_number": attempt_number,
            "status": status
        }
    }
    
    if response_code is not None:
        log_data["delivery_data"]["response_code"] = response_code
        
    if error_details:
        log_data["delivery_data"]["error_details"] = error_details
        
    if extra_data:
        log_data["delivery_data"].update(extra_data)
    
    # Determine log level based on status
    if status == "delivered":
        logger.info("Webhook delivery successful", extra=log_data)
    elif status == "failed":
        logger.error("Webhook delivery failed", extra=log_data)
    else:
        logger.info(f"Webhook delivery status: {status}", extra=log_data) 