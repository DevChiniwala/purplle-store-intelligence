from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

class Event(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    camera_id: str
    track_id: int
    session_id: str
    zone: str
    previous_zone: str | None = None
    confidence: float
    bbox: List[float]
    is_staff: bool
    group_id: str | None = None
    dwell_seconds: float | None = None
    metadata: Dict[str, Any]

class EventsResponse(BaseModel):
    events: List[Event]
    total: int
    page: int
    page_size: int
    filters_applied: Dict[str, str]

@router.get("/", response_model=EventsResponse)
async def get_events(page: int = 1, page_size: int = 50):
    return EventsResponse(
        events=[
            Event(
                event_id="evt-1234",
                event_type="PERSON_ENTERED",
                timestamp="2026-04-10T12:00:01Z",
                camera_id="CAM_3",
                track_id=1,
                session_id="sess-001",
                zone="inside_entrance",
                confidence=0.88,
                bbox=[0.1, 0.1, 0.2, 0.5],
                is_staff=False,
                metadata={}
            )
        ],
        total=1247,
        page=page,
        page_size=page_size,
        filters_applied={}
    )
