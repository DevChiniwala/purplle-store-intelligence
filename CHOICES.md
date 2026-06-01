# Engineering Trade-offs & Choices

## 1. Machine Learning Models
**Choice: YOLOv8n + ByteTrack**
*Trade-off*: We chose YOLOv8-nano over larger models (like YOLOv8-large or RT-DETR) to ensure the pipeline can process 5 concurrent 1080p camera streams on edge hardware in real-time. ByteTrack was chosen over DeepSORT because it relies purely on spatial IoU and detection confidence rather than heavy Re-ID feature extractors, saving significant compute while maintaining robust temporal tracking.

## 2. Event Streaming
**Choice: Redis Streams**
*Trade-off*: We chose Redis Streams over Apache Kafka or RabbitMQ. While Kafka provides better long-term durability, Redis is vastly simpler to deploy in a local/edge Docker environment, uses a fraction of the RAM, and provides exactly the pub/sub + consumer group semantics we need for pushing events from the Python pipeline to PostgreSQL.

## 3. Database
**Choice: PostgreSQL (Relational) vs Time-Series DBs**
*Trade-off*: We chose standard PostgreSQL over specialized time-series databases like TimescaleDB or InfluxDB. The retail analytics domain requires heavy relational joins (Events -> Sessions -> POS Transactions). PostgreSQL handles JSONB for arbitrary bounding box metadata, standard relational joins for POS correlation, and is performant enough for our event volume when properly indexed.

## 4. API Framework
**Choice: FastAPI**
*Trade-off*: We chose FastAPI over Flask or Django. The async native architecture of FastAPI is perfect for the massive concurrent I/O we do (database pooling with `asyncpg` and WebSocket streaming). 

## 5. Frontend Stack
**Choice: React + Vite**
*Trade-off*: We chose React with Vite over Next.js. Since the dashboard is a client-side heavy application streaming real-time WebSockets with complex data visualizations (Recharts), server-side rendering (SSR) via Next.js adds unnecessary complexity. Vite provides instant HMR and a blazing fast build process for the hackathon.

## 6. Spatial Mapping
**Choice: Polygon Zones vs Grid Heatmaps**
*Trade-off*: We mapped the store using strict vector polygons rather than a grid. A grid doesn't respect physical boundaries (shelves, counters). Polygons allow us to perfectly align detection zones with the actual store layout seen in the camera frames, enabling highly accurate "engaged with Skincare" metrics.

## 7. Development Choices
**Choice: Frame Skipping**
*Trade-off*: We only run inference on every 15th frame (~2 FPS). Retail environments have slow-moving targets. Running at 30 FPS wastes 90% of GPU resources on redundant data. 2 FPS is plenty for accurate dwell time and zone transitions.
