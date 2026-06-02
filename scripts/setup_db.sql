-- setup_db.sql

CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY,
    store_id VARCHAR NOT NULL,
    camera_id VARCHAR NOT NULL,
    visitor_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    zone_id VARCHAR,
    dwell_ms INT,
    is_staff BOOL DEFAULT FALSE,
    confidence FLOAT,
    metadata JSONB
);

CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_camera ON events(camera_id);
CREATE INDEX idx_events_visitor ON events(visitor_id);

CREATE TABLE IF NOT EXISTS pos_transactions (
    store_id VARCHAR,
    transaction_id VARCHAR PRIMARY KEY,
    timestamp TIMESTAMPTZ,
    basket_value_inr DECIMAL
);

CREATE INDEX idx_pos_timestamp ON pos_transactions(timestamp);
CREATE INDEX idx_pos_store ON pos_transactions(store_id);

CREATE TABLE IF NOT EXISTS pipeline_status (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    frames_processed INT DEFAULT 0,
    total_frames INT DEFAULT 0,
    events_generated INT DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS sessions (
    visitor_id VARCHAR PRIMARY KEY,
    store_id VARCHAR,
    camera_id VARCHAR,
    entry_time TIMESTAMPTZ,
    exit_time TIMESTAMPTZ,
    dwell_ms INT,
    zones_visited JSONB,
    is_staff BOOL DEFAULT FALSE,
    group_id VARCHAR,
    purchased BOOL DEFAULT FALSE,
    transaction_id VARCHAR
);

CREATE INDEX idx_sessions_entry ON sessions(entry_time);
