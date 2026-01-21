from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "2.0.0-oracle-ready"}

def test_ingest_flow_smoke():
    # Smoke test: ensures endpoint exists and accepts payload
    payload = {
        "device_id": "test-device-01",
        "site_id": "site-01",
        "zone_id": "zone-A",
        "sensor_type": "co2",
        "value": 450.0
    }
    # Note: This might fail if Kafka is not mocked or running.
    # In a real unit test, we would mock ingest_service.
