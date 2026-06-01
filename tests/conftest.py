import pytest
import datetime as dt
from unittest.mock import AsyncMock, MagicMock
from api.main import app

@pytest.fixture
def mock_db_pool():
    pool = AsyncMock()
    conn = AsyncMock()
    # Provide a simple way to configure fetchrow / fetch returns
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool, conn

@pytest.fixture
def sample_event_data():
    return {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "event_type": "PERSON_ENTERED",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "camera_id": "CAM_3",
        "track_id": 101,
        "session_id": "sess-abc",
        "zone": "entrance",
        "confidence": 0.95,
        "bbox": [0.0, 0.0, 100.0, 200.0]
    }
