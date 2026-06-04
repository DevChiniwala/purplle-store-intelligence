import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.database import init_db_pool, close_db_pool, get_pool, get_db_connection
import api.database as db

@pytest.fixture(autouse=True)
def mock_db_pool():
    # Override conftest.py global autouse fixture so it doesn't patch get_pool
    yield

@pytest.mark.asyncio
async def test_database_lifecycle():
    # Reset module pool state
    db._pool = None
    
    mock_pool = MagicMock()
    mock_pool.close = AsyncMock()
    create_call_count = 0
    async def mock_create_pool(*args, **kwargs):
        nonlocal create_call_count
        create_call_count += 1
        return mock_pool
    
    with patch("asyncpg.create_pool", new=mock_create_pool):
        # First call to init
        await init_db_pool()
        assert create_call_count == 1
        assert db.get_pool() is mock_pool
        
        # Second call to init (should be idempotent)
        await init_db_pool()
        assert create_call_count == 1
        
        # Get connection generator
        conn = AsyncMock()
        acquire_mock = AsyncMock()
        acquire_mock.__aenter__.return_value = conn
        mock_pool.acquire.return_value = acquire_mock
        
        connections = []
        async for c in get_db_connection():
            connections.append(c)
        assert len(connections) == 1
        assert connections[0] is conn
        
        # Close pool
        await close_db_pool()
        mock_pool.close.assert_called_once()
        assert db._pool is None
        
        # Calling get_pool after close should raise RuntimeError
        with pytest.raises(RuntimeError):
            db.get_pool()
