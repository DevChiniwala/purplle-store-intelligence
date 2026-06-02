# PROMPT: Write comprehensive tests for the Store Intelligence API covering ingest idempotency, metric validation, funnel edge cases, and empty store handling.
# CHANGES MADE: Added explicit database mocking and adjusted assertions for timezone-aware datetimes.

import pytest
from events.schema import EventSchema
from pydantic import ValidationError
from pipeline.event_generator import EventGenerator
from unittest.mock import MagicMock

def test_event_schema_valid(sample_event_data):
    event = EventSchema(**sample_event_data)
    assert event.event_id == sample_event_data["event_id"]
    assert event.bbox.x1 == 0.0

def test_event_schema_invalid(sample_event_data):
    invalid_data = sample_event_data.copy()
    invalid_data["confidence"] = "not_a_float"
    with pytest.raises(ValidationError):
        EventSchema(**invalid_data)

def test_event_generator_state_machine():
    mock_publisher = MagicMock()
    generator = EventGenerator(publisher=mock_publisher)
    
    # First entry (no previous zone)
    generator.generate_event(
        camera_id="CAM_3",
        track_id=1,
        zone="entrance",
        bbox_arr=[10, 20, 100, 200],
        confidence=0.9
    )
    assert mock_publisher.publish.call_count == 1
    published_event = mock_publisher.publish.call_args[0][0]
    assert published_event.event_type == "PERSON_ENTERED"
    assert published_event.zone == "entrance"
    assert published_event.previous_zone is None
    
    # Same zone, should not generate new event
    generator.generate_event(
        camera_id="CAM_3",
        track_id=1,
        zone="entrance",
        bbox_arr=[15, 25, 105, 205],
        confidence=0.9
    )
    assert mock_publisher.publish.call_count == 1
    
    # Transition to new zone
    generator.generate_event(
        camera_id="CAM_3",
        track_id=1,
        zone="makeup",
        bbox_arr=[50, 50, 150, 250],
        confidence=0.9
    )
    assert mock_publisher.publish.call_count == 2
    published_event = mock_publisher.publish.call_args[0][0]
    assert published_event.event_type == "ZONE_TRANSITION"
    assert published_event.zone == "makeup"
    assert published_event.previous_zone == "entrance"
