"""Database connection pool management using asyncpg."""

import asyncio
import os
from typing import AsyncGenerator, Optional

import asyncpg

# ── Module-level state ───────────────────────────────────────────────────────
_pool: Optional[asyncpg.Pool] = None
_pool_lock = asyncio.Lock()

# ── Configuration (env-driven) ───────────────────────────────────────────────
_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin@postgres:5432/store_intelligence",
)
_POOL_MIN = int(os.getenv("DB_POOL_MIN", "2"))
_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))


async def init_db_pool() -> None:
    """Initialize the asyncpg connection pool (idempotent)."""
    global _pool
    async with _pool_lock:
        if _pool is not None:
            return  # already initialised
        _pool = await asyncpg.create_pool(
            dsn=_DB_URL,
            min_size=_POOL_MIN,
            max_size=_POOL_MAX,
            # Supavisor's transaction-mode pooler (required for IPv4 platforms
            # like Vercel) doesn't support prepared statements.
            statement_cache_size=0,
        )


async def close_db_pool() -> None:
    """Close the asyncpg connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """Return the raw pool for service-layer use (non-dependency-injection)."""
    if _pool is None:
        raise RuntimeError("Database pool not initialised — call init_db_pool() first")
    return _pool


async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency that yields a connection from the pool."""
    if _pool is None:
        await init_db_pool()
    async with _pool.acquire() as conn:
        yield conn
