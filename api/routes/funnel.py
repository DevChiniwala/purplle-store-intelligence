from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta, timezone
from api.services.funnel_service import get_conversion_funnel, ConversionFunnel

router = APIRouter()

@router.get("/", response_model=ConversionFunnel)
async def get_funnel(
    store_id: str,
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format. Defaults to today.")
):
    if not target_date:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    start_time = datetime.fromisoformat(f"{target_date}T00:00:00").replace(tzinfo=timezone.utc)
    end_time = (start_time + timedelta(days=1))
    
    return await get_conversion_funnel(
        store_id=store_id,
        start_time=start_time,
        end_time=end_time
    )
