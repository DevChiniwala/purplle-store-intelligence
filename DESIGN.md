# System Design

## 1. System Architecture
The Store Intelligence System follows a microservices architecture designed for high throughput video processing and low latency analytics.

1. **Computer Vision Pipeline (`pipeline/`)**: Stateful Python daemon that processes video frames using YOLOv8 and ByteTrack. Extracts semantic business events.
2. **Event Broker (`Redis`)**: Decouples the slow/bursty database insertions from the real-time GPU processing.
3. **Data Persistence (`PostgreSQL`)**: Central source of truth storing structured events, consolidated visitor sessions, and POS transactions.
4. **Analytics API (`FastAPI`)**: High-performance async API aggregating data from PostgreSQL for historical reporting and streaming from Redis for real-time updates.
5. **Dashboard (`React/Vite`)**: Client-side SPA providing visualizations.

## 2. Detection Pipeline Design
- **Detection**: YOLOv8 extracts `[x1, y1, x2, y2, confidence]` for the `person` class.
- **Tracking**: ByteTrack assigns persistent IDs across frames.
- **Zone Mapping**: The system uses `shapely`/`opencv` point-in-polygon tests on the bottom-center coordinate of a bounding box to determine the customer's physical location (e.g., Skincare Zone vs Entry).
- **Event Generation**: The state machine detects state changes (Zone A -> Zone B) and emits `ZONE_TRANSITION` events.

## 3. Session Reconstruction Logic
Raw `ZONE_TRANSITION` events are aggregated in PostgreSQL into `sessions`. 
A session groups all tracks for a single visitor across all cameras.
- Entry time: First `PERSON_ENTERED` event.
- Exit time: Final track disappearance near an exit zone.
- Dwell time: `Exit - Entry`.
- Zones visited: JSON array of all unique zones the track intersected.

## 4. Conversion Funnel Algorithm
The funnel is dynamically calculated using SQL aggregations:
1. **Entered**: Total unique non-staff sessions.
2. **Engaged**: Sessions with `dwell_seconds > 60` or `len(zones_visited) >= 2`.
3. **Interested**: Sessions containing specific product zones (`makeup`, `skincare`).
4. **Converted**: Sessions correlated with a POS transaction (via timestamp/zone proximity heuristics).
5. **Repeat**: Visitors identified as returning (via Re-ID or track continuation).

## 5. Scalability Considerations
- **Video Sharding**: The architecture allows running multiple CV containers, each consuming different RTSP streams.
- **Database Partitioning**: The `events` table in PostgreSQL is heavily indexed on `timestamp` and `camera_id`, making it ready for time-based partitioning in a multi-store rollout.
