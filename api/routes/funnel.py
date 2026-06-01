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

@router.get("/", response_model=FunnelResponse)
async def get_funnel(store_id: str):
    return FunnelResponse(
        funnel_stages=[
            FunnelStage(stage="Entered Store", count=72, percentage=100.0),
            FunnelStage(stage="Browsed Products", count=58, percentage=80.6),
            FunnelStage(stage="Engaged with Staff", count=31, percentage=43.1),
            FunnelStage(stage="Reached Billing", count=24, percentage=33.3),
            FunnelStage(stage="Completed Purchase", count=19, percentage=26.4)
        ],
        drop_off_analysis=[
            DropOff(from_stage="Entered Store", to_stage="Browsed Products", drop_off_pct=19.4),
            DropOff(from_stage="Browsed Products", to_stage="Engaged with Staff", drop_off_pct=46.6),
            DropOff(from_stage="Engaged with Staff", to_stage="Reached Billing", drop_off_pct=22.6),
            DropOff(from_stage="Reached Billing", to_stage="Completed Purchase", drop_off_pct=20.8)
        ]
    )
