# PROMPT: Write comprehensive tests for the Store Intelligence API covering ingest idempotency, metric validation, funnel edge cases, and empty store handling.
# CHANGES MADE: Added explicit database mocking, publisher tests, and consumer process tests.

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from events.schema import EventSchema
from pydantic import ValidationError
from pipeline.event_generator import EventGenerator
from events.publisher import EventPublisher
from events.consumer import EventConsumer
import datetime as dt

def test_event_schema_valid(sample_event_data):
    # Just need basic schema validation
    event = EventSchema(**sample_event_data)
    assert event.event_id == sample_event_data["event_id"]

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
        confidence=0.9
    )
    assert mock_publisher.publish.call_count == 1
    published_event = mock_publisher.publish.call_args[0][0]
    assert published_event.event_type == "ENTRY"
    assert published_event.zone_id == "ENTRANCE"
    
    # Same zone -> DWELL
    generator.generate_event(
        camera_id="CAM_3",
        track_id=1,
        zone="entrance",
        confidence=0.88
    )
    assert mock_publisher.publish.call_count == 2
    published_event2 = mock_publisher.publish.call_args[0][0]
    assert published_event2.event_type == "ZONE_DWELL"
    
    # Transition to new zone
    generator.generate_event(
        camera_id="CAM_3",
        track_id=1,
        zone="skincare",
        confidence=0.88
    )
    assert mock_publisher.publish.call_count == 3
    published_event3 = mock_publisher.publish.call_args[0][0]
    assert published_event3.event_type == "ZONE_ENTER"
    assert published_event3.zone_id == "SKINCARE"


# ── Publisher Tests ──────────────────────────────────────────────────────────

def test_publisher_publish():
    mock_redis = MagicMock()
    publisher = EventPublisher(redis_url="redis://localhost:6379", stream_name="test_stream")
    publisher.redis = mock_redis
    
    event = EventSchema(
        event_id="e1",
        store_id="s1",
        camera_id="c1",
        visitor_id="v1",
        event_type="ENTRY",
        timestamp="2026-06-02T12:00:00Z",
        confidence=0.9,
        metadata={"key": "value"}
    )
    publisher.publish(event)
    
    mock_redis.xadd.assert_called_once()
    args, kwargs = mock_redis.xadd.call_args
    assert args[0] == "test_stream"
    assert args[1]["event_id"] == "e1"
    assert args[1]["metadata"] == '{"key": "value"}'

def test_publisher_publish_exception():
    mock_redis = MagicMock()
    mock_redis.xadd.side_effect = Exception("Redis error")
    publisher = EventPublisher(redis_url="redis://localhost:6379", stream_name="test_stream")
    publisher.redis = mock_redis
    
    event = EventSchema(
        event_id="e1",
        store_id="s1",
        camera_id="c1",
        visitor_id="v1",
        event_type="ENTRY",
        timestamp="2026-06-02T12:00:00Z",
        confidence=0.9,
        metadata={"key": "value"}
    )
    # Should handle exception and not crash
    publisher.publish(event)
    mock_redis.xadd.assert_called_once()


# ── Consumer Tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_consumer_process_event_entry():
    consumer = EventConsumer(db_url="postgresql://", redis_url="redis://")
    consumer.pool = MagicMock()
    conn = AsyncMock()
    acquire_mock = AsyncMock()
    acquire_mock.__aenter__.return_value = conn
    consumer.pool.acquire.return_value = acquire_mock
    
    event_data = {
        "event_id": "e1",
        "store_id": "s1",
        "camera_id": "c1",
        "visitor_id": "v1",
        "event_type": "ENTRY",
        "timestamp": "2026-06-02T12:00:00Z",
        "confidence": "0.9",
        "dwell_ms": "1000",
        "is_staff": "False",
        "metadata": "{'session_seq': 1}"
    }
    
    await consumer._process_event(event_data)
    
    assert conn.execute.call_count >= 2
    args1 = conn.execute.call_args_list[0][0]
    assert "INSERT INTO events" in args1[0]
    assert args1[1] == "e1"
    
    args2 = conn.execute.call_args_list[1][0]
    assert "INSERT INTO sessions" in args2[0]
    assert args2[1] == "v1"

@pytest.mark.asyncio
async def test_consumer_process_event_zone_enter():
    consumer = EventConsumer(db_url="postgresql://", redis_url="redis://")
    consumer.pool = MagicMock()
    conn = AsyncMock()
    acquire_mock = AsyncMock()
    acquire_mock.__aenter__.return_value = conn
    consumer.pool.acquire.return_value = acquire_mock
    
    event_data = {
        "event_id": "e1",
        "store_id": "s1",
        "camera_id": "c1",
        "visitor_id": "v1",
        "event_type": "ZONE_ENTER",
        "timestamp": "2026-06-02T12:00:00Z",
        "zone_id": "skincare",
        "confidence": "0.9"
    }
    
    await consumer._process_event(event_data)
    
    assert conn.execute.call_count == 3
    args3 = conn.execute.call_args_list[2][0]
    assert "UPDATE sessions" in args3[0]
    assert json.loads(args3[1]) == ["skincare"]

@pytest.mark.asyncio
async def test_consumer_process_event_exit_with_pos_match():
    consumer = EventConsumer(db_url="postgresql://", redis_url="redis://")
    consumer.pool = MagicMock()
    conn = AsyncMock()
    acquire_mock = AsyncMock()
    acquire_mock.__aenter__.return_value = conn
    consumer.pool.acquire.return_value = acquire_mock
    
    event_data = {
        "event_id": "e1",
        "store_id": "s1",
        "camera_id": "c1",
        "visitor_id": "v1",
        "event_type": "EXIT",
        "timestamp": "2026-06-02T12:00:00Z",
        "confidence": "0.9"
    }
    
    conn.fetchrow.side_effect = [
        {"zones_visited": ["skincare", "billing"], "entry_time": dt.datetime.now(dt.timezone.utc)},
        {"transaction_id": "tx123"}
    ]
    
    await consumer._process_event(event_data)
    
    assert conn.execute.call_count == 3
    assert conn.fetchrow.call_count == 2
    
    exit_args = conn.execute.call_args_list[1][0]
    assert "UPDATE sessions" in exit_args[0]
    
    purch_args = conn.execute.call_args_list[2][0]
    assert "purchased = TRUE" in purch_args[0]
    assert purch_args[1] == "tx123"

@pytest.mark.asyncio
async def test_consumer_process_event_no_visitor_id():
    consumer = EventConsumer(db_url="postgresql://", redis_url="redis://")
    consumer.pool = MagicMock()
    conn = AsyncMock()
    acquire_mock = AsyncMock()
    acquire_mock.__aenter__.return_value = conn
    consumer.pool.acquire.return_value = acquire_mock
    
    event_data = {
        "event_id": "e1",
        "store_id": "s1",
        "camera_id": "c1",
        "event_type": "ENTRY",
        "timestamp": "2026-06-02T12:00:00Z",
        "confidence": "0.9"
    }
    
    await consumer._process_event(event_data)
    assert conn.execute.call_count == 1

@pytest.mark.asyncio
async def test_consumer_run_once():
    consumer = EventConsumer(db_url="postgresql://", redis_url="redis://")
    
    mock_redis = AsyncMock()
    mock_pool = MagicMock()
    
    mock_redis.xreadgroup.side_effect = [
        [(b"stream", [(b"msg_id", {b"event_id": b"e1", b"event_type": b"ENTRY"})])],
        KeyboardInterrupt("Exit loop")
    ]
    
    async def mock_create_pool(*args, **kwargs):
        return mock_pool
    
    with patch("redis.asyncio.from_url", return_value=mock_redis), \
         patch("asyncpg.create_pool", new=mock_create_pool), \
         patch.object(consumer, "_process_event", new_callable=AsyncMock) as mock_process:
         
         with pytest.raises(KeyboardInterrupt, match="Exit loop"):
             await consumer.run()
             
         mock_redis.xgroup_create.assert_called_once()
         assert mock_redis.xreadgroup.call_count == 2
         mock_process.assert_called_once_with({"event_id": "e1", "event_type": "ENTRY"})
         mock_redis.xack.assert_called_once()
