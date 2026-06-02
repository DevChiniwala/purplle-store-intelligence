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
            if "billing" in zone.lower():
                event_type = "BILLING_QUEUE_JOIN"
        elif previous_zone != zone:
            event_type = "ZONE_ENTER"
            if "billing" in zone.lower():
                event_type = "BILLING_QUEUE_JOIN"
            elif previous_zone and "billing" in previous_zone.lower():
                # Emitting a standalone ABANDON is complex here since we override event_type.
                # Actually, we can just let it be ZONE_ENTER for the new zone. 
                # If they left billing without a transaction, the backend consumer handles ABANDON logic based on EXIT + POS matching, 
                # or we can emit an explicit ABANDON event right before the new ZONE_ENTER.
                abandon_event = EventSchema(
                    event_id=str(uuid.uuid4()),
                    store_id=self.store_id,
                    camera_id=camera_id,
                    visitor_id=self.track_visitors.get(track_id),
                    event_type="BILLING_QUEUE_ABANDON",
                    timestamp=timestamp.isoformat(),
                    zone_id=previous_zone.upper().replace(" ", "_"),
                    dwell_ms=0,
                    is_staff=is_staff,
                    confidence=float(confidence),
                    metadata={"session_seq": metadata.get("session_seq", 1)}
                )
                self.publisher.publish(abandon_event)
                
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
            metadata["queue_depth"] = sum(1 for z in self.track_zones.values() if "billing" in z.lower())
            
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

    def generate_exit_event(self, camera_id: str, track_id: int, timestamp: datetime = None, is_staff: bool = False):
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
            
        visitor_id = self.track_visitors.get(track_id)
        if not visitor_id:
            return
            
        last_zone = self.track_zones.get(track_id, "UNKNOWN")
        
        event = EventSchema(
            event_id=str(uuid.uuid4()),
            store_id=self.store_id,
            camera_id=camera_id,
            visitor_id=visitor_id,
            event_type="EXIT",
            timestamp=timestamp.isoformat(),
            zone_id=last_zone.upper().replace(" ", "_"),
            dwell_ms=0,
            is_staff=is_staff,
            confidence=1.0,
            metadata={"session_seq": 999}
        )
        
        self.publisher.publish(event)
        logger.debug(f"Generated event: EXIT for track {track_id}")
        
        # Cleanup
        self.track_zones.pop(track_id, None)
        self.track_visitors.pop(track_id, None)
        self.track_entry_times.pop(track_id, None)
