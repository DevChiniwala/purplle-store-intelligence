# Engineering Trade-offs & Decision Making

This document outlines the core architectural and implementation decisions made to satisfy the Purplle Tech Challenge 2026 Round 2 requirements, focusing on production-readiness, edge cases, and real-time computation.

## 1. Decoupling Detection from Analytics (Redis Streams)
**The Problem:** Running a heavy object detection and tracking pipeline (YOLOv8 + DeepSORT) in the same process as the Analytics API would lead to severe latency, blocked event loops, and dropped API requests.
**The Choice:** We decoupled the two systems using Redis Streams. The CV pipeline acts solely as an event emitter (`events.publisher`), pushing raw semantic events (`ZONE_ENTERED`). A separate asynchronous Python worker (`events.consumer`) reads these streams and builds persistent sessions.
**Trade-off:** Adds an infrastructure dependency (Redis), but guarantees high availability and enables the system to horizontally scale (multiple cameras streaming to one Redis cluster).

## 2. Real-Time Session Aggregation vs Batch Processing
**The Problem:** The `/funnel` and `/metrics` APIs need to calculate metrics based on distinct visitor journeys, but the CV pipeline only emits point-in-time zone events.
**The Choice:** Instead of forcing the API to compute sessions on-the-fly from thousands of raw events (which scales poorly), the `consumer` aggregates events into a `sessions` table in real-time. We use PostgreSQL `JSONB` to store `zones_visited`. 
**Trade-off:** Write-heavy on the database during stream ingestion, but guarantees O(1) or lightning-fast read queries for the dashboard.

## 3. Probabilistic POS Matching
**The Problem:** The Computer Vision pipeline has no concept of a "receipt" or "order_id" to compute absolute Store Conversion Rate.
**The Choice:** We implemented a probabilistic matching algorithm in the Consumer. If a tracked session's `zones_visited` includes the "Billing" area, the system queries the `pos_transactions` table for unassigned orders that occurred within +/- 15 minutes of the visitor's exit time.
**Trade-off:** Not 100% accurate (multiple people might check out simultaneously), but represents a realistic engineering compromise without employing highly invasive facial recognition to cross-reference loyalty accounts.

## 4. Elimination of Mock Data
**The Problem:** Relying on mock scripts caps evaluation scores and hides pipeline integration bugs.
**The Choice:** The entire system—including Heatmaps, Anomalies, Funnels, and Metrics—is powered entirely by live data populated organically by the `pipeline` and `consumer` containers upon running `docker-compose up`. All API endpoints query the PostgreSQL database directly.
