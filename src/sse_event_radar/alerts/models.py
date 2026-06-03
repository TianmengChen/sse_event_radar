from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AlertLevel = Literal["A", "B", "C", "INFO", "RISK"]
AlertDirection = Literal["positive", "negative", "neutral", "uncertain"]


class RelatedStock(BaseModel):
    code: str
    name: str | None = None
    reason: str | None = None
    relevance_score: float | None = Field(default=None, ge=0, le=1)


class Alert(BaseModel):
    level: AlertLevel = "INFO"
    title: str
    summary: str

    direction: AlertDirection = "uncertain"
    market: str = "SSE"
    event_type: str = "unknown"
    time_horizon: str = "unknown"

    source: str | None = None
    source_url: str | None = None

    related_stocks: list[RelatedStock] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)

    confidence: float | None = Field(default=None, ge=0, le=1)
    created_at: datetime = Field(default_factory=datetime.now)