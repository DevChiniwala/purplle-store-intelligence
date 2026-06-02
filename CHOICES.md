# Architectural Choices

This document outlines the three core decisions mandated by the rubric.

## 1. Detection Model Selection
**Options Considered:** YOLOv8, RT-DETR, MediaPipe.
**AI Suggestion:** Claude 3.5 Sonnet suggested using YOLOv8 due to its strong balance of speed and accuracy, mature ecosystem (Ultralytics), and built-in tracking support (BoT-SORT/ByteTrack) which handles occlusions well in retail environments.
**Choice and Rationale:** We chose **YOLOv8** paired with ByteTrack. While RT-DETR offers potentially better transformer-based occlusion handling, YOLOv8's tracking integration provided the fastest path to stable Re-ID without a separate heavy feature extraction model. We explicitly disabled confidence thresholding for output events so that the API layer could dynamically filter rather than having the pipeline silently drop low-confidence partial occlusions.

## 2. Event Schema Design Rationale
**Options Considered:** A highly denormalized flat schema vs. a hierarchical JSON schema.
**AI Suggestion:** Gemini 1.5 Pro suggested a flat schema with a generic `metadata` JSONB column, arguing it provides strong typing for core metrics (timestamp, zone_id, dwell) while retaining flexibility for edge cases (queue_depth, demographics).
**Choice and Rationale:** We chose the **flat schema + metadata JSONB block** as suggested. This aligns perfectly with PostgreSQL's JSONB capabilities. It allows the `events.consumer` to rapidly ingest fixed-schema events into a structured table, while still allowing the `EventGenerator` to attach variable data like `queue_depth` for `BILLING_QUEUE_JOIN` without requiring schema migrations.

## 3. API Architecture Choice
**Options Considered:** Synchronous REST processing vs. Asynchronous stream processing.
**AI Suggestion:** ChatGPT (GPT-4o) strongly recommended a decoupled architecture using Redis Streams and a background consumer to build materialized `sessions`, rather than computing sessions on the fly from raw events.
**Choice and Rationale:** We chose the **Asynchronous Stream Processing** approach. The detection pipeline emits events to Redis. A dedicated Python consumer pulls these events and upserts them into a `sessions` table (recording entry, exit, and zones visited). This prevents the FastAPI endpoints from executing heavy analytical queries over thousands of raw events for the `/funnel` and `/metrics` routes, guaranteeing O(1) read latency for the real-time dashboard.
