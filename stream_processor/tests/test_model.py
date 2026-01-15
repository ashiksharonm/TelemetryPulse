import pytest
from uuid import uuid4
from datetime import datetime
from src.model import TelemetryEvent
from pydantic import ValidationError

def test_telemetry_event_valid():
    data = {
        "event_id": str(uuid4()),
        "device_id": "test-device",
        "site_id": "test-site",
        "zone_id": "test-zone",
        "sensor_type": "co2",
        "value": 450.5,
        "ts_event": datetime.utcnow().isoformat()
    }
    event = TelemetryEvent(**data)
    assert event.device_id == "test-device"
    assert event.value == 450.5

def test_telemetry_event_invalid_missing_field():
    data = {
        "device_id": "test-device",
        # missing site_id, zone_id etc
    }
    with pytest.raises(ValidationError):
        TelemetryEvent(**data)
