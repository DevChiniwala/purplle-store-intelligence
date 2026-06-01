from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncpg
import json
from api.database import get_db_connection

router = APIRouter()

class Event(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    camera_id: str
    track_id: int
    session_id: Optional[str] = None
    zone: Optional[str] = None
    previous_zone: Optional[str] = None
    confidence: float
    bbox: List[float]
    is_staff: bool
    group_id: Optional[str] = None
    dwell_seconds: Optional[float] = None
    metadata: Dict[str, Any]

class EventsResponse(BaseModel):
    events: List[Event]
    total: int
    page: int
    page_size: int
    filters_applied: Dict[str, str]

@router.get("/", response_model=EventsResponse)
async def get_events(
    page: int = 1, 
    page_size: int = 50,
    store_id: Optional[str] = None,
    event_type: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    offset = (page - 1) * page_size
    
    # Base queries
    count_query = "SELECT COUNT(*) FROM events WHERE 1=1"
    data_query = "SELECT * FROM events WHERE 1=1"
    params = []
    
    filters = {}
    if store_id:
        params.append(f"{store_id}%")
        idx = len(params)
        count_query += f" AND camera_id LIKE ${idx}"
        data_query += f" AND camera_id LIKE ${idx}"
        filters["store_id"] = store_id
        
    if event_type:
        params.append(event_type)
        idx = len(params)
        count_query += f" AND event_type = ${idx}"
        data_query += f" AND event_type = ${idx}"
        filters["event_type"] = event_type
        
    # Get total count
    total_count = await conn.fetchval(count_query, *params)
    
    # Get paginated data
    data_query += f" ORDER BY timestamp DESC LIMIT {page_size} OFFSET {offset}"
    rows = await conn.fetch(data_query, *params)
    
    events_list = []
    for row in rows:
        bbox_list = []
        if row['bbox']:
            try:
                # Bbox is stored as JSONB {"x1": 0.1, "y1": 0.1, "x2": 0.2, "y2": 0.5}
                bbox_dict = json.loads(row['bbox']) if isinstance(row['bbox'], str) else row['bbox']
                if 'x1' in bbox_dict:
                    bbox_list = [bbox_dict['x1'], bbox_dict['y1'], bbox_dict['x2'], bbox_dict['y2']]
            except:
                pass
                
        meta_dict = {}
        if row['metadata']:
            try:
                meta_dict = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
            except:
                pass
                
        events_list.append(Event(
            event_id=str(row['event_id']),
            event_type=row['event_type'],
            timestamp=row['timestamp'].isoformat() if row['timestamp'] else "",
            camera_id=row['camera_id'],
            track_id=row['track_id'] if row['track_id'] is not None else 0,
            session_id=row['session_id'],
            zone=row['zone'],
            previous_zone=row['previous_zone'],
            confidence=row['confidence'] if row['confidence'] is not None else 0.0,
            bbox=bbox_list,
            is_staff=row['is_staff'] if row['is_staff'] is not None else False,
            group_id=row['group_id'],
            dwell_seconds=row['dwell_seconds'],
            metadata=meta_dict
        ))
        
    return EventsResponse(
        events=events_list,
        total=total_count,
        page=page,
        page_size=page_size,
        filters_applied=filters
    )
