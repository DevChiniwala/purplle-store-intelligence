import uuid
from datetime import datetime, timezone
import logging
from events.schema import EventSchema, BoundingBox
from events.publisher import EventPublisher

logger = logging.getLogger(__name__)

class EventGenerator:
    def __init__(self, publisher: EventPublisher):
        self.publisher = publisher
        # track_id -> current_zone mapping to detect transitions
        self.track_zones = {}
        # track_id -> session_id mapping
        self.track_sessions = {}
        
    def generate_event(self, camera_id: str, track_id: int, zone: str, bbox_arr, confidence: float, timestamp: datetime = None, is_staff: bool = False, group_id: str = None, metadata: dict = None):
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        if metadata is None:
            metadata = {}
            
        previous_zone = self.track_zones.get(track_id)
        
        # Determine event type
        if previous_zone is None:
            # First time we see this track, if it's the entrance camera and entrance zone, it's an entry
            # Otherwise it's just a general ZONE_ENTERED
            event_type = "PERSON_ENTERED" if "entrance" in zone.lower() else "ZONE_ENTERED"
            self.track_sessions[track_id] = f"sess_{uuid.uuid4().hex[:8]}"
        elif previous_zone != zone:
            event_type = "ZONE_TRANSITION"
        else:
            # Still in the same zone, we don't spam events. We might send a heartbeat or dwell update.
            return
            
        self.track_zones[track_id] = zone
        session_id = self.track_sessions.get(track_id)
        
        event = EventSchema(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=timestamp.isoformat(),
            camera_id=camera_id,
            track_id=track_id,
            session_id=session_id,
            zone=zone,
            previous_zone=previous_zone,
            confidence=float(confidence),
            bbox=BoundingBox(
                x1=float(bbox_arr[0]), 
                y1=float(bbox_arr[1]), 
                x2=float(bbox_arr[2]), 
                y2=float(bbox_arr[3])
            ),
            is_staff=is_staff,
            group_id=group_id,
            metadata=metadata
        )
        
        self.publisher.publish(event)
        logger.debug(f"Generated event: {event_type} for track {track_id} in {zone}")
