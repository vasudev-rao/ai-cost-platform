from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class AlertType(str, enum.Enum):
    BUDGET_THRESHOLD = "budget_threshold"
    COST_SPIKE = "cost_spike"
    ANOMALY = "anomaly"
    USAGE_LIMIT = "usage_limit"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    metadata = Column(JSON, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    notification_channels = Column(JSON, default=["email"])  # email, slack, webhook
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
