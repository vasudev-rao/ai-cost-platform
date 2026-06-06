# AI Cost Intelligence Platform — Architecture Guide

## System Overview

The AI Cost Intelligence Platform is a multi-tenant, event-driven SaaS platform
for monitoring, forecasting, and optimizing AI/LLM spending.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                    │
│   Web App (Next.js)  │  Python SDK  │  REST API  │  Kafka Producer      │
└────────────┬──────────────────┬──────────────────┬─────────────────────┘
             │                  │                  │
             ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY / INGRESS                           │
│              Nginx Ingress  │  Rate Limiting  │  TLS Termination        │
└─────────────────────────────────────────────────────────────────────────┘
             │                  │
    ┌────────▼────────┐  ┌──────▼───────┐
    │  FastAPI Backend │  │  Kafka MSK   │
    │  (3-20 pods)    │  │  (3 brokers) │
    └────────┬────────┘  └──────┬───────┘
             │                  │
    ┌────────▼────────┐  ┌──────▼───────────────┐
    │  PostgreSQL RDS │  │  Spark Structured     │
    │  (Multi-AZ)     │  │  Streaming (EMR/DBX)  │
    └─────────────────┘  └──────┬───────────────┘
                                │
                     ┌──────────▼──────────┐
                     │    Delta Lake (S3)   │
                     │  Bronze/Silver/Gold  │
                     └─────────────────────┘
```

## Data Flow

### Ingestion Path (Real-Time)
1. Application wraps LLM client with AI Cost SDK
2. SDK sends CostEvent to `/api/v1/costs/ingest` (non-blocking)
3. FastAPI validates, computes cost, writes to PostgreSQL
4. FastAPI publishes to Kafka `llm_costs` topic (async)
5. Kafka consumers trigger alert checks and anomaly detection

### Analytics Path (Batch)
1. Spark Structured Streaming reads from Kafka `llm_costs`
2. Bronze layer: raw events written to Delta Lake (30-day retention)
3. Silver layer: cleaned, deduplicated, enriched with CDC feed
4. Gold layer: daily aggregates by org/team/model (used by API)
5. Optimization engine runs nightly on Gold layer

## Component Diagram

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Frontend    │    │  Forecast    │    │  Anomaly     │
│  Next.js 15  │    │  Engine      │    │  Detector    │
│  Recharts    │    │  Prophet     │    │  Z-score     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────▼───────────────────┘
                           │
                  ┌────────▼────────┐
                  │   FastAPI       │
                  │   Backend       │
                  │   Python 3.12   │
                  └─────┬─────┬────┘
                        │     │
              ┌─────────▼──┐  └──────────┐
              │ PostgreSQL │             │
              │ (Primary   │   ┌─────────▼──┐
              │  Store)    │   │   Kafka    │
              └────────────┘   │  (Events) │
                               └─────┬─────┘
                                     │
                          ┌──────────▼──────────┐
                          │  Spark Streaming    │
                          │  (Databricks/EMR)   │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   Delta Lake (S3)   │
                          │  Bronze/Silver/Gold  │
                          └─────────────────────┘
```

## Multi-Tenancy Model

```
Organization (root tenant)
    ├── Teams (sub-tenants)
    │   ├── Users
    │   └── Projects
    └── Billing / Subscription
```

Row-level isolation enforced at:
- API layer: `organization_id` required on all queries
- PostgreSQL: RLS policies per organization
- Delta Lake: partitioned by `organization_id`
- Kafka: per-organization topics (enterprise plan)

## Security Architecture

```
Internet → WAF (CloudFront) → ALB → Nginx Ingress → Services
                                          │
                                   mTLS between services (Istio)
                                          │
                               JWT validation at API layer
                                          │
                              RBAC (super_admin > org_admin > team_lead > developer > viewer)
```

## Scaling Strategy

| Component | Scaling Trigger | Min | Max |
|-----------|----------------|-----|-----|
| FastAPI   | CPU > 70%      | 3   | 20  |
| Kafka     | Consumer lag   | 3   | 9 brokers |
| Spark     | Queue depth    | 2   | 20 executors |
| RDS       | CPU/Connections| Multi-AZ | Read replicas |

## SLOs

| Metric | Target |
|--------|--------|
| API Availability | 99.9% (43.8 min/month downtime) |
| P50 API Latency | < 100ms |
| P99 API Latency | < 500ms |
| Event Ingestion Lag | < 5 seconds |
| Dashboard Freshness | < 1 minute |
| Forecast Generation | < 30 seconds |
