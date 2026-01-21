from confluent_kafka import Consumer, KafkaException
from src.config import settings
from src.utils.logger import setup_logger
from src.db.session import SessionLocal
from src.db.models import RawEvent, Aggregate5m, Alert
from src.services.alerting import AlertingService
from src.services.aggregation import AggregationService
import json
import pandas as pd
from datetime import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = setup_logger("stream_processor")

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

def process_event(event_data: dict, session):
    # 1. Raw Insert
    # Check idempotency
    exists = session.query(RawEvent).filter_by(event_id=event_data['event_id']).first()
    if exists: return

    raw = RawEvent(
        event_id=event_data['event_id'],
        device_id=event_data['device_id'],
        site_id=event_data['site_id'],
        zone_id=event_data['zone_id'],
        sensor_type=event_data['sensor_type'],
        value=event_data['value'],
        ts_event=datetime.fromisoformat(event_data['ts_event'])
    )
    session.add(raw)
    
    # 2. Check Alerts
    alert_data = AlertingService.check_thresholds(event_data)
    if alert_data:
        alert = Alert(**alert_data)
        session.add(alert)
    
    session.commit()

def run_processor():
    conf = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': settings.KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest',
        'security.protocol': settings.KAFKA_SECURITY_PROTOCOL,
        'sasl.mechanism': settings.KAFKA_SASL_MECHANISM,
        'sasl.username': settings.KAFKA_SASL_USERNAME,
        'sasl.password': settings.KAFKA_SASL_PASSWORD,
    }
    
    # SSL Setup reuse from logic - ideally shared, but inline for now
    if settings.KAFKA_SSL_CA:
        import tempfile
        def write_temp(content):
            t = tempfile.NamedTemporaryFile(delete=False, mode='w')
            t.write(content)
            t.close()
            return t.name
        conf['ssl.ca.location'] = write_temp(settings.KAFKA_SSL_CA)
        conf['ssl.certificate.location'] = write_temp(settings.KAFKA_SSL_CERT)
        conf['ssl.key.location'] = write_temp(settings.KAFKA_SSL_KEY)
        conf['security.protocol'] = 'SSL'

    consumer = Consumer(conf)
    consumer.subscribe([settings.KAFKA_TOPIC_EVENTS])
    
    logger.info(f"Subscribed to {settings.KAFKA_TOPIC_EVENTS}")

    session = SessionLocal()
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue
            
            try:
                data = json.loads(msg.value().decode('utf-8'))
                process_event(data, session)
            except Exception as e:
                logger.error(f"Failed to process msg: {e}")
                session.rollback()
    finally:
        session.close()
        consumer.close()

if __name__ == "__main__":
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    run_processor()
