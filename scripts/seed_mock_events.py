import asyncio
import asyncpg
import os
import uuid
import datetime as dt
from random import randint, choice, uniform

async def seed_events():
    db_url = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/store_intelligence")
    if "postgres" in db_url and not os.getenv("IN_DOCKER"):
        db_url = "postgresql://admin:admin@localhost:5432/store_intelligence"
    
    conn = await asyncpg.connect(db_url)
    print("Connected to DB, seeding mock CV sessions & events...")
    
    # 1. Clear existing
    await conn.execute("TRUNCATE TABLE events, sessions;")
    
    # 2. Seed Sessions (which funnel/metrics rely on)
    store_id = "ST1008"
    base_time = dt.datetime(2026, 4, 10, 10, 0, tzinfo=dt.timezone.utc)
    
    zones = ["entrance", "makeup", "skincare", "billing", "backroom"]
    
    for i in range(1, 80): # 79 mock sessions
        session_id = f"mock-sess-{i}"
        entry_time = base_time + dt.timedelta(minutes=randint(0, 600))
        dwell = randint(10, 1200)
        exit_time = entry_time + dt.timedelta(seconds=dwell)
        
        # Pick 1-4 random zones
        visited_zones = list(set([choice(zones) for _ in range(randint(1, 4))]))
        
        # Make ~25% convert
        purchased = randint(1, 100) > 75
        
        await conn.execute("""
            INSERT INTO sessions (session_id, track_id, camera_id, entry_time, exit_time, dwell_seconds, zones_visited, purchased, is_staff)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, session_id, i, f"{store_id}_CAM3", entry_time, exit_time, float(dwell), f"[{','.join(chr(34) + z + chr(34) for z in visited_zones)}]", purchased, False)
        
    print("Successfully seeded 79 mock sessions.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_events())
