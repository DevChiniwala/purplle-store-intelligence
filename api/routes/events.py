from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncpg
import json
from datetime import datetime
from api.database import get_db_connection

router = APIRouter()

class Event(BaseModel):
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

class EventsResponse(BaseModel):
    events: List[Event]
    total: int
    page: int
    page_size: int
    filters_applied: Dict[str, str]

class IngestResponse(BaseModel):
    status: str
    inserted: int
    errors: List[Dict[str, str]] = []

@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    events: List[Event],
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    if len(events) > 500:
        raise HTTPException(status_code=400, detail="Batch size exceeds limit of 500")
        
    inserted_count = 0
    errors = []
    
    query = """
    INSERT INTO events (
        event_id, store_id, camera_id, visitor_id, event_type, 
        timestamp, zone_id, dwell_ms, is_staff, confidence, metadata
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
    ) ON CONFLICT (event_id) DO NOTHING
    """
    
    for event in events:
        try:
            ts = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
            res = await conn.execute(
                query,
                event.event_id, event.store_id, event.camera_id, event.visitor_id,
                event.event_type, ts, event.zone_id, event.dwell_ms,
                event.is_staff, event.confidence, json.dumps(event.metadata)
            )
            if res.endswith(" 1"):
                inserted_count += 1
        except Exception as e:
            errors.append({"event_id": event.event_id, "error": str(e)})
            
    return IngestResponse(status="partial_success" if errors else "success", inserted=inserted_count, errors=errors)


@router.get("/", response_model=EventsResponse)
async def get_events(
    page: int = 1, 
    page_size: int = 50,
    store_id: Optional[str] = None,
    event_type: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    offset = (page - 1) * page_size
    
    count_query = "SELECT COUNT(*) FROM events WHERE 1=1"
    data_query = "SELECT * FROM events WHERE 1=1"
    params = []
    
    filters = {}
    if store_id:
        params.append(store_id)
        idx = len(params)
        count_query += f" AND store_id = ${idx}"
        data_query += f" AND store_id = ${idx}"
        filters["store_id"] = store_id
        
    if event_type:
        params.append(event_type)
        idx = len(params)
        count_query += f" AND event_type = ${idx}"
        data_query += f" AND event_type = ${idx}"
        filters["event_type"] = event_type
        
    total_count = await conn.fetchval(count_query, *params)
    
    data_query += f" ORDER BY timestamp DESC LIMIT {page_size} OFFSET {offset}"
    rows = await conn.fetch(data_query, *params)
    
    events_list = []
    for row in rows:
        meta_dict = {}
        if row['metadata']:
            try:
                meta_dict = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
            except:
                pass
                
        events_list.append(Event(
            event_id=str(row['event_id']),
            store_id=row['store_id'],
            camera_id=row['camera_id'],
            visitor_id=row['visitor_id'],
            event_type=row['event_type'],
            timestamp=row['timestamp'].isoformat() if row['timestamp'] else "",
            zone_id=row['zone_id'],
            dwell_ms=row['dwell_ms'],
            is_staff=row['is_staff'] if row['is_staff'] is not None else False,
            confidence=row['confidence'] if row['confidence'] is not None else 0.0,
            metadata=meta_dict
        ))
        
    return EventsResponse(
        events=events_list,
        total=total_count,
        page=page,
        page_size=page_size,
        filters_applied=filters
    )
