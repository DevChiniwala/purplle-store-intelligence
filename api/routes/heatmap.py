from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

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
async def get_heatmap(store_id: str):
    return HeatmapResponse(
        zones=[
            ZoneStats(zone_id="entry", name="Entrance", visit_count=72, avg_dwell_sec=15),
            ZoneStats(zone_id="makeup", name="Makeup Section", visit_count=45, avg_dwell_sec=480),
            ZoneStats(zone_id="skincare", name="Skincare Section", visit_count=38, avg_dwell_sec=360),
            ZoneStats(zone_id="billing", name="Billing Counter", visit_count=24, avg_dwell_sec=180)
        ],
        time_range=TimeRange(start="12:00:00", end="22:00:00")
    )
