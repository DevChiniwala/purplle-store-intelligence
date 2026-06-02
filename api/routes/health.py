from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from api.database import get_db_connection
import asyncpg
import redis.asyncio as aioredis
import os
from datetime import datetime, timezone, timedelta

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]
    last_event_timestamps: Dict[str, str] = {}
    warnings: list[str] = []

@router.get("/", response_model=HealthResponse)
async def get_health(conn: asyncpg.Connection = Depends(get_db_connection)):
    services = {
        "api": "running",
        "database": "unknown",
        "redis": "unknown"
    }
    
    last_event_timestamps = {}
    warnings = []
    
    # Check Database and Latest Events
    try:
        await conn.execute("SELECT 1")
        services["database"] = "connected"
        
        # Get latest event per store
        rows = await conn.fetch("SELECT store_id, MAX(timestamp) as last_ts FROM events GROUP BY store_id")
        now = datetime.now(timezone.utc)
        
        for row in rows:
            store_id = row['store_id']
            last_ts = row['last_ts']
            
            if last_ts:
                last_event_timestamps[store_id] = last_ts.isoformat()
                if (now - last_ts).total_seconds() > 600:  # 10 minutes
                    warnings.append(f"STALE_FEED: {store_id} has not sent events in over 10 minutes.")
                    
    except Exception as e:
        services["database"] = f"error: {str(e)}"
        
    # Check Redis
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    try:
        r = aioredis.from_url(redis_url)
        await r.ping()
        services["redis"] = "connected"
        await r.aclose()
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
    
    status = "healthy" if all(v == "connected" or v == "running" for v in services.values()) and not warnings else "degraded"
    
    return HealthResponse(
        status=status,
        services=services,
        last_event_timestamps=last_event_timestamps,
        warnings=warnings
    )
