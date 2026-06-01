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
    assert "total_footfall" in data
    assert "store_conversion_rate" in data

@pytest.mark.asyncio
async def test_get_funnel():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/funnel/")
    assert response.status_code == 200
    data = response.json()
    assert "funnel_stages" in data
    assert len(data["funnel_stages"]) > 0

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
    assert data["page"] == 1

@pytest.mark.asyncio
async def test_get_heatmap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/stores/ST1008/heatmap/")
    assert response.status_code == 200
    data = response.json()
    assert "zones" in data
