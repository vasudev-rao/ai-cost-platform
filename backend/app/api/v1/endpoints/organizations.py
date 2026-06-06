from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.db.models.organization import Organization

router = APIRouter()


@router.get("/{org_id}")
async def get_organization(org_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Organization not found")
    return {
        "id": str(org.id), "name": org.name, "slug": org.slug,
        "plan": org.plan, "is_active": org.is_active, "created_at": str(org.created_at),
    }
