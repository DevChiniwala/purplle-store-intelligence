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
            bbox_str = event_data.get('bbox', '{}').replace("'", '"') 
            event_type = event_data.get('event_type')
            session_id = event_data.get('session_id')
            timestamp_str = event_data.get('timestamp')
            is_staff = event_data.get('is_staff', 'False') == 'True'
            zone = event_data.get('zone')
            
            await conn.execute("""
                INSERT INTO events (
                    event_id, event_type, timestamp, camera_id, track_id, 
                    session_id, zone, previous_zone, confidence, bbox, 
                    is_staff, group_id, metadata
                ) VALUES (
                    $1, $2, $3::timestamptz, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12, $13::jsonb
                )
                ON CONFLICT (event_id) DO NOTHING
            """,
                event_data.get('event_id'), event_type, timestamp_str,
                event_data.get('camera_id'), int(event_data.get('track_id', 0)),
                session_id, zone, event_data.get('previous_zone'),
                float(event_data.get('confidence', 0.0)), bbox_str,
                is_staff, event_data.get('group_id'), '{}'
            )
            
            if not session_id:
                return

            # 2. Build/Update Session
            if event_type == 'PERSON_ENTERED':
                await conn.execute("""
                    INSERT INTO sessions (
                        session_id, track_id, camera_id, entry_time, is_staff, group_id, zones_visited
                    ) VALUES ($1, $2, $3, $4::timestamptz, $5, $6, '[]'::jsonb)
                    ON CONFLICT (session_id) DO NOTHING
                """,
                    session_id, int(event_data.get('track_id', 0)), event_data.get('camera_id'),
                    timestamp_str, is_staff, event_data.get('group_id')
                )
                
            elif event_type == 'ZONE_ENTERED':
                if zone:
                    # Upsert session if it doesn't exist just in case we missed PERSON_ENTERED
                    await conn.execute("""
                        INSERT INTO sessions (session_id, track_id, camera_id, entry_time, zones_visited)
                        VALUES ($1, $2, $3, $4::timestamptz, '[]'::jsonb)
                        ON CONFLICT (session_id) DO NOTHING
                    """, session_id, int(event_data.get('track_id', 0)), event_data.get('camera_id'), timestamp_str)
                    
                    await conn.execute("""
                        UPDATE sessions 
                        SET zones_visited = zones_visited || $1::jsonb
                        WHERE session_id = $2
                    """, json.dumps([zone]), session_id)
                    
            elif event_type == 'PERSON_EXITED':
                # Set exit time and calculate dwell
                await conn.execute("""
                    UPDATE sessions 
                    SET exit_time = $1::timestamptz, 
                        dwell_seconds = EXTRACT(EPOCH FROM ($1::timestamptz - entry_time))
                    WHERE session_id = $2
                """, timestamp_str, session_id)
                
                # POS Matching logic
                # If they visited Billing, try to match a POS transaction near their exit time
                row = await conn.fetchrow("SELECT zones_visited, entry_time FROM sessions WHERE session_id = $1", session_id)
                if row and row['zones_visited']:
                    zones_visited = json.loads(row['zones_visited'])
                    if any('billing' in z.lower() or 'checkout' in z.lower() for z in zones_visited):
                        # Find an unassigned POS transaction within +/- 15 minutes of exit time
                        pos_match = await conn.fetchrow("""
                            SELECT order_id FROM pos_transactions 
                            WHERE order_date = ($1::timestamptz AT TIME ZONE 'UTC')::date
                            AND order_time >= ($1::timestamptz - INTERVAL '15 minutes')::time
                            AND order_time <= ($1::timestamptz + INTERVAL '15 minutes')::time
                            AND order_id NOT IN (SELECT order_id FROM sessions WHERE order_id IS NOT NULL)
                            LIMIT 1
                        """, timestamp_str)
                        
                        if pos_match:
                            await conn.execute("""
                                UPDATE sessions SET purchased = TRUE, order_id = $1 WHERE session_id = $2
                            """, pos_match['order_id'], session_id)
                            logger.info(f"Matched session {session_id} to order {pos_match['order_id']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_url = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/store_intelligence")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    
    consumer = EventConsumer(db_url, redis_url)
    asyncio.run(consumer.run())
