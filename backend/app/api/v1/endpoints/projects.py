from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.db.models.project import Project

router = APIRouter()


@router.get("/")
async def list_projects(org_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.organization_id == org_id))
    projects = result.scalars().all()
    return [{"id": str(p.id), "name": p.name, "slug": p.slug, "api_key": p.api_key} for p in projects]
