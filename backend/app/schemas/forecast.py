from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import date
from enum import Enum


class ForecastHorizon(str, Enum):
    DAYS_30 = "30d"
    DAYS_90 = "90d"
    DAYS_365 = "365d"


class ForecastDataPoint(BaseModel):
    date: str
    predicted_usd: float
    lower_bound_usd: float
    upper_bound_usd: float


class ForecastRequest(BaseModel):
    horizon: ForecastHorizon = ForecastHorizon.DAYS_30
    team_id: Optional[UUID4] = None
    model_filter: Optional[str] = None


class ForecastResponse(BaseModel):
    id: UUID4
    horizon: str
    model_used: str
    data_points: List[ForecastDataPoint]
    total_predicted_usd: float
    confidence_score: float
    created_at: str

    class Config:
        from_attributes = True
