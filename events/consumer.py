import os
import json
import asyncio
import asyncpg
import redis.asyncio as aioredis
import logging

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
                    count=10,
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
                await asyncio.sleep(5)
                
    async def _process_event(self, event_data: dict):
        # Insert into PostgreSQL
        query = """
            INSERT INTO events (
                event_id, event_type, timestamp, camera_id, track_id, 
                session_id, zone, previous_zone, confidence, bbox, 
                is_staff, group_id, metadata
            ) VALUES (
                $1, $2, $3::timestamptz, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12, $13::jsonb
            )
            ON CONFLICT (event_id) DO NOTHING
        """
        async with self.pool.acquire() as conn:
            # handle 'None' strings from redis serialization
            bbox_str = event_data.get('bbox', '{}').replace("'", '"') 
            
            await conn.execute(
                query,
                event_data.get('event_id'),
                event_data.get('event_type'),
                event_data.get('timestamp'),
                event_data.get('camera_id'),
                int(event_data.get('track_id', 0)),
                event_data.get('session_id'),
                event_data.get('zone'),
                event_data.get('previous_zone'),
                float(event_data.get('confidence', 0.0)),
                bbox_str,
                event_data.get('is_staff', 'False') == 'True',
                event_data.get('group_id'),
                '{}' # metadata
            )
        logger.debug(f"Saved event {event_data.get('event_id')} to DB")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_url = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/store_intelligence")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    
    consumer = EventConsumer(db_url, redis_url)
    asyncio.run(consumer.run())
