from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.cost_repository import CostRepository
from app.schemas.cost import CostEventCreate, DashboardMetrics
import logging

logger = logging.getLogger(__name__)

# Model pricing table (per 1M tokens) in microdollars
MODEL_PRICING: Dict[str, Dict[str, int]] = {
    "gpt-4o": {"input": 5_000_000, "output": 15_000_000},
    "gpt-4o-mini": {"input": 150_000, "output": 600_000},
    "gpt-4-turbo": {"input": 10_000_000, "output": 30_000_000},
    "gpt-3.5-turbo": {"input": 500_000, "output": 1_500_000},
    "claude-3-opus-20240229": {"input": 15_000_000, "output": 75_000_000},
    "claude-3-sonnet-20240229": {"input": 3_000_000, "output": 15_000_000},
    "claude-3-haiku-20240307": {"input": 250_000, "output": 1_250_000},
    "gemini-1.5-pro": {"input": 3_500_000, "output": 10_500_000},
    "gemini-1.5-flash": {"input": 350_000, "output": 1_050_000},
    "amazon.titan-text-express-v1": {"input": 800_000, "output": 1_600_000},
}


def calculate_cost(
    model: str, prompt_tokens: int, completion_tokens: int
) -> Dict[str, int]:
    """Calculate cost in microdollars"""
    pricing = MODEL_PRICING.get(model, {"input": 1_000_000, "output": 2_000_000})
    prompt_cost = int((prompt_tokens / 1_000_000) * pricing["input"])
    completion_cost = int((completion_tokens / 1_000_000) * pricing["output"])
    return {
        "prompt_cost_usd_micro": prompt_cost,
        "completion_cost_usd_micro": completion_cost,
        "total_cost_usd_micro": prompt_cost + completion_cost,
    }


class CostService:
    def __init__(self, db: AsyncSession):
        self.repo = CostRepository(db)

    async def record_cost_event(
        self,
        org_id: UUID,
        project_id: UUID,
        event: CostEventCreate,
        team_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> Dict:
        costs = calculate_cost(event.model, event.prompt_tokens, event.completion_tokens)
        event_data = {
            "organization_id": org_id,
            "team_id": team_id,
            "project_id": project_id,
            "user_id": user_id,
            "provider": event.provider.value,
            "model": event.model,
            "prompt_tokens": event.prompt_tokens,
            "completion_tokens": event.completion_tokens,
            "total_tokens": event.prompt_tokens + event.completion_tokens,
            "latency_ms": event.latency_ms,
            "request_id": event.request_id,
            "session_id": event.session_id,
            "environment": event.environment,
            "endpoint": event.endpoint,
            "tags": event.tags,
            "is_streaming": 1 if event.is_streaming else 0,
            **costs,
        }
        created = await self.repo.create(event_data)
        return {
            "id": str(created.id),
            "total_cost_usd": costs["total_cost_usd_micro"] / 1_000_000,
        }

    async def get_dashboard_metrics(self, org_id: UUID) -> DashboardMetrics:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
        prev_month_end = month_start

        current = await self.repo.get_summary(org_id, month_start, now)
        previous = await self.repo.get_summary(org_id, prev_month_start, prev_month_end)

        mom_change = 0.0
        if previous["total_cost_usd"] > 0:
            mom_change = ((current["total_cost_usd"] - previous["total_cost_usd"]) / previous["total_cost_usd"]) * 100

        daily_trend = await self.repo.get_daily_trend(org_id, days=30)
        top_models = await self.repo.get_cost_by_model(org_id, month_start, now)

        return DashboardMetrics(
            current_month_cost_usd=current["total_cost_usd"],
            previous_month_cost_usd=previous["total_cost_usd"],
            mom_change_pct=round(mom_change, 2),
            current_month_tokens=current["total_tokens"],
            current_month_requests=current["total_requests"],
            daily_trend=[
                {"date": d["date"], "cost_usd": d["cost_usd"],
                 "tokens": d["tokens"], "requests": d["requests"]}
                for d in daily_trend
            ],
            top_models=top_models[:10],
            top_teams=[],
            budget_utilization_pct=0.0,
            anomalies_count=0,
            active_alerts_count=0,
        )
