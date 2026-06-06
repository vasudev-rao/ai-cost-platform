# Development Guide

## Prerequisites

- Docker Desktop 4.x+
- Node.js 20+
- Python 3.12+
- AWS CLI (for cloud deployment)

## Local Development Setup

```bash
# 1. Clone and configure
git clone https://github.com/vasudev-rao/ai-cost-platform
cd ai-cost-platform
cp .env.example .env

# 2. Start all services
docker-compose up -d

# Wait for health checks
docker-compose ps

# 3. Initialize database
docker-compose exec postgres psql -U postgres -d ai_cost_platform -f /docker-entrypoint-initdb.d/init.sql

# 4. Backend (with hot reload)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 5. Frontend (with hot reload)
cd frontend
npm install
npm run dev

# Access points
# Frontend:    http://localhost:3000
# API:         http://localhost:8000
# API Docs:    http://localhost:8000/docs
# Kafka UI:    http://localhost:8080
# Grafana:     http://localhost:3001 (admin/admin)
# Prometheus:  http://localhost:9090
```

## Testing the SDK

```python
from sdk.python.ai_cost_sdk import AIcostClient, CostEvent

client = AIcostClient(
    api_key="test-key",
    platform_url="http://localhost:8000",
    org_id="00000000-0000-0000-0000-000000000001",
    project_id="test-project",
    disabled=False,
)

# Manually track an event
client.track(CostEvent(
    provider="openai",
    model="gpt-4o",
    prompt_tokens=500,
    completion_tokens=200,
    latency_ms=850,
))
client.shutdown()
print("Event tracked!")
```

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

## Code Style

```bash
# Backend
ruff check .
mypy app/

# Frontend
npm run lint
npm run type-check
```
