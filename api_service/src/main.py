from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
from api_service.src.db import get_db


app = FastAPI(title="TelemetryPulse Analytics API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/kpis/live")
def get_live_kpis(site_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get the latest 5-minute aggregate for each sensor in the given site (or all sites).
    This gives a snapshot of 'current' conditions.
    """
    # We'll fetch the most recent window for each (site, zone, sensor)
    # Using DISTINCT ON (site_id, zone_id, sensor_type) ... ORDER BY window_start DESC
    
    where_clause = ""
    params = {}
    if site_id:
        where_clause = "WHERE site_id = :site_id"
        params["site_id"] = site_id

    query = text(f"""
        SELECT DISTINCT ON (site_id, zone_id, sensor_type)
            site_id, zone_id, sensor_type, avg_value, max_value, count_events, window_end
        FROM telemetry_agg_5m
        {where_clause}
        ORDER BY site_id, zone_id, sensor_type, window_start DESC
    """)
    
    result = db.execute(query, params).fetchall()
    
    return [
        {
            "site_id": row.site_id,
            "zone_id": row.zone_id,
            "sensor_type": row.sensor_type,
            "current_avg": row.avg_value,
            "current_max": row.max_value,
            "sample_count": row.count_events,
            "last_updated": row.window_end
        }
        for row in result
    ]

@app.get("/trends")
def get_trends(
    sensor_type: str,
    zone_id: Optional[str] = None,
    window: str = "5m", 
    db: Session = Depends(get_db)
):
    """
    Get historical trends for a specific sensor type.
    """
    table = "telemetry_agg_5m" if window == "5m" else "telemetry_agg_15m"
    
    where_clause = "WHERE sensor_type = :sensor_type"
    params = {"sensor_type": sensor_type}
    
    if zone_id:
        where_clause += " AND zone_id = :zone_id"
        params["zone_id"] = zone_id

    query = text(f"""
        SELECT window_start, avg_value, min_value, max_value
        FROM {table}
        {where_clause}
        ORDER BY window_start DESC
        LIMIT 100
    """)
    
    result = db.execute(query, params).fetchall()
    return [
        {
            "timestamp": row.window_start,
            "avg": row.avg_value,
            "min": row.min_value,
            "max": row.max_value
        }
        for row in result
    ]

@app.get("/alerts/recent")
def get_recent_alerts(limit: int = 20, db: Session = Depends(get_db)):
    query = text("""
        SELECT alert_id, site_id, zone_id, alert_type, value, threshold, triggered_at
        FROM telemetry_alerts
        ORDER BY triggered_at DESC
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit}).fetchall()
    return [
        {
            "alert_id": row.alert_id,
            "site": row.site_id,
            "zone": row.zone_id,
            "type": row.alert_type,
            "value": row.value,
            "threshold": row.threshold,
            "time": row.triggered_at
        }
        for row in result
    ]

@app.get("/utilization/heatmap")
def get_utilization_heatmap(site_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Return average occupancy by zone for the last hour to build a heatmap.
    """
    # Last 1 hour
    
    where_clause = "WHERE sensor_type = 'occupancy' AND window_start > NOW() - INTERVAL '1 hour'"
    params = {}
    
    if site_id:
        where_clause += " AND site_id = :site_id"
        params["site_id"] = site_id

    query = text(f"""
        SELECT site_id, zone_id, AVG(avg_value) as occupancy_rate
        FROM telemetry_agg_15m
        {where_clause}
        GROUP BY site_id, zone_id
    """)
    
    result = db.execute(query, params).fetchall()
    return [
        {
            "site_id": row.site_id,
            "zone_id": row.zone_id,
            "occupancy_rate": row.occupancy_rate
        }
        for row in result
    ]
