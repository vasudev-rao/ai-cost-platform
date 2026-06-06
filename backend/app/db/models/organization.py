from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True)
    logo_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    monthly_budget_usd = Column(Integer, default=0)  # cents
    plan = Column(String(50), default="free")  # free, starter, growth, enterprise
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")
    projects = relationship("Project", back_populates="organization")
    budgets = relationship("Budget", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
