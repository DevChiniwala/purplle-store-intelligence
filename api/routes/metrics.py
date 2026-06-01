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

@router.get("/", response_model=MetricsResponse)
async def get_metrics(
    store_id: str,
    target_date: str = "2026-04-10",
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    # This is a mocked logic for now, representing what the analytics engine would compute
    # Normally this would be a complex query joining `events`, `sessions`, and `pos_transactions`
    
    return MetricsResponse(
        store_id=store_id,
        store_name="Brigade_Bangalore",
        date=target_date,
        total_footfall=87,
        unique_visitors=72,
        customers_purchased=19,
        store_conversion_rate=26.39,
        average_dwell_time_minutes=12.4,
        peak_hour="18:00-19:00",
        total_revenue=28547.00,
        average_basket_size=4.21,
        average_order_value=1502.47,
        staff_count=5,
        hourly_breakdown=[
            HourlyMetrics(hour="12:00", entries=8, exits=5, purchases=3),
            HourlyMetrics(hour="13:00", entries=6, exits=7, purchases=2)
        ]
    )
