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
            event_data = {}
            for k, v in event_dict.items():
                if v is not None:
                    if isinstance(v, (dict, list)):
                        event_data[k] = json.dumps(v)
                    elif not isinstance(v, str):
                        event_data[k] = str(v)
                    else:
                        event_data[k] = v
            self.redis.xadd(self.stream_name, event_data)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
