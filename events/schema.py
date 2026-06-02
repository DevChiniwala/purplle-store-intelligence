from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

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
    metadata: Dict[str, Any] = {}
