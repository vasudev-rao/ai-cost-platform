from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timedelta
from app.core.database import get_db
from app.db.repositories.cost_repository import CostRepository

router = APIRouter()


@router.get("/monthly-summary")
async def monthly_summary(
    org_id: UUID,
    year: int = Query(default=None),
    month: int = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    y = year or now.year
    m = month or now.month
    start = datetime(y, m, 1)
    if m == 12:
        end = datetime(y + 1, 1, 1)
    else:
        end = datetime(y, m + 1, 1)
    
    repo = CostRepository(db)
    summary = await repo.get_summary(org_id, start, end)
    by_model = await repo.get_cost_by_model(org_id, start, end)
    trend = await repo.get_daily_trend(org_id, 31)
    
    return {
        "period": f"{y}-{m:02d}",
        "summary": summary,
        "by_model": by_model,
        "daily_trend": trend,
    }
