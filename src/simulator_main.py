from src.services.ingest_service import ingest_service
from src.utils.logger import setup_logger
from src.config import settings
import time
import random
import uuid
from datetime import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = setup_logger("simulator")

# --- Dummy Server for Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_server():
    port = int(settings.PORT) if hasattr(settings, 'PORT') and settings.PORT else 10000
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Starting dummy HTTP server on port {port}")
    server.serve_forever()
# -------------------------------

def generate_event(site_id, zone_id, device_id):
    sensor_types = ['co2', 'temperature', 'humidity', 'occupancy']
    sensor = random.choice(sensor_types)
    
    value = 0.0
    if sensor == 'co2': value = random.uniform(400, 1200)
    elif sensor == 'temperature': value = random.uniform(18, 32)
    elif sensor == 'humidity': value = random.uniform(30, 90)
    elif sensor == 'occupancy': value = random.randint(0, 15)
    
    return {
        "event_id": str(uuid.uuid4()),
        "device_id": device_id,
        "site_id": site_id,
        "zone_id": zone_id,
        "sensor_type": sensor,
        "value": round(value, 2),
        "ts_event": datetime.utcnow().isoformat()
    }

def run_simulator():
    logger.info("Starting Simulator Loop...")
    
    # Pre-generate heavy device list
    devices = []
    for s in range(1, settings.NUM_SITES + 1):
        for z in range(1, settings.ZONES_PER_SITE + 1):
            for d in range(1, settings.DEVICES_PER_ZONE + 1):
                devices.append({
                    "site": f"site-{s:02d}",
                    "zone": f"zone-{z:02d}",
                    "id": f"dev-{s}-{z}-{d}"
                })
    
    while True:
        # Batch send 5 events
        for _ in range(settings.EVENTS_PER_SECOND):
            target = random.choice(devices)
            evt = generate_event(target['site'], target['zone'], target['id'])
            ingest_service.send_event(evt)
        
        # Flush occasionally
        ingest_service.flush()
        time.sleep(1.0)

if __name__ == "__main__":
    # Start Health Server in background (for Render)
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    
    run_simulator()
