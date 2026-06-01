"""Database connection pool management using asyncpg."""

import os
import asyncpg
from typing import Optional, AsyncGenerator

# Database connection pool
pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    """Initialize the asyncpg connection pool."""
    global pool
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://admin:admin@postgres:5432/store_intelligence"
    )
    pool = await asyncpg.create_pool(dsn=db_url, min_size=2, max_size=10)


async def close_db_pool():
    """Close the asyncpg connection pool."""
    global pool
    if pool:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    """Return the raw pool for service-layer use (non-dependency-injection)."""
    if pool is None:
        raise RuntimeError("Database pool not initialised — call init_db_pool() first")
    return pool


async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency that yields a connection from the pool."""
    global pool
    if pool is None:
        await init_db_pool()
    async with pool.acquire() as conn:
        yield conn
