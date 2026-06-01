from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.database import init_db_pool, close_db_pool
import structlog
import os

from api.routes import health, metrics, funnel, anomalies, events, heatmap

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up API server...")
    await init_db_pool()
    yield
    # Shutdown
    logger.info("Shutting down API server...")
    await close_db_pool()

app = FastAPI(
    title="Store Intelligence API",
    description="API for Purplle Tech Challenge 2026 - Store Intelligence System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1/stores/{store_id}/metrics", tags=["metrics"])
app.include_router(funnel.router, prefix="/api/v1/stores/{store_id}/funnel", tags=["funnel"])
app.include_router(anomalies.router, prefix="/api/v1/stores/{store_id}/anomalies", tags=["anomalies"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(heatmap.router, prefix="/api/v1/stores/{store_id}/heatmap", tags=["heatmap"])

@app.get("/")
def read_root():
    return {"message": "Store Intelligence API is running"}
