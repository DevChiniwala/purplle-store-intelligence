import os
import asyncpg
from typing import Optional

# Database connection pool
pool: Optional[asyncpg.Pool] = None

async def init_db_pool():
    global pool
    db_url = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/store_intelligence")
    pool = await asyncpg.create_pool(dsn=db_url, min_size=2, max_size=10)

async def close_db_pool():
    global pool
    if pool:
        await pool.close()

async def get_db_connection():
    global pool
    if pool is None:
        await init_db_pool()
    async with pool.acquire() as conn:
        yield conn
