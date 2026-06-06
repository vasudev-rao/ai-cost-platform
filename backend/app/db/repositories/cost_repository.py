from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from app.db.models.cost_event import CostEvent
import logging

logger = logging.getLogger(__name__)


class CostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event_data: dict) -> CostEvent:
        event = CostEvent(**event_data)
        self.db.add(event)
        await self.db.flush()
        return event

    async def bulk_create(self, events: List[dict]) -> int:
        objects = [CostEvent(**e) for e in events]
        self.db.add_all(objects)
        await self.db.flush()
        return len(objects)

    async def get_by_id(self, event_id: UUID) -> Optional[CostEvent]:
        result = await self.db.execute(
            select(CostEvent).where(CostEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_summary(
        self,
        org_id: UUID,
        start_date: datetime,
        end_date: datetime,
        team_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        filters = [
            CostEvent.organization_id == org_id,
            CostEvent.created_at >= start_date,
            CostEvent.created_at <= end_date,
        ]
        if team_id:
            filters.append(CostEvent.team_id == team_id)
        if project_id:
            filters.append(CostEvent.project_id == project_id)

        result = await self.db.execute(
            select(
                func.sum(CostEvent.total_cost_usd_micro).label("total_cost"),
                func.sum(CostEvent.total_tokens).label("total_tokens"),
                func.count(CostEvent.id).label("total_requests"),
                func.avg(CostEvent.latency_ms).label("avg_latency"),
            ).where(and_(*filters))
        )
        row = result.fetchone()
        return {
            "total_cost_usd": (row.total_cost or 0) / 1_000_000,
            "total_tokens": row.total_tokens or 0,
            "total_requests": row.total_requests or 0,
            "avg_latency_ms": float(row.avg_latency or 0),
        }

    async def get_cost_by_model(
        self, org_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        result = await self.db.execute(
            select(
                CostEvent.model,
                CostEvent.provider,
                func.sum(CostEvent.total_cost_usd_micro).label("total_cost"),
                func.sum(CostEvent.total_tokens).label("total_tokens"),
                func.count(CostEvent.id).label("total_requests"),
            )
            .where(
                and_(
                    CostEvent.organization_id == org_id,
                    CostEvent.created_at >= start_date,
                    CostEvent.created_at <= end_date,
                )
            )
            .group_by(CostEvent.model, CostEvent.provider)
            .order_by(func.sum(CostEvent.total_cost_usd_micro).desc())
        )
        return [
            {
                "model": r.model,
                "provider": r.provider,
                "total_cost_usd": r.total_cost / 1_000_000,
                "total_tokens": r.total_tokens,
                "total_requests": r.total_requests,
            }
            for r in result.fetchall()
        ]

    async def get_daily_trend(
        self, org_id: UUID, days: int = 30
    ) -> List[Dict]:
        start_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(
                func.date_trunc("day", CostEvent.created_at).label("day"),
                func.sum(CostEvent.total_cost_usd_micro).label("total_cost"),
                func.sum(CostEvent.total_tokens).label("total_tokens"),
                func.count(CostEvent.id).label("total_requests"),
            )
            .where(
                and_(
                    CostEvent.organization_id == org_id,
                    CostEvent.created_at >= start_date,
                )
            )
            .group_by(text("day"))
            .order_by(text("day"))
        )
        return [
            {
                "date": str(r.day.date()),
                "cost_usd": r.total_cost / 1_000_000,
                "tokens": r.total_tokens,
                "requests": r.total_requests,
            }
            for r in result.fetchall()
        ]

    async def get_historical_daily_costs(
        self, org_id: UUID, days: int = 90
    ) -> List[Dict]:
        """For forecasting model training"""
        return await self.get_daily_trend(org_id, days=days)
