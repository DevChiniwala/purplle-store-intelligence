from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class FunnelStage(BaseModel):
    stage: str
    count: int
    percentage: float

class DropOff(BaseModel):
    from_stage: str
    to_stage: str
    drop_off_pct: float

class FunnelResponse(BaseModel):
    funnel_stages: List[FunnelStage]
    drop_off_analysis: List[DropOff]

from datetime import datetime, timezone
from api.services.funnel_service import get_conversion_funnel, ConversionFunnel

@router.get("/", response_model=ConversionFunnel)
async def get_funnel(
    store_id: str,
    target_date: str = "2026-04-10"
):
    start_time = datetime.fromisoformat(f"{target_date}T00:00:00").replace(tzinfo=timezone.utc)
    end_time = datetime.fromisoformat(f"{target_date}T23:59:59").replace(tzinfo=timezone.utc)
    
    return await get_conversion_funnel(
        store_id=store_id,
        start_time=start_time,
        end_time=end_time
    )
