from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

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
async def get_anomalies(store_id: str):
    return AnomaliesResponse(
        anomalies=[
            Anomaly(
                anomaly_id="ANO-001",
                type="UNUSUAL_DWELL",
                severity="medium",
                timestamp="2026-04-10T15:23:00",
                description="Person track_42 dwelled in Zone C for 45 minutes (3.6x average)",
                zone="Zone C - Skincare",
                track_id=42
            ),
            Anomaly(
                anomaly_id="ANO-002",
                type="FOOTFALL_SPIKE",
                severity="high",
                timestamp="2026-04-10T18:30:00",
                description="Footfall spike: 15 entries in 10 minutes (2.8x hourly average)",
                zone="Entry"
            ),
            Anomaly(
                anomaly_id="ANO-003",
                type="LOW_CONVERSION",
                severity="low",
                timestamp="2026-04-10T14:00:00",
                description="0 purchases in 14:00-15:00 despite 8 visitors",
                zone="Store-wide"
            )
        ]
    )
