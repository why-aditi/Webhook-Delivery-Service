# Webhook Delivery Service

A robust webhook delivery service that manages, monitors, and delivers webhooks with retry mechanisms and detailed logging.

## Live Application

The application is deployed at: https://webhook-frontend-aghc.onrender.com/

## Features

- **Webhook Management**

  - Create, read, update, and delete webhook subscriptions
  - Configure target URLs and event types
  - Optional webhook secret for signature verification

- **Delivery Monitoring**

  - Real-time delivery status tracking
  - Detailed delivery logs and history
  - Success/failure rate analytics
  - Retry mechanism for failed deliveries

- **Testing Tools**
  - Built-in webhook testing interface
  - Manual webhook triggering
  - Payload customization

## Architecture

### Framework Choices

- **FastAPI**: Chosen for its high performance, automatic API documentation, and excellent async support
- **React**: Selected for the frontend due to its component-based architecture and rich ecosystem
- **PostgreSQL**: Primary database for its reliability, ACID compliance, and JSON support
- **Redis**: Optional caching layer for subscription data and rate limiting
- **AsyncIO**: For handling concurrent webhook deliveries efficiently

### Database Schema

```sql
-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    target_url TEXT NOT NULL,
    event_types TEXT[] NOT NULL,
    secret TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Deliveries table
CREATE TABLE deliveries (
    id UUID PRIMARY KEY,
    subscription_id UUID REFERENCES subscriptions(id),
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Delivery attempts table
CREATE TABLE delivery_attempts (
    id UUID PRIMARY KEY,
    delivery_id UUID REFERENCES deliveries(id),
    status_code INTEGER,
    response_body TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_subscriptions_event_types ON subscriptions USING GIN (event_types);
CREATE INDEX idx_deliveries_subscription_id ON deliveries(subscription_id);
CREATE INDEX idx_deliveries_status ON deliveries(status);
CREATE INDEX idx_delivery_attempts_delivery_id ON delivery_attempts(delivery_id);
```

### Retry Strategy

- Exponential backoff with jitter
- Maximum 5 retry attempts
- Initial retry delay: 1 second
- Maximum retry delay: 30 seconds
- Jitter: ±20% of the delay

## Getting Started

### Docker Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/webhook-delivery-service.git
cd webhook-delivery-service
```

2. Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/webhook_service
REDIS_URL=redis://redis:6379
```

3. Start the services:

```bash
docker-compose up -d
```

4. Access the applications:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Manual Setup

#### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL
- Redis (optional)

#### Backend Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Configure environment variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/webhook_service
```

4. Run the backend:

```bash
uvicorn app.main:app --reload
```

#### Frontend Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Run the development server:

```bash
npm run dev
```

## API Examples

### Subscription Management

```bash
# Create a subscription
curl -X POST http://localhost:8000/subscriptions/ \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com/webhook",
    "event_types": ["user.created", "user.updated"],
    "secret": "your-secret-key"
  }'

# List subscriptions
curl http://localhost:8000/subscriptions/

# Get subscription details
curl http://localhost:8000/subscriptions/{subscription_id}

# Update subscription
curl -X PUT http://localhost:8000/subscriptions/{subscription_id} \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com/new-webhook",
    "event_types": ["user.created"]
  }'

# Delete subscription
curl -X DELETE http://localhost:8000/subscriptions/{subscription_id}
```

### Webhook Delivery

```bash
# Send a webhook
curl -X POST http://localhost:8000/ingest/{subscription_id} \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user.created",
    "data": {
      "user_id": "123",
      "name": "John Doe"
    }
  }'

# Check delivery status
curl http://localhost:8000/deliveries/{delivery_id}

# Get delivery history
curl http://localhost:8000/deliveries/{delivery_id}/history

# Get subscription delivery history
curl http://localhost:8000/subscriptions/{subscription_id}/deliveries
```

## Cost Estimation

### Assumptions

- 5,000 webhooks ingested per day
- Average 1.2 delivery attempts per webhook
- 30 days per month
- 24/7 operation

### Infrastructure Costs (Monthly)

1. **Compute (Vercel - Free Tier)**

   - Frontend: Free (included in hobby plan)
   - Backend: Free (included in hobby plan)

2. **Database (Supabase - Free Tier)**

   - PostgreSQL: Free (500MB included)
   - Estimated storage: ~100MB (assuming 1KB per webhook)
   - Estimated queries: ~180,000/month (within free tier limits)

3. **Redis (Upstash - Free Tier)**
   - Cache: Free (100MB included)
   - Estimated usage: ~50MB (well within limits)

Total Estimated Monthly Cost: $0 (Free tier)

### Traffic Limits

- Vercel: 100GB bandwidth/month
- Supabase: 500MB database, 50,000 rows
- Upstash: 100MB storage, 10,000 commands/day

## Assumptions

1. **Traffic Patterns**

   - Webhooks are evenly distributed throughout the day
   - Peak traffic is 2x average
   - 95% of webhooks are delivered successfully on first attempt

2. **Data Storage**

   - Average webhook payload size: 1KB
   - Delivery logs retained for 30 days
   - Minimal metadata overhead

3. **Performance**
   - Average delivery time: < 1 second
   - Redis cache hit rate: 90%
   - Database query response time: < 50ms

## Credits

- **FastAPI**: Modern, fast web framework for building APIs
- **React**: JavaScript library for building user interfaces
- **Tailwind CSS**: Utility-first CSS framework
- **PostgreSQL**: Powerful, open source object-relational database
- **Redis**: In-memory data structure store
- **Docker**: Containerization platform
- **Vercel**: Deployment platform
- **Supabase**: Backend-as-a-Service platform
- **Upstash**: Serverless Redis provider

## License

This project is licensed under the MIT License - see the LICENSE file for details.
