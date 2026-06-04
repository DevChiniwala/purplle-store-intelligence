# PROMPT: Write comprehensive tests for the Store Intelligence API covering ingest idempotency, metric validation, funnel edge cases, and empty store handling.
# CHANGES MADE: Added explicit database mocking and adjusted assertions for timezone-aware datetimes.

import pytest
import datetime as dt
from unittest.mock import patch
from api.services.funnel_service import get_conversion_funnel

@pytest.mark.asyncio
async def test_funnel_stages(mock_db_pool):
    pool, conn = mock_db_pool
    # Mocking rows returned from DB for sessions
    mock_rows = [
        {"visitor_id": "v1", "dwell_ms": 120000, "zones_visited": '["entrance", "makeup_wall"]', "purchased": False, "transaction_id": None},
        {"visitor_id": "v2", "dwell_ms": 45000, "zones_visited": '["entrance"]', "purchased": False, "transaction_id": None},
        {"visitor_id": "v3", "dwell_ms": 300000, "zones_visited": '["entrance", "skincare_wall", "billing"]', "purchased": True, "transaction_id": "T1"},
        {"visitor_id": "v3", "dwell_ms": 200000, "zones_visited": '["entrance", "makeup_wall"]', "purchased": False, "transaction_id": None},
    ]
    pool.fetch.return_value = mock_rows

    funnel = await get_conversion_funnel(
        store_id="ST1008",
        start_time=dt.datetime(2026, 4, 10, 0, 0, tzinfo=dt.timezone.utc),
        end_time=dt.datetime(2026, 4, 11, 0, 0, tzinfo=dt.timezone.utc)
    )

    assert funnel.store_id == "ST1008"
    assert len(funnel.stages) == 5
    
    # Entered: v1, v2, v3 (Unique visitors) => count is 3
    assert funnel.stages[0].count == 3
    # Engaged: v1, v3 => count is 2
    assert funnel.stages[1].count == 2
    # Interested (Product zone): v1, v3 => count is 2
    assert funnel.stages[2].count == 2
    # Converted (Purchased): v3 => count is 1
    assert funnel.stages[3].count == 1
