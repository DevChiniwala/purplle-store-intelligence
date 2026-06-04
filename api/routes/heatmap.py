from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

import json
from api.database import get_db_connection

router = APIRouter()

class ZoneStats(BaseModel):
    zone_id: str
    name: str
    visit_count: int
    avg_dwell_sec: int

class TimeRange(BaseModel):
    start: str
    end: str

class HeatmapResponse(BaseModel):
    zones: List[ZoneStats]
    time_range: TimeRange

@router.get("/", response_model=HeatmapResponse)
async def get_heatmap(store_id: str, db = Depends(get_db_connection)):
    # Calculate zone visits dynamically from sessions
    rows = await db.fetch("""
        SELECT s.zones_visited, s.dwell_ms, s.entry_time 
        FROM sessions s
        WHERE s.store_id = $1
        AND s.is_staff = FALSE
    """, store_id)
    
    zone_counts = {}
    zone_dwells = {}
    
    min_time = None
    max_time = None
    
    for row in rows:
        if row['entry_time']:
            if not min_time or row['entry_time'] < min_time:
                min_time = row['entry_time']
            if not max_time or row['entry_time'] > max_time:
                max_time = row['entry_time']
                
        if row['zones_visited']:
            try:
                zones = json.loads(row['zones_visited'])
                for z in zones:
                    if z not in zone_counts:
                        zone_counts[z] = 0
                        zone_dwells[z] = []
                    zone_counts[z] += 1
                    if row['dwell_ms']:
                        zone_dwells[z].append(row['dwell_ms'] / 1000.0)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
                
    result_zones = []
    for z, count in zone_counts.items():
        avg_dwell = 0
        if len(zone_dwells[z]) > 0:
            # Approx dwell per zone: we divide total session dwell by number of zones visited for simplicity
            # since we don't have per-zone dwell calculated in the db schema natively yet.
            avg_dwell = int(sum(zone_dwells[z]) / len(zone_dwells[z]))
            
        result_zones.append(ZoneStats(
            zone_id=z.lower().replace(" ", "_"),
            name=z,
            visit_count=count,
            avg_dwell_sec=avg_dwell
        ))
        
    start_str = min_time.strftime("%H:%M:%S") if min_time else "00:00:00"
    end_str = max_time.strftime("%H:%M:%S") if max_time else "23:59:59"

    return HeatmapResponse(
        zones=result_zones,
        time_range=TimeRange(start=start_str, end=end_str)
    )
