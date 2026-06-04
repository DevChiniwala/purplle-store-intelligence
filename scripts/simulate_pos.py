import asyncio
import asyncpg
import random
import uuid
from datetime import datetime, timezone

import os

async def simulate_pos():
    db_url = os.getenv("DATABASE_URL", "postgresql://admin:admin@localhost:5432/store_intelligence")
    conn = await asyncpg.connect(db_url)
    
    # 1. Find all sessions that visited billing but haven't purchased
    sessions = await conn.fetch("""
        SELECT visitor_id, store_id, exit_time 
        FROM sessions 
        WHERE zones_visited::text ILIKE '%billing%' 
        AND purchased = FALSE
    """)
    
    count = 0
    for s in sessions:
        # Simulate 70% conversion rate for people in billing
        if random.random() < 0.7:
            tx_id = f"TX_{uuid.uuid4().hex[:8]}"
            basket_value = round(random.uniform(500, 3000), 2)
            
            # Insert POS transaction
            await conn.execute("""
                INSERT INTO pos_transactions (store_id, transaction_id, timestamp, basket_value_inr)
                VALUES ($1, $2, $3, $4)
            """, s['store_id'], tx_id, s['exit_time'] or datetime.now(timezone.utc), basket_value)
            
            # Update session
            await conn.execute("""
                UPDATE sessions 
                SET purchased = TRUE, transaction_id = $1 
                WHERE visitor_id = $2
            """, tx_id, s['visitor_id'])
            count += 1
            
    print(f"Simulated {count} POS transactions and purchases.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(simulate_pos())
