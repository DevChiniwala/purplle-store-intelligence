from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from datetime import date
from api.database import get_db_connection
import asyncpg

router = APIRouter()

class HourlyMetrics(BaseModel):
    hour: str
    entries: int
    exits: int
    purchases: int

class MetricsResponse(BaseModel):
    store_id: str
    store_name: str
    date: str
    total_footfall: int
    unique_visitors: int
    customers_purchased: int
    store_conversion_rate: float
    average_dwell_time_minutes: float
    peak_hour: str
    total_revenue: float
    average_basket_size: float
    average_order_value: float
    staff_count: int
    hourly_breakdown: List[HourlyMetrics]

from datetime import datetime, timezone

from api.services.metrics_service import get_store_metrics, StoreMetrics

@router.get("/", response_model=StoreMetrics)
async def get_metrics(
    store_id: str,
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format. Defaults to today."),
):
    if not target_date:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    start_time = datetime.fromisoformat(f"{target_date}T00:00:00").replace(tzinfo=timezone.utc)
    end_time = datetime.fromisoformat(f"{target_date}T23:59:59").replace(tzinfo=timezone.utc)
    
    return await get_store_metrics(
        store_id=store_id,
        start_time=start_time,
        end_time=end_time
    )
