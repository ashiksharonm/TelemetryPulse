from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class IngestResponse(BaseModel):
    status: str
    message: str

class DeviceStats(BaseModel):
    device_id: str
    avg_temp: Optional[float]
    max_co2: Optional[float]
    last_seen: datetime

class AlertSchema(BaseModel):
    alert_id: str
    alert_type: str
    value: float
    threshold: float
    triggered_at: datetime
    site_id: str
    zone_id: str
