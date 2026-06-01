"""FastAPI entrypoint for the Store Intelligence API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
import os

from api.database import init_db_pool, close_db_pool
from api.routes import health, metrics, funnel, anomalies, events, heatmap
from api.websocket import router as ws_router
from api.middleware.tracing import CorrelationIdMiddleware
from api.middleware.logging_middleware import RequestLoggingMiddleware, configure_structlog

# Configure structlog before anything else
configure_structlog()

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("api.startup", message="Starting Store Intelligence API")
    await init_db_pool()
    yield
    # Shutdown
    logger.info("api.shutdown", message="Shutting down API server")
    await close_db_pool()


app = FastAPI(
    title="Store Intelligence API",
    description="AI-powered retail analytics — Purplle Tech Challenge 2026",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters: outermost first) ──────────────────────────────
origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:80"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# ── REST Routers ─────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1/stores/{store_id}/metrics", tags=["metrics"])
app.include_router(funnel.router, prefix="/api/v1/stores/{store_id}/funnel", tags=["funnel"])
app.include_router(anomalies.router, prefix="/api/v1/stores/{store_id}/anomalies", tags=["anomalies"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(heatmap.router, prefix="/api/v1/stores/{store_id}/heatmap", tags=["heatmap"])

# ── WebSocket Router ─────────────────────────────────────────────────────────
app.include_router(ws_router, tags=["websocket"])


@app.get("/", tags=["root"])
def read_root():
    return {
        "service": "Store Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
