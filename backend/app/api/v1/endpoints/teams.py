from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.db.models.team import Team

router = APIRouter()


@router.get("/")
async def list_teams(org_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.organization_id == org_id))
    teams = result.scalars().all()
    return [{"id": str(t.id), "name": t.name, "slug": t.slug} for t in teams]
