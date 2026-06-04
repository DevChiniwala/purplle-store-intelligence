# Technical Choices & Trade-offs

## 1. Model Selection (YOLOv8)
**Choice:** We chose YOLOv8 Nano (`yolov8n.pt`) as our object detection model for the pipeline.
**Reason:**
- The primary concern for processing multiple concurrent CCTV streams is latency and throughput. YOLOv8n offers the best balance of fast inference speed (often >30 FPS on standard hardware) and adequate accuracy for detecting people.
- It comes with built-in multi-object tracking (using ByteTrack or BoT-SORT natively supported in Ultralytics) out of the box, saving us from implementing complex Kalman Filter pipelines manually.

## 2. FastAPI Framework
**Choice:** We selected FastAPI for the backend over Django or Flask.
**Reason:**
- The application is heavily IO-bound (database queries, Redis, WebSockets). FastAPI’s native async/await support ensures optimal performance.
- Built-in Pydantic validation handles JSON schemas seamlessly, providing automatic 422 errors for malformed event data.
- Built-in OpenAPI documentation generation aids in rapid testing.

## 2. PostgreSQL + asyncpg
**Choice:** PostgreSQL with `asyncpg` as the primary datastore.
**Reason:**
- We need robust analytical querying capabilities (grouping by zones, calculating time differences) which standard relational databases excel at.
- `asyncpg` is the fastest async driver for PostgreSQL in Python, maximizing throughput.
- JSONB columns in Postgres allow us to flexibly store metadata or lists of visited zones without creating overly complex relational schemas.

## 3. Redis Streams for Event Ingestion
**Choice:** Using a message broker buffer (Redis Streams) instead of direct database inserts for the pipeline events.
**Reason:**
- **Resilience:** If the database goes down or experiences a spike, Redis Streams buffers the incoming events.
- **Consumer Groups:** Allows scaling out consumers horizontally and tracking progress (xack).
- **Latency:** Edge detection system can write to Redis instantly with minimal latency.
- **Trade-off:** Eventual consistency (events take a few milliseconds to appear in the database/dashboard).

## 4. Frontend - React + Vite + Recharts
**Choice:** React built with Vite, utilizing Recharts for data visualization.
**Reason:**
- Vite provides instantaneous hot-module replacement (HMR) for fast iteration.
- React's component-based architecture is ideal for real-time dashboards where individual widgets (like the Funnel or KPI cards) need independent state updates via WebSockets.
- Recharts handles complex SVG calculations automatically and provides responsive charts out of the box.

## 5. Mocking in Test Suite
**Choice:** Using `pytest` with `pytest-asyncio` and `AsyncMock` to completely mock the database and Redis dependency in unit tests.
**Reason:**
- Ensuring the tests run instantaneously and do not rely on an external running database container.
- We overrode the FastAPI dependencies and mocked `asyncpg` and `redis` context managers, achieving >85% statement coverage across API, service, and event pipeline layers.

## 6. Dwell Time Computation
**Choice:** Calculating `dwell_ms` using memory tracking in `video_processor.py` rather than purely in SQL.
**Reason:**
- It's simpler to track when a `track_id` first appears and when it disappears at the edge or ingestion layer. This prevents complex self-joins or window functions in PostgreSQL, shifting computation left to the ingestion layer.
