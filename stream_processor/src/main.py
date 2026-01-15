import sys
import logging
import json
import socket
from confluent_kafka import Consumer, Producer, KafkaException, KafkaError

from stream_processor.src.config import settings
from stream_processor.src.model import TelemetryEvent
from datetime import datetime, timedelta
from uuid import uuid4
from pydantic import ValidationError
from stream_processor.src.db import insert_event, insert_alert, upsert_aggregate_5m, upsert_aggregate_15m

# ... imports ...

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("stream_processor")

def get_kafka_config(base_conf):
    conf = base_conf.copy()
    if settings.KAFKA_SASL_USERNAME:
        conf.update({
            'security.protocol': settings.KAFKA_SECURITY_PROTOCOL,
            'sasl.mechanism': settings.KAFKA_SASL_MECHANISM,
            'sasl.username': settings.KAFKA_SASL_USERNAME,
            'sasl.password': settings.KAFKA_SASL_PASSWORD,
        })
    elif settings.KAFKA_SSL_CA:
        import tempfile
        def create_temp_cert(content):
            t = tempfile.NamedTemporaryFile(delete=False, mode='w')
            t.write(content)
            t.close()
            return t.name

        ca_path = create_temp_cert(settings.KAFKA_SSL_CA)
        cert_path = create_temp_cert(settings.KAFKA_SSL_CERT)
        key_path = create_temp_cert(settings.KAFKA_SSL_KEY)

        conf.update({
            'security.protocol': 'SSL',
            'ssl.ca.location': ca_path,
            'ssl.certificate.location': cert_path,
            'ssl.key.location': key_path,
        })
    return conf

def create_consumer():
    base_conf = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': settings.KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }
    return Consumer(get_kafka_config(base_conf))

def create_producer():
    base_conf = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'client.id': socket.gethostname()
    }
    return Producer(get_kafka_config(base_conf))

dlq_producer = create_producer()

def send_to_dlq(raw_msg, error_msg):
    try:
        err_payload = {
            "error": str(error_msg),
            "original_payload": raw_msg.decode('utf-8', errors='ignore')
        }
        dlq_producer.produce(
            settings.KAFKA_TOPIC_DLQ,
            value=json.dumps(err_payload).encode('utf-8')
        )
        dlq_producer.poll(0)
    except Exception as e:
        logger.error(f"Failed to send to DLQ: {e}")

def process_alerts(event: TelemetryEvent):
    if event.sensor_type == 'co2' and event.value > 1000.0:
        alert = {
            "alert_id": uuid4(),
            "site_id": event.site_id,
            "zone_id": event.zone_id,
            "alert_type": "CO2_HIGH",
            "threshold": 1000.0,
            "value": event.value,
            "triggered_at": event.ts_event,
            "resolved": False
        }
        insert_alert(alert)

def process_aggregates(event: TelemetryEvent):
    # Calculate Window Starts
    # Timestamp is in UTC.
    ts = event.ts_event.timestamp()
    
    # 5 Minute Window
    start_5m_ts = (ts // 300) * 300
    start_5m = datetime.fromtimestamp(start_5m_ts)
    end_5m = start_5m + timedelta(minutes=5)
    
    upsert_aggregate_5m({
        "window_start": start_5m,
        "window_end": end_5m,
        "site_id": event.site_id,
        "zone_id": event.zone_id,
        "sensor_type": event.sensor_type,
        "value": event.value
    })

    # 15 Minute Window
    start_15m_ts = (ts // 900) * 900
    start_15m = datetime.fromtimestamp(start_15m_ts)
    end_15m = start_15m + timedelta(minutes=15)
    
    upsert_aggregate_15m({
        "window_start": start_15m,
        "window_end": end_15m,
        "site_id": event.site_id,
        "zone_id": event.zone_id,
        "sensor_type": event.sensor_type,
        "value": event.value
    })

def consumer_loop():
    consumer = create_consumer()
    try:
        consumer.subscribe([settings.KAFKA_TOPIC_EVENTS])
        logger.info(f"Subscribed to {settings.KAFKA_TOPIC_EVENTS}")

        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

            try:
                payload = msg.value()
                data = json.loads(payload)
                
                # Validation
                event = TelemetryEvent(**data)
                
                # 1. Raw Insertion
                insert_event(event.model_dump())
                
                # 2. Alerts
                process_alerts(event)
                
                # 3. Aggregates
                process_aggregates(event)
                
                # Commit offset
                consumer.commit(message=msg, asynchronous=True)

            except ValidationError as ve:
                logger.warning(f"Validation Error: {ve}")
                send_to_dlq(msg.value(), f"Validation Error: {ve}")
                consumer.commit(message=msg, asynchronous=True) 
                
            except json.JSONDecodeError as je:
                logger.warning(f"JSON Error: {je}")
                send_to_dlq(msg.value(), f"JSON Error: {je}")
                consumer.commit(message=msg, asynchronous=True)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")

    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
    finally:
        consumer.close()
        dlq_producer.flush()

def main():
    import threading
    import os
    from http.server import HTTPServer, BaseHTTPRequestHandler

    # Start consumer in background
    logger.info("Starting consumer loop in background thread...")
    t = threading.Thread(target=consumer_loop, daemon=True)
    t.start()

    # Dummy HTTP server
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Starting dummy HTTP server on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    main()
