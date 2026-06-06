from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.ai.forecast_engine import generate_forecast
from app.db.repositories.cost_repository import CostRepository
from app.db.models.forecast import Forecast
import uuid

router = APIRouter()


@router.post("/generate")
async def generate_cost_forecast(
    org_id: UUID,
    payload: ForecastRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = CostRepository(db)
    historical = await repo.get_historical_daily_costs(org_id, days=90)

    if len(historical) < 7:
        raise HTTPException(status_code=400, detail="Need at least 7 days of data for forecasting")

    result = generate_forecast(historical, payload.horizon.value)

    forecast = Forecast(
        organization_id=org_id,
        team_id=payload.team_id,
        horizon=payload.horizon,
        model_used=result["model_used"],
        forecast_data=result["data_points"],
        total_predicted_usd_micro=int(result["total_predicted_usd"] * 1_000_000),
        confidence_score=result["confidence_score"],
    )
    db.add(forecast)
    await db.flush()

    return {
        "id": str(forecast.id),
        "horizon": payload.horizon.value,
        "model_used": result["model_used"],
        "data_points": result["data_points"],
        "total_predicted_usd": result["total_predicted_usd"],
        "confidence_score": result["confidence_score"],
    }


@router.get("/latest")
async def get_latest_forecast(org_id: UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, desc
    result = await db.execute(
        select(Forecast)
        .where(Forecast.organization_id == org_id)
        .order_by(desc(Forecast.created_at))
        .limit(3)
    )
    forecasts = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "horizon": f.horizon,
            "total_predicted_usd": f.total_predicted_usd_micro / 1_000_000,
            "confidence_score": f.confidence_score,
            "created_at": str(f.created_at),
        }
        for f in forecasts
    ]
