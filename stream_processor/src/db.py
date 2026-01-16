from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from stream_processor.src.config import settings
import logging

logger = logging.getLogger("stream_processor.db")

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def insert_event(event_data: dict):
    """
    Inserts a raw event into telemetry_events.
    Idempotent: If event_id exists, does nothing.
    """
    query = text("""
        INSERT INTO telemetry_events (event_id, device_id, site_id, zone_id, sensor_type, value, ts_event)
        VALUES (:event_id, :device_id, :site_id, :zone_id, :sensor_type, :value, :ts_event)
        ON CONFLICT (event_id) DO NOTHING
    """)
    
    with SessionLocal() as session:
        try:
            session.execute(query, event_data)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting event into DB: {e}")
            raise e

def insert_alert(alert_data: dict):
    query = text("""
        INSERT INTO telemetry_alerts (alert_id, site_id, zone_id, alert_type, threshold, value, triggered_at, resolved)
        VALUES (:alert_id, :site_id, :zone_id, :alert_type, :threshold, :value, :triggered_at, :resolved)
    """)
    with SessionLocal() as session:
        try:
            session.execute(query, alert_data)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting alert: {e}")
            raise e

def upsert_aggregate_5m(agg_data: dict):
    # agg_data must contain: window_start, window_end, site_id, zone_id, sensor_type, value
    # We pass 'value' as avg, min, max for the initial row.
    query = text("""
        INSERT INTO telemetry_agg_5m (window_start, window_end, site_id, zone_id, sensor_type, avg_value, min_value, max_value, count_events)
        VALUES (:window_start, :window_end, :site_id, :zone_id, :sensor_type, :value, :value, :value, 1)
        ON CONFLICT (window_start, site_id, zone_id, sensor_type)
        DO UPDATE SET
            avg_value = (telemetry_agg_5m.avg_value * telemetry_agg_5m.count_events + EXCLUDED.avg_value) / (telemetry_agg_5m.count_events + 1),
            min_value = LEAST(telemetry_agg_5m.min_value, EXCLUDED.min_value),
            max_value = GREATEST(telemetry_agg_5m.max_value, EXCLUDED.max_value),
            count_events = telemetry_agg_5m.count_events + 1
    """)
    with SessionLocal() as session:
        try:
            session.execute(query, agg_data)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error upserting 5m agg: {e}")
            raise e

def upsert_aggregate_15m(agg_data: dict):
    query = text("""
        INSERT INTO telemetry_agg_15m (window_start, window_end, site_id, zone_id, sensor_type, avg_value, min_value, max_value, count_events)
        VALUES (:window_start, :window_end, :site_id, :zone_id, :sensor_type, :value, :value, :value, 1)
        ON CONFLICT (window_start, site_id, zone_id, sensor_type)
        DO UPDATE SET
            avg_value = (telemetry_agg_15m.avg_value * telemetry_agg_15m.count_events + EXCLUDED.avg_value) / (telemetry_agg_15m.count_events + 1),
            min_value = LEAST(telemetry_agg_15m.min_value, EXCLUDED.min_value),
            max_value = GREATEST(telemetry_agg_15m.max_value, EXCLUDED.max_value),
            count_events = telemetry_agg_15m.count_events + 1
    """)
    with SessionLocal() as session:
        try:
            session.execute(query, agg_data)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error upserting 15m agg: {e}")
            raise e
