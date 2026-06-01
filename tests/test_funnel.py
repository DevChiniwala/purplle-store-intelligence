import pytest
import datetime as dt
from unittest.mock import patch, MagicMock
from api.services.funnel_service import get_conversion_funnel

@pytest.mark.asyncio
async def test_funnel_stages(mock_db_pool):
    pool, conn = mock_db_pool
    # Mocking rows returned from DB for sessions
    mock_rows = [
        {"session_id": "s1", "track_id": 1, "dwell_seconds": 120, "zones_visited": ["entrance", "makeup"], "purchased": False, "customer_number": None},
        {"session_id": "s2", "track_id": 2, "dwell_seconds": 45, "zones_visited": ["entrance"], "purchased": False, "customer_number": None},
        {"session_id": "s3", "track_id": 3, "dwell_seconds": 300, "zones_visited": ["entrance", "skincare", "billing"], "purchased": True, "customer_number": "C123"},
        {"session_id": "s4", "track_id": 3, "dwell_seconds": 200, "zones_visited": ["entrance", "makeup"], "purchased": False, "customer_number": "C123"}, # Repeat visitor
    ]
    pool.fetch.return_value = mock_rows

    with patch("api.services.funnel_service.get_pool", return_value=pool):
        funnel = await get_conversion_funnel(
            store_id="ST1008",
            start_time=dt.datetime(2026, 4, 10, 0, 0, tzinfo=dt.timezone.utc),
            end_time=dt.datetime(2026, 4, 11, 0, 0, tzinfo=dt.timezone.utc)
        )

        assert funnel.store_id == "ST1008"
        assert len(funnel.stages) == 5
        
        # Verify counts
        # Total entered: 4 (s1, s2, s3, s4)
        assert funnel.stages[0].count == 4
        # Engaged (>=2 zones or dwell > 60): s1, s3, s4
        assert funnel.stages[1].count == 3
        # Converted (purchased): s3
        assert funnel.stages[3].count == 1
        # Repeat (track_id 3 appears twice): 2 sessions (s3, s4)
        assert funnel.stages[4].count == 2
        
        # Verify monotonically decreasing percentages (mostly, repeat can vary but typically yes for standard stages)
        assert funnel.stages[0].percentage == 100.0
        assert funnel.stages[1].percentage <= funnel.stages[0].percentage
