"""Funnel service – session-based 5-stage conversion funnel.

Stages:
  1. Entered     – visitor entered the store (has a session)
  2. Engaged     – visitor visited ≥ 2 zones or dwell > 60 s
  3. Interested  – visitor spent time in product / trial zones
  4. Converted   – visitor made a purchase (session.purchased = TRUE)
  5. Repeat      – customer appears in > 1 session in the period
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Optional

import asyncpg
import structlog
from pydantic import BaseModel, Field

from api.database import get_pool

logger = structlog.get_logger(__name__)

PRODUCT_ZONES = {"shelf", "display", "trial", "product", "gondola", "endcap"}


class FunnelStage(BaseModel):
    stage: str
    label: str
    count: int = 0
    percentage: float = Field(0.0, description="Percentage relative to stage-1 (Entered)")


class ConversionFunnel(BaseModel):
    store_id: str
    period_start: dt.datetime
    period_end: dt.datetime
    stages: list[FunnelStage]
    overall_conversion_rate: float = Field(0.0, description="Converted / Entered × 100")


async def get_conversion_funnel(
    store_id: str,
    start_time: dt.datetime,
    end_time: dt.datetime,
    zone_id: Optional[str] = None,
) -> ConversionFunnel:
    """Build a 5-stage conversion funnel for the given store & period."""
    pool: asyncpg.Pool = get_pool()
    log = logger.bind(store_id=store_id)
    log.info("funnel.computing")

    zone_filter = "AND s.zones_visited ? $4" if zone_id else ""
    params: list[Any] = [store_id, start_time, end_time]
    if zone_id:
        params.append(zone_id)

    # Fetch all non-staff sessions in the window
    query = f"""
        SELECT
            s.visitor_id,
            s.dwell_ms,
            s.zones_visited,
            s.purchased,
            s.transaction_id
        FROM sessions s
        WHERE s.store_id = $1
          AND s.entry_time >= $2
          AND s.entry_time <  $3
          AND s.is_staff = FALSE
          {zone_filter}
    """
    rows = await pool.fetch(query, *params)

    entered: set[str] = set()
    engaged: set[str] = set()
    interested: set[str] = set()
    converted: set[str] = set()
    track_session_count: dict[int, int] = {}

    for row in rows:
        vid: str = row["visitor_id"]
        dwell: float = float(row["dwell_ms"] or 0) / 1000.0
        zones: list[str] = row["zones_visited"] if row["zones_visited"] else []
        purchased: bool = row["purchased"] or False

        # Stage 1 – Entered
        entered.add(vid)
        track_session_count[vid] = track_session_count.get(vid, 0) + 1

        # Stage 2 – Engaged (≥2 zones or dwell > 60s)
        if len(zones) >= 2 or dwell > 60:
            engaged.add(sid)

        # Stage 3 – Interested (visited a product zone)
        zone_set = {z.lower() for z in zones}
        if zone_set & PRODUCT_ZONES:
            interested.add(vid)

        # Stage 4 – Converted
        if purchased:
            converted.add(vid)

    # Stage 5 – Repeat (visitor_id appears in > 1 session)
    # Note: In the real world, visitor_id is a re-id token. If they appear more than once in the time period, they are repeat.
    # In our simplified table, visitor_id is the primary key of sessions, so we can't have multiple rows with same visitor_id. 
    # But let's assume the re-id works across sessions if visitor_id was not PK. Since visitor_id is PK, we can just say repeat=0 
    # or if visitor_id maps to something else. We'll leave count from `track_session_count` logic.
    repeat_tracks = {vid for vid, cnt in track_session_count.items() if cnt > 1}
    repeat_sessions: set[str] = set()
    for row in rows:
        if row["visitor_id"] in repeat_tracks:
            repeat_sessions.add(row["visitor_id"])

    total_entered = len(entered)

    def _pct(count: int) -> float:
        return round((count / total_entered * 100) if total_entered else 0.0, 2)

    stages = [
        FunnelStage(stage="entered", label="Entered Store", count=total_entered, percentage=100.0 if total_entered else 0.0),
        FunnelStage(stage="engaged", label="Engaged (≥2 zones / 60s dwell)", count=len(engaged), percentage=_pct(len(engaged))),
        FunnelStage(stage="interested", label="Interested (product zone)", count=len(interested), percentage=_pct(len(interested))),
        FunnelStage(stage="converted", label="Made Purchase", count=len(converted), percentage=_pct(len(converted))),
        FunnelStage(stage="repeat", label="Repeat Visitor", count=len(repeat_sessions), percentage=_pct(len(repeat_sessions))),
    ]

    overall_conversion = _pct(len(converted))
    log.info("funnel.computed", entered=total_entered, converted=len(converted))

    return ConversionFunnel(
        store_id=store_id,
        period_start=start_time,
        period_end=end_time,
        stages=stages,
        overall_conversion_rate=overall_conversion,
    )
