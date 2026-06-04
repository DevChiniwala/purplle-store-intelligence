from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
from api.database import get_db_connection

router = APIRouter()

class Anomaly(BaseModel):
    anomaly_id: str
    type: str
    severity: str
    timestamp: str
    description: str
    zone: str
    track_id: int | None = None

class AnomaliesResponse(BaseModel):
    anomalies: List[Anomaly]

@router.get("/", response_model=AnomaliesResponse)
async def get_anomalies(store_id: str, db = Depends(get_db_connection)):
    anomalies_list = []
    
    # 1. Unusual Dwell Time (> 1 min = 60,000 ms)
    dwell_rows = await db.fetch("""
        SELECT visitor_id, dwell_ms, entry_time, zones_visited
        FROM sessions
        WHERE store_id = $1 AND dwell_ms > 60000
        ORDER BY dwell_ms DESC
        LIMIT 5
    """, store_id)
    
    for row in dwell_rows:
        anomalies_list.append(Anomaly(
            anomaly_id=f"ANO-DWELL-{(row['visitor_id'] or 'unknown')[:8]}",
            type="UNUSUAL_DWELL",
            severity="high" if row['dwell_ms'] > 120000 else "medium",
            timestamp=row['entry_time'].isoformat() if row['entry_time'] else datetime.now(timezone.utc).isoformat(),
            description=f"Person {row['visitor_id']} dwelled for {int(row['dwell_ms']/1000)} seconds.",
            zone="Store-wide",
            track_id=None
        ))
        
    # 2. Frequent Visitors (Re-entry) 
    # Group by visitor_id
    reentry_rows = await db.fetch("""
        SELECT visitor_id, COUNT(*) as visit_count, MAX(entry_time) as last_visit
        FROM sessions
        WHERE store_id = $1
        GROUP BY visitor_id
        HAVING COUNT(*) > 1
        LIMIT 5
    """, store_id)
    
    for row in reentry_rows:
        anomalies_list.append(Anomaly(
            anomaly_id=f"ANO-REENTRY-{(row['visitor_id'] or 'unknown')[:8]}",
            type="FREQUENT_REENTRY",
            severity="low",
            timestamp=row['last_visit'].isoformat() if row['last_visit'] else datetime.now(timezone.utc).isoformat(),
            description=f"Person {row['visitor_id']} detected {row['visit_count']} times.",
            zone="Entry",
            track_id=None
        ))
        
    # Provide fallback if no dynamic anomalies exist yet
    if not anomalies_list:
        anomalies_list.append(Anomaly(
            anomaly_id="ANO-SYSTEM-001",
            type="SYSTEM_INFO",
            severity="low",
            timestamp=datetime.now(timezone.utc).isoformat(),
            description="Monitoring active. No unusual dwell times or frequent re-entries detected yet.",
            zone="System"
        ))

    return AnomaliesResponse(anomalies=anomalies_list)
