from pydantic import BaseModel, UUID4
from typing import Optional, Dict, Any, List
from datetime import datetime


class RecommendationResponse(BaseModel):
    id: UUID4
    title: str
    description: str
    rec_type: str
    current_model: Optional[str]
    recommended_model: Optional[str]
    estimated_savings_usd: float
    estimated_savings_pct: float
    confidence: float
    evidence: Optional[Dict[str, Any]]
    is_applied: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationApply(BaseModel):
    recommendation_id: UUID4
    notes: Optional[str] = None
