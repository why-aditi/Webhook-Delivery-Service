# Webhook Delivery Service

A robust FastAPI-based webhook delivery service that handles subscription management and reliable webhook delivery with advanced features.

## Features

- **Subscription Management**

  - CRUD operations for webhook subscriptions
  - Validation of webhook URLs
  - Support for multiple event types per subscription

- **Reliable Webhook Delivery**

  - Asynchronous webhook processing
  - Retry mechanism with exponential backoff
  - Configurable retry attempts and intervals
  - Automatic handling of failed deliveries

- **Performance Optimizations**

  - Redis-based caching for subscription details
  - Efficient background processing
  - Connection pooling for database operations

- **Monitoring and Logging**
  - Structured logging for all delivery attempts
  - Detailed error tracking
  - Delivery status monitoring
  - Performance metrics

## Tech Stack

- FastAPI - Modern, fast web framework
- PostgreSQL - Primary database
- Redis - Caching layer
- SQLAlchemy - ORM and database toolkit
- Pydantic - Data validation
- httpx - Async HTTP client
- Uvicorn - ASGI server

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize the database:

```bash
alembic upgrade head
```

4. Start the service:

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Subscription Management

- `POST /subscriptions/` - Create a new webhook subscription
- `GET /subscriptions/` - List all subscriptions
- `GET /subscriptions/{subscription_id}` - Get subscription details
- `PUT /subscriptions/{subscription_id}` - Update a subscription
- `DELETE /subscriptions/{subscription_id}` - Delete a subscription

### Webhook Processing

- `POST /webhooks/{event_type}` - Trigger webhook delivery for an event

## Configuration

The service can be configured through environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `MAX_RETRIES` - Maximum number of delivery attempts
- `INITIAL_RETRY_INTERVAL` - Base retry interval in seconds
- `MAX_RETRY_INTERVAL` - Maximum retry interval in seconds
- `WEBHOOK_TIMEOUT` - Timeout for webhook delivery attempts

## Monitoring

The service provides structured logging with the following information:

- Delivery attempt status
- Subscription details
- Response status codes
- Error messages
- Retry counts
- Processing times

## Development

To run tests:

```bash
pytest
```

To run linting:

```bash
flake8
black .
```
