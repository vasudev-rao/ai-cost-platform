from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from app.core.database import get_db
from app.db.models.alert import Alert

router = APIRouter()


@router.get("/")
async def list_alerts(
    org_id: UUID,
    unresolved_only: bool = Query(default=True),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Alert).where(Alert.organization_id == org_id)
    if unresolved_only:
        query = query.where(Alert.is_resolved == False)
    query = query.order_by(desc(Alert.created_at)).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "is_resolved": a.is_resolved,
            "created_at": str(a.created_at),
        }
        for a in alerts
    ]


@router.patch("/{alert_id}/resolve")
async def resolve_alert(alert_id: UUID, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    await db.flush()
    return {"status": "resolved"}
