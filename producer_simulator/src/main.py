import time
import random
import json
import logging
import signal
import sys
from datetime import datetime
from uuid import uuid4


from confluent_kafka import Producer
from producer_simulator.src.config import settings
from producer_simulator.src.schema import TelemetryEvent


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("producer_simulator")

# Global flag for shutdown
running = True

def signal_handler(sig, frame):
    global running
    logger.info("Shutdown signal received")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        logger.error(f'Message delivery failed: {err}')
    else:
        # logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')
        pass

def generate_value(sensor_type):
    if sensor_type == 'co2':
        return round(random.uniform(400, 1200), 2)  # ppm
    elif sensor_type == 'temperature':
        return round(random.uniform(18.0, 30.0), 1) # Celsius
    elif sensor_type == 'humidity':
        return round(random.uniform(30.0, 70.0), 1) # Percent
    elif sensor_type == 'occupancy':
        return float(random.choice([0, 1])) # 0 or 1
    return 0.0

def producer_loop():
    logger.info(f"Starting Producer Simulator. Target: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    
    conf = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'client.id': 'python-producer-simulator',
        'queue.buffering.max.messages': 100000,
        'linger.ms': 100 # Batching
    }

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


    producer = Producer(conf)

    # Pre-generate devices structure
    devices = []
    sensor_types = ['co2', 'temperature', 'humidity', 'occupancy']
    
    for s in range(1, settings.NUM_SITES + 1):
        site_id = f"site-{s:02d}"
        for z in range(1, settings.ZONES_PER_SITE + 1):
            zone_id = f"zone-{z:02d}"
            for d in range(1, settings.DEVICES_PER_ZONE + 1):
                device_id = f"{site_id}-{zone_id}-dev-{d:02d}"
                devices.append({
                    "site_id": site_id,
                    "zone_id": zone_id,
                    "device_id": device_id
                })
    
    logger.info(f"Simulating {len(devices)} devices across {settings.NUM_SITES} sites.")

    while running:
        start_time = time.time()
        
        # Batch generation
        for _ in range(settings.EVENTS_PER_SECOND):
            device_cfg = random.choice(devices)
            sensor_type = random.choice(sensor_types)
            
            event = TelemetryEvent(
                event_id=uuid4(),
                device_id=device_cfg['device_id'],
                site_id=device_cfg['site_id'],
                zone_id=device_cfg['zone_id'],
                sensor_type=sensor_type,
                value=generate_value(sensor_type),
                ts_event=datetime.utcnow()
            )

            try:
                # Produce asynchronously
                producer.produce(
                    settings.KAFKA_TOPIC,
                    key=event.device_id.encode('utf-8'), # Key by device_id for partial ordering
                    value=event.model_dump_json().encode('utf-8'),
                    callback=delivery_report
                )
            except BufferError:
                logger.warning("Local buffer full, waiting...")
                producer.poll(1)

        # Serve delivery reports
        producer.poll(0)

        # Sleep to maintain rate
        elapsed = time.time() - start_time
        sleep_time = max(0, 1.0 - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)

    logger.info("Flushing records...")
    producer.flush()
    logger.info("Producer stopped.")

def main():
    import threading
    import os
    from http.server import HTTPServer, BaseHTTPRequestHandler

    # Start producer in background
    logger.info("Starting producer loop in background thread...")
    t = threading.Thread(target=producer_loop, daemon=True)
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
