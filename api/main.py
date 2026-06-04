"""FastAPI entrypoint for the Store Intelligence API."""

from contextlib import asynccontextmanager

import asyncpg
import structlog
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.database import init_db_pool, close_db_pool
from api.routes import health, metrics, funnel, anomalies, events, heatmap
from api.websocket import router as ws_router
from api.middleware.tracing import CorrelationIdMiddleware
from api.middleware.logging_middleware import RequestLoggingMiddleware, configure_structlog

# ── Constants ────────────────────────────────────────────────────────────────
API_VERSION = "1.0.0"

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
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Exception Handlers ──────────────────────────────────────────────────────

@app.exception_handler(asyncpg.exceptions.PostgresError)
async def db_exception_handler(request: Request, exc: asyncpg.exceptions.PostgresError):
    logger.error("database_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=503,
        content={"error": "Database unavailable", "detail": "The service is currently experiencing degraded performance. Please try again later."}
    )

@app.exception_handler(OSError)
async def os_exception_handler(request: Request, exc: OSError):
    logger.error("connection_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=503,
        content={"error": "Database unavailable", "detail": "Unable to connect to downstream database services. Please try again later."}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("internal_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred."}
    )


# ── Middleware (order matters: outermost first) ──────────────────────────────
origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost"
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
async def read_root():
    return {
        "service": "Store Intelligence API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
