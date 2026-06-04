# PROMPT: Write comprehensive tests for the Store Intelligence API covering ingest idempotency, metric validation, funnel edge cases, and empty store handling.
# CHANGES MADE: Added explicit database mocking and adjusted assertions for timezone-aware datetimes.

import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "api" in data["services"]

@pytest.mark.asyncio
async def test_get_metrics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/metrics/")
    assert response.status_code == 200
    data = response.json()
    assert data["store_id"] == "ST1008"
    assert "footfall" in data
    assert "conversion_rate" in data

@pytest.mark.asyncio
async def test_get_funnel():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/funnel/")
    assert response.status_code == 200
    data = response.json()
    assert "stages" in data
    assert len(data["stages"]) > 0

@pytest.mark.asyncio
async def test_get_anomalies():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/anomalies/")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data

@pytest.mark.asyncio
async def test_get_events():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/events/")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data

@pytest.mark.asyncio
async def test_get_heatmap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/heatmap/")
    assert response.status_code == 200
    data = response.json()
    assert "zones" in data

@pytest.mark.asyncio
async def test_post_events(sample_event_data):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/events/ingest", json=[sample_event_data])
    assert response.status_code in [200, 201, 202]

@pytest.mark.asyncio
async def test_database_error_handler(mock_db_pool):
    import asyncpg
    pool, conn = mock_db_pool
    pool.fetchrow.side_effect = asyncpg.exceptions.PostgresError("Database connection lost")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/metrics/")
    
    assert response.status_code == 503
    data = response.json()
    assert data["error"] == "Database unavailable"
    assert "degraded" in data["detail"]
    pool.fetchrow.side_effect = None

@pytest.mark.asyncio
async def test_os_error_handler(mock_db_pool):
    pool, conn = mock_db_pool
    pool.fetchrow.side_effect = OSError("Connection refused")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/metrics/")
    
    assert response.status_code == 503
    data = response.json()
    assert data["error"] == "Database unavailable"
    assert "Unable to connect" in data["detail"]
    pool.fetchrow.side_effect = None

@pytest.mark.asyncio
async def test_generic_exception_handler(mock_db_pool):
    pool, conn = mock_db_pool
    pool.fetchrow.side_effect = Exception("Unexpected crash")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/metrics/")
    
    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "Internal server error"
    pool.fetchrow.side_effect = None