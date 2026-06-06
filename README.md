# AI Cost Intelligence Platform

> Enterprise-grade LLM cost monitoring, forecasting, and optimization platform

## Overview

The AI Cost Intelligence Platform provides complete visibility into AI/LLM spending across OpenAI, Anthropic, Gemini, Azure OpenAI, AWS Bedrock, and self-hosted models.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 15 Frontend                       │
│         Dashboard · Analytics · Forecasting · Alerts        │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST / WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                   FastAPI Backend                            │
│      Auth · Costs · Forecasts · Alerts · Recommendations     │
└──────┬──────────────┬──────────────────┬────────────────────┘
       │              │                  │
┌──────▼──────┐ ┌─────▼──────┐ ┌────────▼──────────┐
│  PostgreSQL │ │   Kafka    │ │  Spark Streaming  │
│  (Primary)  │ │  (Events)  │ │  (Delta Lake)     │
└─────────────┘ └────────────┘ └───────────────────┘
```

## Quick Start

```bash
# Clone and start
git clone https://github.com/vasudev-rao/ai-cost-platform
cd ai-cost-platform
cp .env.example .env
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Grafana:  http://localhost:3001
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, TailwindCSS, ShadCN UI, Recharts |
| Backend | FastAPI, Python 3.12, SQLAlchemy, Alembic |
| Streaming | Apache Kafka, Spark Structured Streaming |
| Data Platform | Databricks, Delta Lake |
| Database | PostgreSQL 16 |
| Cloud | AWS (EKS, RDS, S3, MSK) |
| Infrastructure | Terraform, Kubernetes, Helm |
| Monitoring | Prometheus, Grafana, OpenTelemetry |

## Documentation

- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api.md)
- [Data Engineering](docs/data-engineering.md)
- [Deployment Guide](docs/deployment.md)
- [Development Guide](docs/development.md)

## License

MIT License — Copyright 2025 Vasudev Rao
