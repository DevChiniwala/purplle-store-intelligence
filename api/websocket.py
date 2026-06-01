"""WebSocket endpoint for real-time event streaming from Redis."""

import asyncio
import json
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog
import os

router = APIRouter()
logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket.connected", total=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("websocket.disconnected", total=len(self.active_connections))
    
    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.active_connections.remove(conn)


manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """Stream real-time events from Redis to the WebSocket client."""
    await manager.connect(websocket)
    
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    
    try:
        redis = aioredis.from_url(redis_url)
        last_id = "$"  # Only new messages
        
        while True:
            try:
                # Read new messages from the stream
                messages = await redis.xread(
                    streams={"store_events": last_id},
                    count=10,
                    block=2000
                )
                
                if messages:
                    for stream, msg_list in messages:
                        for msg_id, msg_data in msg_list:
                            event = {
                                k.decode("utf-8"): v.decode("utf-8")
                                for k, v in msg_data.items()
                            }
                            await manager.broadcast(event)
                            last_id = msg_id
                            
            except aioredis.ConnectionError:
                logger.warning("websocket.redis_reconnect")
                await asyncio.sleep(2)
                redis = aioredis.from_url(redis_url)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket.error", error=str(e))
        manager.disconnect(websocket)
