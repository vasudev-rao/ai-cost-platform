from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from app.core.database import get_db
from app.schemas.cost import CostEventCreate, CostSummary, DashboardMetrics
from app.services.cost_service import CostService

router = APIRouter()


@router.post("/ingest", status_code=201)
async def ingest_cost_event(
    org_id: UUID,
    project_id: UUID,
    payload: CostEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """Primary ingestion endpoint — called by SDK"""
    service = CostService(db)
    result = await service.record_cost_event(org_id, project_id, payload)
    return {"status": "recorded", **result}


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = CostService(db)
    return await service.get_dashboard_metrics(org_id)


@router.get("/summary")
async def get_cost_summary(
    org_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    team_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    from app.db.repositories.cost_repository import CostRepository
    repo = CostRepository(db)
    end = end_date or datetime.utcnow()
    start = start_date or (end - timedelta(days=30))
    return await repo.get_summary(org_id, start, end, team_id)


@router.get("/by-model")
async def get_cost_by_model(
    org_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    from app.db.repositories.cost_repository import CostRepository
    repo = CostRepository(db)
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return await repo.get_cost_by_model(org_id, start, end)


@router.get("/trend")
async def get_cost_trend(
    org_id: UUID,
    days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    from app.db.repositories.cost_repository import CostRepository
    repo = CostRepository(db)
    return await repo.get_daily_trend(org_id, days)
