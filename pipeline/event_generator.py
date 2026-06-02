import uuid
from datetime import datetime, timezone
import logging
from events.schema import EventSchema
from events.publisher import EventPublisher

logger = logging.getLogger(__name__)

class EventGenerator:
    def __init__(self, publisher: EventPublisher, store_id: str = "ST-5001"):
        self.publisher = publisher
        self.store_id = store_id
        # track_id -> current_zone mapping to detect transitions
        self.track_zones = {}
        # track_id -> visitor_id mapping
        self.track_visitors = {}
        # track_id -> entry_time for dwell calculation
        self.track_entry_times = {}
        
    def generate_event(self, camera_id: str, track_id: int, zone: str, confidence: float, timestamp: datetime = None, is_staff: bool = False, metadata: dict = None):
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        if metadata is None:
            metadata = {}
            
        previous_zone = self.track_zones.get(track_id)
        
        # Determine event type
        if previous_zone is None:
            event_type = "ENTRY" if "entrance" in zone.lower() else "ZONE_ENTER"
            self.track_visitors[track_id] = f"VIS_{uuid.uuid4().hex[:6]}"
            self.track_entry_times[track_id] = timestamp
        elif previous_zone != zone:
            # We could emit a ZONE_EXIT for previous, but let's just emit ZONE_ENTER for new
            event_type = "ZONE_ENTER"
            self.track_entry_times[track_id] = timestamp
        else:
            # Same zone, simulate a ZONE_DWELL
            event_type = "ZONE_DWELL"
            
        self.track_zones[track_id] = zone
        visitor_id = self.track_visitors.get(track_id)
        
        # Calculate dwell_ms
        dwell_ms = 0
        if event_type == "ZONE_DWELL":
            entry_time = self.track_entry_times.get(track_id, timestamp)
            dwell_ms = int((timestamp - entry_time).total_seconds() * 1000)
        
        # Ensure metadata has required fields if applicable
        if event_type == "BILLING_QUEUE_JOIN" and "queue_depth" not in metadata:
            metadata["queue_depth"] = 1
            
        metadata["session_seq"] = metadata.get("session_seq", 1)
        
        event = EventSchema(
            event_id=str(uuid.uuid4()),
            store_id=self.store_id,
            camera_id=camera_id,
            visitor_id=visitor_id,
            event_type=event_type,
            timestamp=timestamp.isoformat(),
            zone_id=zone.upper().replace(" ", "_"),
            dwell_ms=dwell_ms,
            is_staff=is_staff,
            confidence=float(confidence),
            metadata=metadata
        )
        
        self.publisher.publish(event)
        logger.debug(f"Generated event: {event_type} for track {track_id} in {zone}")
