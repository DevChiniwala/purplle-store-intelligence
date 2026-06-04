import pytest
import datetime as dt
from unittest.mock import AsyncMock, patch
from api.database import get_db_connection
from api.main import app

@pytest.fixture(autouse=True)
def mock_db_pool():
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    
    # Default valid returns for metric/funnel endpoints
    pool.fetchrow.return_value = {"total_sessions": 10, "unique_visitors": 8, "avg_dwell_ms": 150000, "bounce_count": 2, "purchased_count": 3, "total_revenue": 5000, "txn_count": 3}
    pool.fetch.return_value = []
    
    async def override_get_db_connection():
        yield conn
    
    app.dependency_overrides[get_db_connection] = override_get_db_connection
    
    with patch("api.database.get_pool", return_value=pool), \
         patch("api.main.init_db_pool", return_value=None), \
         patch("api.main.close_db_pool", return_value=None), \
         patch("api.services.metrics_service.get_pool", return_value=pool), \
         patch("api.services.funnel_service.get_pool", return_value=pool):
        yield pool, conn
        
    app.dependency_overrides.clear()

@pytest.fixture
def sample_event_data():
    return {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "event_type": "PERSON_ENTERED",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "camera_id": "CAM_3",
        "store_id": "STORE_001",
        "visitor_id": "VIS_001",
        "zone_id": "entrance",
        "dwell_ms": 12000,
        "is_staff": False,
        "confidence": 0.95,
        "metadata": {}
    }
