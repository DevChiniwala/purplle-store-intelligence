import json
import redis
import logging
from events.schema import EventSchema

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self, redis_url: str = "redis://redis:6379", stream_name: str = "store_events"):
        self.redis = redis.from_url(redis_url)
        self.stream_name = stream_name
        
    def publish(self, event: EventSchema):
        try:
            event_dict = event.model_dump()
            # Convert dicts and lists to strings for redis hash
            event_data = {k: str(v) if not isinstance(v, str) else v for k, v in event_dict.items() if v is not None}
            self.redis.xadd(self.stream_name, event_data)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
