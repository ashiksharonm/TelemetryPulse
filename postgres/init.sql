-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Raw Events Table
-- Stores all incoming sensor telemetry
CREATE TABLE IF NOT EXISTS telemetry_events (
    event_id UUID PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    zone_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL, -- 'co2', 'temperature', 'humidity', 'occupancy'
    value FLOAT NOT NULL,
    ts_event TIMESTAMP WITH TIME ZONE NOT NULL,
    ts_ingest TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX idx_events_ts_event ON telemetry_events(ts_event);
CREATE INDEX idx_events_site_zone ON telemetry_events(site_id, zone_id);
CREATE INDEX idx_events_sensor_type ON telemetry_events(sensor_type);


-- 2. Aggregates (5 minutes)
-- Tumbling window aggregates
CREATE TABLE IF NOT EXISTS telemetry_agg_5m (
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    zone_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    avg_value FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    count_events INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (window_start, site_id, zone_id, sensor_type)
);

-- 3. Aggregates (15 minutes)
CREATE TABLE IF NOT EXISTS telemetry_agg_15m (
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    zone_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    avg_value FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    count_events INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (window_start, site_id, zone_id, sensor_type)
);

-- 4. Alerts
-- Stores triggered alerts (e.g., CO2 > 1000)
CREATE TABLE IF NOT EXISTS telemetry_alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id VARCHAR(50) NOT NULL,
    zone_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- e.g., 'CO2_HIGH'
    threshold FLOAT,
    value FLOAT,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved boolean DEFAULT FALSE
);

CREATE INDEX idx_alerts_site_zone ON telemetry_alerts(site_id, zone_id);
CREATE INDEX idx_alerts_triggered_at ON telemetry_alerts(triggered_at);
