from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class CostEvent(Base):
    __tablename__ = "cost_events"
    __table_args__ = {
        "postgresql_partition_by": "RANGE (created_at)"
    }

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # LLM metadata
    provider = Column(String(50), nullable=False, index=True)   # openai, anthropic, gemini, bedrock
    model = Column(String(100), nullable=False, index=True)      # gpt-4, claude-3-opus
    model_version = Column(String(50), nullable=True)

    # Token counts
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost in microdollars (avoid float precision issues)
    prompt_cost_usd_micro = Column(Integer, default=0)
    completion_cost_usd_micro = Column(Integer, default=0)
    total_cost_usd_micro = Column(Integer, default=0)

    # Performance
    latency_ms = Column(Integer, default=0)
    first_token_latency_ms = Column(Integer, nullable=True)
    is_streaming = Column(Integer, default=0)

    # Request metadata
    request_id = Column(String(128), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)
    environment = Column(String(50), default="production")
    endpoint = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True)

    # Status
    status = Column(String(50), default="success")  # success, error, cached
    error_code = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    organization = relationship("Organization")
    team = relationship("Team", back_populates="cost_events")
    project = relationship("Project", back_populates="cost_events")
    user = relationship("User", back_populates="cost_events")
