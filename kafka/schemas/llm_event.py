"""Avro-compatible schemas for LLM events"""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class LLMRequestEvent(BaseModel):
    event_id: str
    organization_id: str
    team_id: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    status: str
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    environment: str = "production"
    timestamp: str = ""

    def __init__(self, **data):
        if not data.get("timestamp"):
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)


class LLMCostEvent(LLMRequestEvent):
    prompt_cost_usd_micro: int
    completion_cost_usd_micro: int
    total_cost_usd_micro: int


AVRO_SCHEMA = {
    "type": "record",
    "name": "LLMCostEvent",
    "namespace": "com.aicostplatform",
    "fields": [
        {"name": "event_id", "type": "string"},
        {"name": "organization_id", "type": "string"},
        {"name": "team_id", "type": ["null", "string"], "default": None},
        {"name": "project_id", "type": ["null", "string"], "default": None},
        {"name": "provider", "type": "string"},
        {"name": "model", "type": "string"},
        {"name": "prompt_tokens", "type": "int"},
        {"name": "completion_tokens", "type": "int"},
        {"name": "total_tokens", "type": "int"},
        {"name": "total_cost_usd_micro", "type": "long"},
        {"name": "latency_ms", "type": "int"},
        {"name": "status", "type": "string"},
        {"name": "timestamp", "type": "string"},
    ],
}
