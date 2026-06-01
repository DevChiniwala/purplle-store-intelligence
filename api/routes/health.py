from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
from api.database import get_db_connection
import asyncpg

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
        
    # In a real app we'd check redis here too
    
    status = "healthy" if all(v == "connected" or v == "running" for v in services.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        services=services
    )
