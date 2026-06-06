from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rec_type = Column(String(50), nullable=False)  # model_switch, prompt_optimization, caching, batching
    current_model = Column(String(100), nullable=True)
    recommended_model = Column(String(100), nullable=True)
    estimated_savings_usd_micro = Column(Integer, default=0)
    estimated_savings_pct = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    evidence = Column(JSON, nullable=True)
    is_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
