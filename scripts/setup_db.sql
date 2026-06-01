-- setup_db.sql

CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    camera_id VARCHAR NOT NULL,
    track_id INT,
    session_id VARCHAR,
    zone VARCHAR,
    previous_zone VARCHAR,
    confidence FLOAT,
    bbox JSONB,
    is_staff BOOL DEFAULT FALSE,
    group_id VARCHAR,
    dwell_seconds FLOAT,
    metadata JSONB
);

CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_camera ON events(camera_id);
CREATE INDEX idx_events_session ON events(session_id);

CREATE TABLE IF NOT EXISTS pos_transactions (
    order_id VARCHAR NOT NULL,
    invoice_number VARCHAR NOT NULL,
    order_date DATE NOT NULL,
    order_time TIME NOT NULL,
    store_id VARCHAR,
    store_name VARCHAR,
    customer_name VARCHAR,
    customer_number VARCHAR,
    product_name VARCHAR,
    brand_name VARCHAR,
    category VARCHAR,
    sub_category VARCHAR,
    salesperson_name VARCHAR,
    qty INT,
    gmv DECIMAL,
    nmv DECIMAL,
    total_amount DECIMAL
);

CREATE INDEX idx_pos_order_time ON pos_transactions(order_date, order_time);
CREATE INDEX idx_pos_customer ON pos_transactions(customer_name);

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
    session_id VARCHAR PRIMARY KEY,
    track_id INT,
    camera_id VARCHAR,
    entry_time TIMESTAMPTZ,
    exit_time TIMESTAMPTZ,
    dwell_seconds FLOAT,
    zones_visited JSONB,
    is_staff BOOL DEFAULT FALSE,
    group_id VARCHAR,
    purchased BOOL DEFAULT FALSE,
    order_id VARCHAR
);

CREATE INDEX idx_sessions_entry ON sessions(entry_time);
