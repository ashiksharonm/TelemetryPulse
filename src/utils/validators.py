from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import uuid

class TelemetryPayload(BaseModel):
    event_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    site_id: str
    zone_id: str
    sensor_type: str = Field(pattern="^(co2|temperature|humidity|occupancy)$")
    value: float
    ts_event: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('value')
    @classmethod
    def validate_value_range(cls, v, info):
        # Basic sanity checks
        if info.data.get('sensor_type') == 'humidity' and (v < 0 or v > 100):
            raise ValueError("Humidity must be between 0 and 100")
        return v
