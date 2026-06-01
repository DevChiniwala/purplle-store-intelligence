from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime
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
    
    # 1. Unusual Dwell Time (> 10 mins = 600 seconds)
    dwell_rows = await db.fetch("""
        SELECT session_id, track_id, dwell_seconds, entry_time, zones_visited
        FROM sessions
        WHERE camera_id LIKE $1 || '%' AND dwell_seconds > 600
        ORDER BY dwell_seconds DESC
        LIMIT 5
    """, store_id)
    
    for row in dwell_rows:
        anomalies_list.append(Anomaly(
            anomaly_id=f"ANO-DWELL-{row['session_id'][:8]}",
            type="UNUSUAL_DWELL",
            severity="high" if row['dwell_seconds'] > 1200 else "medium",
            timestamp=row['entry_time'].isoformat() if row['entry_time'] else datetime.utcnow().isoformat(),
            description=f"Person track_{row['track_id']} dwelled for {int(row['dwell_seconds']/60)} minutes.",
            zone="Store-wide",
            track_id=row['track_id']
        ))
        
    # 2. Frequent Visitors (Re-entry) 
    # Let's see if any track_id appears multiple times (if tracking maintains ID across sessions)
    reentry_rows = await db.fetch("""
        SELECT track_id, COUNT(*) as visit_count, MAX(entry_time) as last_visit
        FROM sessions
        WHERE camera_id LIKE $1 || '%'
        GROUP BY track_id
        HAVING COUNT(*) > 2
        LIMIT 5
    """, store_id)
    
    for row in reentry_rows:
        anomalies_list.append(Anomaly(
            anomaly_id=f"ANO-REENTRY-{row['track_id']}",
            type="FREQUENT_REENTRY",
            severity="low",
            timestamp=row['last_visit'].isoformat() if row['last_visit'] else datetime.utcnow().isoformat(),
            description=f"Person track_{row['track_id']} detected {row['visit_count']} times today.",
            zone="Entry",
            track_id=row['track_id']
        ))
        
    # Provide fallback if no dynamic anomalies exist yet
    if not anomalies_list:
        anomalies_list.append(Anomaly(
            anomaly_id="ANO-SYSTEM-001",
            type="SYSTEM_INFO",
            severity="low",
            timestamp=datetime.utcnow().isoformat(),
            description="Monitoring active. No unusual dwell times or frequent re-entries detected yet.",
            zone="System"
        ))

    return AnomaliesResponse(anomalies=anomalies_list)
