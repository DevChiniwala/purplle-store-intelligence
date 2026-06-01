# Purplle Store Intelligence System 🏪

![Dashboard Screenshot](dashboard/public/hero.png)

A high-performance, AI-powered store intelligence system designed for the **Purplle Tech Challenge 2026**. This system ingests multi-camera CCTV footage and POS sales data to generate real-time analytics on footfall, conversion rates, zone engagement, and staff efficiency.

## 🌟 Key Features

- **Real-time Computer Vision**: YOLOv8 + ByteTrack pipeline running on 5 concurrent camera feeds.
- **Semantic Zone Mapping**: Translates raw X/Y coordinates into business-meaningful zones (Skincare, Makeup, Billing, Entrance).
- **High-Throughput Event Engine**: Redis Pub/Sub architecture ensures the GPU pipeline never blocks on database writes.
- **Rich Analytics API**: FastAPI backend delivering comprehensive KPIs, conversion funnels, and spatial heatmaps.
- **Interactive Dashboard**: Modern, glassmorphism React+Vite frontend with Recharts visualization.
- **Edge Case Handling**: Staff filtering, shopping group detection, and child demographics heuristics.

## 🏗️ Architecture

```mermaid
graph TD
    subgraph Edge / Store
        CAM1[Cam 1: Skincare] -->|RTSP/Video| YOLO
        CAM2[Cam 2: Makeup] -->|RTSP/Video| YOLO
        CAM3[Cam 3: Entrance] -->|RTSP/Video| YOLO
        CAM4[Cam 4: Staff] -->|RTSP/Video| YOLO
        CAM5[Cam 5: Billing] -->|RTSP/Video| YOLO
    end

    subgraph CV Pipeline
        YOLO[YOLOv8 Detection] --> BT[ByteTrack]
        BT --> ZC[Zone Classifier]
        ZC --> EC[Edge Case Filter]
        EC --> EG[Event Generator]
    end

    subgraph Event Broker
        EG -->|Publish| Redis[(Redis Streams)]
    end

    subgraph Data Layer
        Redis -->|Consume| DB[(PostgreSQL)]
        POS[POS Excel Data] -->|Seed Script| DB
    end

    subgraph Application
        DB --> API[FastAPI Server]
        Redis -->|WebSocket| API
        API -->|REST / WS| UI[React Dashboard]
    end
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 22+ (for local UI dev)
- Python 3.10+ (for local API dev)

### Run with Docker Compose (Recommended)

1. Clone the repository
2. Extract your CCTV footage into `data/videos/CCTV Footage/`
3. Run the orchestration stack:
```bash
docker-compose up -d --build
```
4. Access the Dashboard at [http://localhost:5173](http://localhost:5173)
5. Access the API Docs at [http://localhost:8000/docs](http://localhost:8000/docs)

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | System health status |
| `/api/v1/stores/{store_id}/metrics` | GET | Core KPIs (Footfall, Revenue, Conversion) |
| `/api/v1/stores/{store_id}/funnel` | GET | 5-stage conversion funnel analysis |
| `/api/v1/stores/{store_id}/heatmap` | GET | Zone engagement and dwell times |
| `/api/v1/stores/{store_id}/anomalies` | GET | Detected anomalies (e.g., loitering, spikes) |
| `/api/v1/events` | GET | Paginated raw event log |
| `/ws/events` | WS | Real-time WebSocket event stream |

## 📁 Project Structure

```
purplle-store-intelligence/
├── api/                  # FastAPI backend
├── config/               # System and camera zone configurations
├── dashboard/            # React + Vite frontend
├── events/               # Redis pub/sub schemas and workers
├── pipeline/             # YOLOv8 + ByteTrack CV pipeline
├── scripts/              # DB setup and POS seeding scripts
├── tests/                # Pytest suite
└── docker-compose.yml    # Orchestration
```

---
*Built for the Purplle Tech Challenge 2026 Round 2.*
