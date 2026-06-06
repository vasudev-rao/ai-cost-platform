from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    organization_name: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID4
    email: str
    full_name: str
    role: str
    organization_id: Optional[UUID4]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
