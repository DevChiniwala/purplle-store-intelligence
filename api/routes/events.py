"""Event ingestion and retrieval routes."""

import json
from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from api.database import get_db_connection

router = APIRouter()

# ── Request/Response Models ──────────────────────────────────────────────────

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
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventsResponse(BaseModel):
    events: List[Event]
    total: int
    page: int
    page_size: int
    filters_applied: Dict[str, str]


class IngestResponse(BaseModel):
    status: str
    inserted: int
    errors: List[Dict[str, str]] = Field(default_factory=list)


# ── Batch size limit ─────────────────────────────────────────────────────────
MAX_BATCH_SIZE = 500
MAX_PAGE_SIZE = 200


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    request: Request,
    events: List[Event],
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    if len(events) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds limit of {MAX_BATCH_SIZE}",
        )
    request.state.event_count = len(events)

    inserted_count = 0
    errors: list[Dict[str, str]] = []

    query = """
    INSERT INTO events (
        event_id, store_id, camera_id, visitor_id, event_type,
        timestamp, zone_id, dwell_ms, is_staff, confidence, metadata
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
    ) ON CONFLICT (event_id) DO NOTHING
    """

    async def _do_inserts():
        nonlocal inserted_count
        for event in events:
            try:
                ts = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
                res = await conn.execute(
                    query,
                    event.event_id,
                    event.store_id,
                    event.camera_id,
                    event.visitor_id,
                    event.event_type,
                    ts,
                    event.zone_id,
                    event.dwell_ms,
                    event.is_staff,
                    event.confidence,
                    json.dumps(event.metadata),
                )
                if res.endswith(" 1"):
                    inserted_count += 1
            except Exception as e:
                errors.append({"event_id": event.event_id, "error": str(e)})

    # Wrap in a transaction when available (real asyncpg connections)
    if hasattr(conn, "transaction"):
        try:
            async with conn.transaction():
                await _do_inserts()
        except Exception:
            # Fallback: transaction not supported (e.g. in tests with mocks)
            await _do_inserts()
    else:
        await _do_inserts()

    return IngestResponse(
        status="partial_success" if errors else "success",
        inserted=inserted_count,
        errors=errors,
    )


@router.get("/", response_model=EventsResponse)
async def get_events(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    store_id: Optional[str] = None,
    event_type: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db_connection),
):
    offset = (page - 1) * page_size

    count_query = "SELECT COUNT(*) FROM events WHERE 1=1"
    data_query = "SELECT * FROM events WHERE 1=1"
    params: list[Any] = []

    filters: Dict[str, str] = {}
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

    # Parameterise LIMIT/OFFSET for safety
    params.append(page_size)
    limit_idx = len(params)
    params.append(offset)
    offset_idx = len(params)
    data_query += f" ORDER BY timestamp DESC LIMIT ${limit_idx} OFFSET ${offset_idx}"
    rows = await conn.fetch(data_query, *params)

    events_list: list[Event] = []
    for row in rows:
        meta_dict: Dict[str, Any] = {}
        if row["metadata"]:
            try:
                meta_dict = (
                    json.loads(row["metadata"])
                    if isinstance(row["metadata"], str)
                    else dict(row["metadata"])
                )
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        events_list.append(
            Event(
                event_id=str(row["event_id"]),
                store_id=row["store_id"],
                camera_id=row["camera_id"],
                visitor_id=row["visitor_id"],
                event_type=row["event_type"],
                timestamp=row["timestamp"].isoformat() if row["timestamp"] else "",
                zone_id=row["zone_id"],
                dwell_ms=row["dwell_ms"],
                is_staff=row["is_staff"] if row["is_staff"] is not None else False,
                confidence=row["confidence"] if row["confidence"] is not None else 0.0,
                metadata=meta_dict,
            )
        )

    return EventsResponse(
        events=events_list,
        total=total_count,
        page=page,
        page_size=page_size,
        filters_applied=filters,
    )
