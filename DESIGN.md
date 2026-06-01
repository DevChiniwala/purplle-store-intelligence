# Purplle Store Intelligence - System Design & Architecture

## System Architecture Overview

The system is designed as a fully decoupled, event-driven streaming architecture capable of handling real-time CCTV feeds and processing them into actionable business insights.

### 1. Computer Vision Pipeline (Edge/Node)
- **Object Detection & Tracking:** YOLOv8 detects persons in the video frames, and DeepSORT tracks them across frames.
- **Zone Classification:** A geometric mapping module projects the person's bounding box coordinates onto a store layout to classify their current semantic zone (e.g., "Entry", "Skincare", "Billing").
- **Edge Case Manager:** Implements logic to deduplicate staff (based on zone lingering or predefined areas) and handle group bounding boxes.

### 2. Event Streaming (Redis)
- To prevent the heavy GPU/CPU workload of the CV pipeline from blocking the API, the pipeline emits raw semantic events (`PERSON_ENTERED`, `ZONE_ENTERED`, `PERSON_EXITED`) directly into a Redis Stream (`store_events`).
- This guarantees high throughput and decouples the AI inference from data persistence.

### 3. Session Aggregator (Consumer)
- An asynchronous Python consumer reads from the Redis stream in real-time.
- It aggregates individual frame-level events into persistent "Sessions" in PostgreSQL.
- **POS Mapping:** When a session concludes (especially if the `Billing` zone was visited), the consumer probabilistically matches the visitor with real POS transactions based on exit timestamps.

### 4. Real-time Analytics API (FastAPI)
- Exposes REST and WebSocket endpoints for the frontend dashboard.
- Aggregates `sessions` into Funnels, Store Conversion Rates, and identifies Anomalies via dynamic SQL queries.

### 5. Dashboard (React + Recharts)
- Consumes the API to render visually stunning metrics.

## Data Flow
`Video.mp4` -> `YOLO Pipeline` -> `Redis Stream` -> `Python Consumer` -> `PostgreSQL` -> `FastAPI` -> `React Dashboard`
