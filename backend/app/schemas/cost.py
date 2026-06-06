from pydantic import BaseModel, UUID4, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    SELF_HOSTED = "self_hosted"


class CostEventCreate(BaseModel):
    provider: Provider
    model: str
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    environment: str = "production"
    endpoint: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    is_streaming: bool = False

    @validator("model")
    def model_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Model name cannot be empty")
        return v


class CostEventResponse(BaseModel):
    id: UUID4
    organization_id: UUID4
    team_id: Optional[UUID4]
    project_id: Optional[UUID4]
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost_usd: float  # computed from micro
    latency_ms: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CostSummary(BaseModel):
    total_cost_usd: float
    total_tokens: int
    total_requests: int
    avg_cost_per_request: float
    avg_latency_ms: float
    cost_by_provider: Dict[str, float]
    cost_by_model: Dict[str, float]
    cost_by_team: Dict[str, float]
    period_start: datetime
    period_end: datetime


class CostTrend(BaseModel):
    date: str
    cost_usd: float
    tokens: int
    requests: int


class DashboardMetrics(BaseModel):
    current_month_cost_usd: float
    previous_month_cost_usd: float
    mom_change_pct: float
    current_month_tokens: int
    current_month_requests: int
    daily_trend: List[CostTrend]
    top_models: List[Dict[str, Any]]
    top_teams: List[Dict[str, Any]]
    budget_utilization_pct: float
    anomalies_count: int
    active_alerts_count: int
