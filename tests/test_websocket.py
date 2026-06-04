import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from api.websocket import ConnectionManager, websocket_endpoint

@pytest.mark.asyncio
async def test_connection_manager_success():
    manager = ConnectionManager()
    websocket = AsyncMock(spec=WebSocket)
    
    await manager.connect(websocket)
    websocket.accept.assert_called_once()
    assert websocket in manager.active_connections
    
    await manager.broadcast({"message": "hello"})
    websocket.send_json.assert_called_once_with({"message": "hello"})
    
    manager.disconnect(websocket)
    assert websocket not in manager.active_connections

@pytest.mark.asyncio
async def test_connection_manager_broadcast_dead():
    manager = ConnectionManager()
    websocket_ok = AsyncMock(spec=WebSocket)
    websocket_dead = AsyncMock(spec=WebSocket)
    websocket_dead.send_json.side_effect = Exception("Connection closed")
    
    manager.active_connections.append(websocket_ok)
    manager.active_connections.append(websocket_dead)
    
    await manager.broadcast({"message": "hello"})
    websocket_ok.send_json.assert_called_once()
    websocket_dead.send_json.assert_called_once()
    assert websocket_ok in manager.active_connections
    assert websocket_dead not in manager.active_connections

@pytest.mark.asyncio
async def test_websocket_endpoint_success():
    websocket = AsyncMock(spec=WebSocket)
    mock_redis = AsyncMock()
    
    # xread returns one list of events, then on next loop raises WebSocketDisconnect to stop the infinite loop
    mock_redis.xread.side_effect = [
        [(b"store_events", [(b"1-0", {b"event_id": b"e1", b"store_id": b"s1"})])],
        WebSocketDisconnect()
    ]
    
    with patch("redis.asyncio.from_url", return_value=mock_redis), \
         patch("api.websocket.manager.connect", new_callable=AsyncMock) as mock_connect, \
         patch("api.websocket.manager.disconnect") as mock_disconnect, \
         patch("api.websocket.manager.broadcast", new_callable=AsyncMock) as mock_broadcast:
         
         await websocket_endpoint(websocket)
         mock_connect.assert_called_once_with(websocket)
         mock_broadcast.assert_called_once_with({"event_id": "e1", "store_id": "s1"})
         mock_disconnect.assert_called_once_with(websocket)

@pytest.mark.asyncio
async def test_websocket_endpoint_redis_error_recovery():
    websocket = AsyncMock(spec=WebSocket)
    mock_redis = AsyncMock()
    
    # Raise ConnectionError first, then raise WebSocketDisconnect on next loop
    mock_redis.xread.side_effect = [
        aioredis.ConnectionError("Redis down"),
        WebSocketDisconnect()
    ]
    
    with patch("redis.asyncio.from_url", return_value=mock_redis), \
         patch("api.websocket.manager.connect", new_callable=AsyncMock) as mock_connect, \
         patch("api.websocket.manager.disconnect") as mock_disconnect, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
         
         await websocket_endpoint(websocket)
         mock_connect.assert_called_once_with(websocket)
         mock_sleep.assert_called_once_with(2)
         mock_disconnect.assert_called_once_with(websocket)

@pytest.mark.asyncio
async def test_websocket_endpoint_generic_exception():
    websocket = AsyncMock(spec=WebSocket)
    mock_redis = AsyncMock()
    mock_redis.xread.side_effect = Exception("Fatal error")
    
    with patch("redis.asyncio.from_url", return_value=mock_redis), \
         patch("api.websocket.manager.connect", new_callable=AsyncMock) as mock_connect, \
         patch("api.websocket.manager.disconnect") as mock_disconnect:
         
         await websocket_endpoint(websocket)
         mock_connect.assert_called_once_with(websocket)
         mock_disconnect.assert_called_once_with(websocket)
