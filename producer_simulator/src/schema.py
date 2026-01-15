from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class TelemetryEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    device_id: str
    site_id: str
    zone_id: str
    sensor_type: str  # 'co2', 'temperature', 'humidity', 'occupancy'
    value: float
    ts_event: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            # Ensure proper JSON serialization for UUID and datetime if not handled by default in Pydantic v2 .model_dump_json()
        }
