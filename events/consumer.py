import os
import json
import asyncio
import asyncpg
import redis.asyncio as aioredis
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class EventConsumer:
    def __init__(self, db_url: str, redis_url: str, stream_name: str = "store_events", group_name: str = "analytics"):
        self.db_url = db_url
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = f"consumer_{os.getpid()}"
        
    async def run(self):
        self.redis = aioredis.from_url(self.redis_url)
        self.pool = await asyncpg.create_pool(self.db_url)
        
        try:
            # Create consumer group (ignore if exists)
            await self.redis.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
        except Exception as e:
            logger.info(f"Consumer group may already exist: {e}")
            
        logger.info(f"Started Event Consumer {self.consumer_name}")
        
        while True:
            try:
                # Read from stream
                messages = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={self.stream_name: ">"},
                    count=50,
                    block=2000
                )
                
                if not messages:
                    continue
                    
                for stream, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        # Decode message
                        event = {k.decode('utf-8'): v.decode('utf-8') for k, v in msg_data.items()}
                        await self._process_event(event)
                        # Acknowledge message
                        await self.redis.xack(self.stream_name, self.group_name, msg_id)
                        
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}")
                await asyncio.sleep(2)
                
    async def _process_event(self, event_data: dict):
        async with self.pool.acquire() as conn:
            # 1. Insert Raw Event
            event_type = event_data.get('event_type')
            visitor_id = event_data.get('visitor_id')
            timestamp_str = event_data.get('timestamp')
            is_staff = event_data.get('is_staff', 'False') == 'True'
            zone_id = event_data.get('zone_id')
            store_id = event_data.get('store_id')
            
            await conn.execute("""
                INSERT INTO events (
                    event_id, store_id, camera_id, visitor_id, event_type, 
                    timestamp, zone_id, dwell_ms, is_staff, confidence, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6::timestamptz, $7, $8, $9, $10, $11::jsonb
                )
                ON CONFLICT (event_id) DO NOTHING
            """,
                event_data.get('event_id'), store_id,
                event_data.get('camera_id'), visitor_id,
                event_type, timestamp_str, zone_id,
                int(event_data.get('dwell_ms') or 0),
                is_staff, float(event_data.get('confidence', 0.0)),
                event_data.get('metadata', '{}')
            )
            
            if not visitor_id:
                return

            # 2. Build/Update Session
            if event_type == 'ENTRY':
                await conn.execute("""
                    INSERT INTO sessions (
                        visitor_id, store_id, camera_id, entry_time, is_staff, zones_visited
                    ) VALUES ($1, $2, $3, $4::timestamptz, $5, '[]'::jsonb)
                    ON CONFLICT (visitor_id) DO NOTHING
                """,
                    visitor_id, store_id, event_data.get('camera_id'),
                    timestamp_str, is_staff
                )
                
            elif event_type == 'ZONE_ENTER':
                if zone_id:
                    # Upsert session if it doesn't exist just in case we missed ENTRY
                    await conn.execute("""
                        INSERT INTO sessions (visitor_id, store_id, camera_id, entry_time, zones_visited)
                        VALUES ($1, $2, $3, $4::timestamptz, '[]'::jsonb)
                        ON CONFLICT (visitor_id) DO NOTHING
                    """, visitor_id, store_id, event_data.get('camera_id'), timestamp_str)
                    
                    await conn.execute("""
                        UPDATE sessions 
                        SET zones_visited = zones_visited || $1::jsonb
                        WHERE visitor_id = $2
                    """, json.dumps([zone_id]), visitor_id)
                    
            elif event_type == 'EXIT':
                # Set exit time and calculate dwell_ms
                await conn.execute("""
                    UPDATE sessions 
                    SET exit_time = $1::timestamptz, 
                        dwell_ms = (EXTRACT(EPOCH FROM ($1::timestamptz - entry_time)) * 1000)::int
                    WHERE visitor_id = $2
                """, timestamp_str, visitor_id)
                
                # POS Matching logic
                # If they visited Billing, try to match a POS transaction near their exit time
                row = await conn.fetchrow("SELECT zones_visited, entry_time FROM sessions WHERE visitor_id = $1", visitor_id)
                if row and row['zones_visited']:
                    zones_visited = json.loads(row['zones_visited'])
                    if any('billing' in z.lower() or 'checkout' in z.lower() for z in zones_visited):
                        # Find an unassigned POS transaction within +/- 15 minutes of exit time
                        pos_match = await conn.fetchrow("""
                            SELECT transaction_id FROM pos_transactions 
                            WHERE store_id = $1
                            AND timestamp >= ($2::timestamptz - INTERVAL '15 minutes')
                            AND timestamp <= ($2::timestamptz + INTERVAL '15 minutes')
                            AND transaction_id NOT IN (SELECT transaction_id FROM sessions WHERE transaction_id IS NOT NULL)
                            LIMIT 1
                        """, store_id, timestamp_str)
                        
                        if pos_match:
                            await conn.execute("""
                                UPDATE sessions SET purchased = TRUE, transaction_id = $1 WHERE visitor_id = $2
                            """, pos_match['transaction_id'], visitor_id)
                            logger.info(f"Matched session {visitor_id} to order {pos_match['transaction_id']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_url = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/store_intelligence")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    
    consumer = EventConsumer(db_url, redis_url)
    asyncio.run(consumer.run())
