"""Metrics service – computes store KPIs from events and POS data."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, Optional

import asyncpg
import structlog
from pydantic import BaseModel, Field

from api.database import get_pool

logger = structlog.get_logger(__name__)


# ── Pydantic response models ───────────────────────────────────────────────

class HourlyBreakdown(BaseModel):
    hour: int = Field(..., ge=0, le=23, description="Hour of the day (0-23)")
    footfall: int = Field(0, description="Number of unique visitors in this hour")
    revenue: Decimal = Field(Decimal("0"), description="Revenue generated in this hour")
    transactions: int = Field(0, description="Number of transactions in this hour")


class StoreMetrics(BaseModel):
    store_id: str
    store_name: str
    period_start: dt.datetime
    period_end: dt.datetime
    footfall: int = Field(0, description="Total unique non-staff visitors")
    total_sessions: int = Field(0, description="Total visitor sessions")
    conversion_rate: float = Field(0.0, description="Percentage of sessions that purchased")
    revenue: Decimal = Field(Decimal("0"), description="Total NMV revenue")
    gmv: Decimal = Field(Decimal("0"), description="Total GMV")
    average_transaction_value: Decimal = Field(Decimal("0"), description="Revenue / transactions")
    transactions: int = Field(0, description="Number of POS transactions")
    average_dwell_seconds: float = Field(0.0, description="Mean dwell time in seconds")
    bounce_rate: float = Field(0.0, description="Percentage of sessions with dwell < 30s")
    hourly_breakdown: list[HourlyBreakdown] = Field(default_factory=list)


# ── Service layer ───────────────────────────────────────────────────────────

async def get_store_metrics(
    store_id: str,
    start_time: dt.datetime,
    end_time: dt.datetime,
    granularity: str = "hourly",
    zone_id: Optional[str] = None,
) -> StoreMetrics:
    """Compute aggregate KPIs for *store_id* in the given time window."""
    pool: asyncpg.Pool = get_pool()
    log = logger.bind(store_id=store_id, start=str(start_time), end=str(end_time))
    log.info("metrics.computing")

    # ── Footfall & sessions ──────────────────────────────────────────────
    zone_filter = "AND s.zones_visited ? $4" if zone_id else ""
    session_query = f"""
        SELECT
            COUNT(*)                                             AS total_sessions,
            COUNT(DISTINCT s.visitor_id)                         AS unique_visitors,
            COALESCE(AVG(s.dwell_ms), 0)                         AS avg_dwell_ms,
            COUNT(*) FILTER (WHERE s.dwell_ms < 30000)           AS bounce_count,
            COUNT(*) FILTER (WHERE s.purchased = TRUE)           AS purchased_count
        FROM sessions s
        WHERE s.store_id = $1
          AND s.entry_time >= $2
          AND s.entry_time <  $3
          AND s.is_staff = FALSE
          {zone_filter}
    """
    params: list[Any] = [store_id, start_time, end_time]
    if zone_id:
        params.append(zone_id)

    row = await pool.fetchrow(session_query, *params)

    total_sessions: int = row["total_sessions"] if row else 0
    unique_visitors: int = row["unique_visitors"] if row else 0
    avg_dwell_ms: float = float(row["avg_dwell_ms"]) if row else 0.0
    avg_dwell = avg_dwell_ms / 1000.0
    bounce_count: int = row["bounce_count"] if row else 0
    purchased_count: int = row["purchased_count"] if row else 0

    conversion_rate = round((purchased_count / total_sessions * 100) if total_sessions else 0.0, 2)
    bounce_rate = round((bounce_count / total_sessions * 100) if total_sessions else 0.0, 2)

    # ── POS revenue ──────────────────────────────────────────────────────
    pos_query = """
        SELECT
            COALESCE(SUM(basket_value_inr), 0) AS total_revenue,
            COUNT(DISTINCT transaction_id)     AS txn_count
        FROM pos_transactions
        WHERE store_id = $1
          AND timestamp >= $2
          AND timestamp < $3
    """
    pos_row = await pool.fetchrow(pos_query, store_id, start_time, end_time)
    
    if pos_row and pos_row.get("total_revenue") is not None:
        revenue = Decimal(str(pos_row["total_revenue"]))
    else:
        revenue = Decimal("0")
        
    gmv = revenue  # simplified for new schema
    txn_count: int = pos_row["txn_count"] if pos_row else 0
    atv = round(revenue / txn_count, 2) if txn_count else Decimal("0")

    # ── Hourly breakdown ─────────────────────────────────────────────────
    hourly_footfall_query = f"""
        SELECT
            EXTRACT(HOUR FROM s.entry_time)::int AS hour,
            COUNT(DISTINCT s.visitor_id)         AS footfall
        FROM sessions s
        WHERE s.store_id = $1
          AND s.entry_time >= $2
          AND s.entry_time <  $3
          AND s.is_staff = FALSE
          {zone_filter}
        GROUP BY 1
        ORDER BY 1
    """
    hourly_revenue_query = """
        SELECT
            EXTRACT(HOUR FROM timestamp)::int   AS hour,
            COALESCE(SUM(basket_value_inr), 0)  AS revenue,
            COUNT(DISTINCT transaction_id)      AS transactions
        FROM pos_transactions
        WHERE store_id = $1
          AND timestamp >= $2
          AND timestamp < $3
        GROUP BY 1
        ORDER BY 1
    """

    footfall_rows = await pool.fetch(hourly_footfall_query, *params)
    revenue_rows = await pool.fetch(hourly_revenue_query, store_id, start_time, end_time)

    footfall_map: dict[int, int] = {r["hour"]: r["footfall"] for r in footfall_rows}
    revenue_map: dict[int, dict[str, Any]] = {
        r["hour"]: {"revenue": Decimal(str(r["revenue"])), "transactions": r["transactions"]}
        for r in revenue_rows
    }

    hourly: list[HourlyBreakdown] = []
    for h in range(24):
        hourly.append(
            HourlyBreakdown(
                hour=h,
                footfall=footfall_map.get(h, 0),
                revenue=revenue_map.get(h, {}).get("revenue", Decimal("0")),
                transactions=revenue_map.get(h, {}).get("transactions", 0),
            )
        )

    store_name = await _resolve_store_name(pool, store_id)
    log.info("metrics.computed", footfall=unique_visitors, revenue=str(revenue))

    return StoreMetrics(
        store_id=store_id,
        store_name=store_name,
        period_start=start_time,
        period_end=end_time,
        footfall=unique_visitors,
        total_sessions=total_sessions,
        conversion_rate=conversion_rate,
        revenue=revenue,
        gmv=gmv,
        average_transaction_value=atv,
        transactions=txn_count,
        average_dwell_seconds=round(avg_dwell, 2),
        bounce_rate=bounce_rate,
        hourly_breakdown=hourly,
    )


async def _resolve_store_name(pool: asyncpg.Pool, store_id: str) -> str:
    """Look up the store name from POS data, fall back to store_id."""
    return store_id  # Store name is no longer in pos_transactions
