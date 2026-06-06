from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class ForecastHorizon(str, enum.Enum):
    DAYS_30 = "30d"
    DAYS_90 = "90d"
    DAYS_365 = "365d"


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True)
    horizon = Column(Enum(ForecastHorizon), nullable=False)
    model_used = Column(String(50), default="prophet")
    forecast_data = Column(JSON, nullable=False)   # [{date, predicted, lower, upper}]
    total_predicted_usd_micro = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
