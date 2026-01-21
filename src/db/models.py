from sqlalchemy import Column, String, Float, DateTime, Integer, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class RawEvent(Base):
    __tablename__ = "telemetry_events"

    event_id = Column(String, primary_key=True)
    device_id = Column(String, index=True)
    site_id = Column(String)
    zone_id = Column(String)
    sensor_type = Column(String)
    value = Column(Float)
    ts_event = Column(DateTime, index=True)  # Index on timestamp

class Aggregate5m(Base):
    __tablename__ = "telemetry_agg_5m"
    
    # Composite Primary Key for window + granularity
    window_start = Column(DateTime, primary_key=True)
    site_id = Column(String, primary_key=True)
    zone_id = Column(String, primary_key=True)
    sensor_type = Column(String, primary_key=True)
    
    window_end = Column(DateTime)
    avg_value = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)
    count_events = Column(Integer)

class Alert(Base):
    __tablename__ = "telemetry_alerts"
    
    alert_id = Column(String, primary_key=True)
    site_id = Column(String)
    zone_id = Column(String)
    alert_type = Column(String) # e.g. "CO2_HIGH"
    threshold = Column(Float)
    value = Column(Float)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Integer, default=0)
