# PROMPT: Write comprehensive tests for the Store Intelligence API covering ingest idempotency, metric validation, funnel edge cases, and empty store handling.
# CHANGES MADE: Added explicit database mocking and adjusted assertions for timezone-aware datetimes.

import pytest
import datetime as dt
from unittest.mock import patch
from api.services.metrics_service import get_store_metrics
from api.services.funnel_service import get_conversion_funnel

@pytest.mark.asyncio
async def test_empty_store_metrics(mock_db_pool):
    pool, conn = mock_db_pool
    # Return no sessions and no POS rows
    pool.fetchrow.side_effect = [
        None,
        None
    ]
    
    metrics = await get_store_metrics(
        store_id="ST1008",
        start_time=dt.datetime(2026, 4, 10, 0, 0, tzinfo=dt.timezone.utc),
        end_time=dt.datetime(2026, 4, 11, 0, 0, tzinfo=dt.timezone.utc)
    )
    
    assert metrics.footfall == 0
    assert metrics.conversion_rate == 0.0
    assert metrics.revenue == 0.0
    
    pool.fetchrow.side_effect = None

@pytest.mark.asyncio
async def test_empty_store_funnel(mock_db_pool):
    pool, conn = mock_db_pool
    pool.fetch.return_value = []
    
    funnel = await get_conversion_funnel(
        store_id="ST1008",
        start_time=dt.datetime(2026, 4, 10, 0, 0, tzinfo=dt.timezone.utc),
        end_time=dt.datetime(2026, 4, 11, 0, 0, tzinfo=dt.timezone.utc)
    )
    
    assert funnel.stages[0].count == 0
    assert funnel.stages[0].percentage == 0.0

@pytest.mark.asyncio
async def test_all_staff_metrics(mock_db_pool):
    # If all staff, the WHERE is_staff = FALSE query naturally returns 0 rows.
    # The behavior should mirror empty store exactly.
    pool, conn = mock_db_pool
    pool.fetchrow.side_effect = [
        {"total_sessions": 0, "unique_visitors": 0, "avg_dwell_ms": 0, "bounce_count": 0, "purchased_count": 0},
        {"total_revenue": 0, "txn_count": 0}
    ]
    
    metrics = await get_store_metrics(
        store_id="ST1008",
        start_time=dt.datetime(2026, 4, 10, 0, 0, tzinfo=dt.timezone.utc),
        end_time=dt.datetime(2026, 4, 11, 0, 0, tzinfo=dt.timezone.utc)
    )
    
    assert metrics.total_sessions == 0
    assert metrics.footfall == 0
    
    # Reset side effect
    pool.fetchrow.side_effect = None

@pytest.mark.asyncio
async def test_zero_purchases_funnel(mock_db_pool):
    pool, conn = mock_db_pool
    mock_rows = [
        {"visitor_id": "v1", "dwell_ms": 120000, "zones_visited": '["entrance", "skincare", "billing"]', "purchased": False, "transaction_id": None},
    ]
    pool.fetch.return_value = mock_rows
    
    funnel = await get_conversion_funnel(
        store_id="ST1008",
        start_time=dt.datetime(2026, 4, 10, 0, 0, tzinfo=dt.timezone.utc),
        end_time=dt.datetime(2026, 4, 11, 0, 0, tzinfo=dt.timezone.utc)
    )
    
    assert funnel.stages[0].count == 1  # Entered
    assert funnel.stages[3].count == 0  # Converted
    assert funnel.stages[3].percentage == 0.0

@pytest.mark.asyncio
async def test_re_entry_funnel(mock_db_pool):
    pool, conn = mock_db_pool
    # Same visitor enters twice. Should only count as 1 unique visitor in the top funnel stage.
    mock_rows = [
        {"visitor_id": "v_reentry", "dwell_ms": 120000, "zones_visited": '["entrance"]', "purchased": False, "transaction_id": None},
        {"visitor_id": "v_reentry", "dwell_ms": 45000, "zones_visited": '["entrance"]', "purchased": False, "transaction_id": None},
    ]
    pool.fetch.return_value = mock_rows
    
    funnel = await get_conversion_funnel(
        store_id="ST1008",
        start_time=dt.datetime(2026, 4, 10, 0, 0, tzinfo=dt.timezone.utc),
        end_time=dt.datetime(2026, 4, 11, 0, 0, tzinfo=dt.timezone.utc)
    )
    
    assert funnel.stages[0].count == 1  # Unique visitors
    assert funnel.stages[4].count == 1  # Repeat visits count total sessions from repeat visitors
