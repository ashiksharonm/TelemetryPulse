from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.db.models import RawEvent, Alert
from src.api.schemas import IngestResponse, DeviceStats, AlertSchema
from src.utils.validators import TelemetryPayload
from src.services.ingest_service import ingest_service
from typing import List

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_telemetry(payload: TelemetryPayload):
    """
    Accepts telemetry payload and pushes to Kafka.
    """
    success = ingest_service.send_event(payload.model_dump(mode='json'))
    if not success:
        raise HTTPException(status_code=500, detail="Kafka unavailable")
    return {"status": "accepted", "message": "Event queued"}

@router.get("/devices/{device_id}", response_model=DeviceStats)
def get_device_stats(device_id: str, db: Session = Depends(get_db)):
    """
    Returns simple stats for a device (demonstration).
    """
    # Simple query: last event
    last_event = db.query(RawEvent).filter(RawEvent.device_id == device_id).order_by(RawEvent.ts_event.desc()).first()
    if not last_event:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "device_id": device_id,
        "avg_temp": 22.5, # Placeholder for expensive Agg query
        "max_co2": 450.0, # Placeholder
        "last_seen": last_event.ts_event
    }

@router.get("/alerts", response_model=List[AlertSchema])
def get_recent_alerts(limit: int = 10, db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.triggered_at.desc()).limit(limit).all()
    return alerts

@router.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0-oracle-ready"}
