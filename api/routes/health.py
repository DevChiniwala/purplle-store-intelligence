from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
from api.database import get_db_connection
import asyncpg
import redis.asyncio as aioredis
import os

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]

@router.get("/", response_model=HealthResponse)
async def get_health(conn: asyncpg.Connection = Depends(get_db_connection)):
    services = {
        "api": "running",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check Database
    try:
        await conn.execute("SELECT 1")
        services["database"] = "connected"
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
    
    status = "healthy" if all(v == "connected" or v == "running" for v in services.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        services=services
    )
