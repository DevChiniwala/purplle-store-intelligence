from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class EventSchema(BaseModel):
    event_id: str
    event_type: str  # e.g., "PERSON_ENTERED", "ZONE_TRANSITION", "PERSON_EXITED"
    timestamp: str
    camera_id: str
    track_id: int
    session_id: Optional[str] = None
    zone: str
    previous_zone: Optional[str] = None
    confidence: float
    bbox: BoundingBox
    is_staff: bool = False
    group_id: Optional[str] = None
    dwell_seconds: Optional[float] = None
    metadata: Dict[str, Any] = {}
