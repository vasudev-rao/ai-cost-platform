from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timedelta
from app.core.database import get_db
from app.db.repositories.cost_repository import CostRepository
from app.services.ai.recommendation_engine import generate_recommendations
from app.db.models.recommendation import Recommendation
from sqlalchemy import select, desc

router = APIRouter()


@router.get("/")
async def get_recommendations(org_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.organization_id == org_id, Recommendation.is_applied == False)
        .order_by(desc(Recommendation.estimated_savings_usd_micro))
        .limit(20)
    )
    recs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "description": r.description,
            "rec_type": r.rec_type,
            "current_model": r.current_model,
            "recommended_model": r.recommended_model,
            "estimated_savings_usd": r.estimated_savings_usd_micro / 1_000_000,
            "estimated_savings_pct": r.estimated_savings_pct,
            "confidence": r.confidence,
            "evidence": r.evidence,
        }
        for r in recs
    ]


@router.post("/analyze")
async def analyze_and_generate(org_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = CostRepository(db)
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    
    cost_by_model = await repo.get_cost_by_model(org_id, start, end)
    daily_costs = await repo.get_daily_trend(org_id, 30)
    summary = await repo.get_summary(org_id, start, end)
    
    recs = generate_recommendations(cost_by_model, daily_costs, summary["total_cost_usd"])
    
    created = []
    for rec in recs:
        obj = Recommendation(
            organization_id=org_id,
            title=rec["title"],
            description=rec["description"],
            rec_type=rec["rec_type"],
            current_model=rec["current_model"],
            recommended_model=rec["recommended_model"],
            estimated_savings_usd_micro=int(rec["estimated_savings_usd"] * 1_000_000),
            estimated_savings_pct=rec["estimated_savings_pct"],
            confidence=rec["confidence"],
            evidence=rec["evidence"],
        )
        db.add(obj)
        created.append(rec)
    
    await db.flush()
    return {"generated": len(created), "recommendations": created}
