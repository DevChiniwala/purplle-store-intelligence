"""Canonical event schema shared across publisher/consumer."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventSchema(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: str
    zone_id: Optional[str] = None
    dwell_ms: Optional[int] = None
    is_staff: bool = False
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
