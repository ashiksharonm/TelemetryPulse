from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class TelemetryEvent(BaseModel):
    event_id: UUID
    device_id: str
    site_id: str
    zone_id: str
    sensor_type: str
    value: float
    ts_event: datetime
