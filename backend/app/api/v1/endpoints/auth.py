from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
)
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse, RefreshRequest
from app.db.models.user import User, UserRole
from app.db.models.organization import Organization
from sqlalchemy import select
import uuid

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    org = None
    if payload.organization_name:
        org = Organization(
            name=payload.organization_name,
            slug=payload.organization_name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8],
        )
        db.add(org)
        await db.flush()

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        organization_id=org.id if org else None,
        role=UserRole.ORG_ADMIN if org else UserRole.DEVELOPER,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token_data = {"sub": str(user.id), "org": str(user.organization_id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=1800,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest):
    claims = verify_token(payload.refresh_token)
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type")
    token_data = {k: v for k, v in claims.items() if k not in ("exp", "type")}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=1800,
    )
