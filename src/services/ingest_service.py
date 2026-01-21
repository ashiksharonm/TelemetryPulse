from confluent_kafka import Producer
from src.config import settings
from src.utils.logger import setup_logger
import json

logger = setup_logger("ingest_service")

class IngestService:
    def __init__(self):
        conf = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'security.protocol': settings.KAFKA_SECURITY_PROTOCOL,
            'sasl.mechanism': settings.KAFKA_SASL_MECHANISM,
            'sasl.username': settings.KAFKA_SASL_USERNAME,
            'sasl.password': settings.KAFKA_SASL_PASSWORD,
        }
        
        # SSL Setup (Aiven)
        if settings.KAFKA_SSL_CA:
            import tempfile
            def write_temp(content):
                import base64
                t = tempfile.NamedTemporaryFile(delete=False, mode='w')
                t.write(content if not 'BEGIN CERTIFICATE' in content else content) # Basic check, ideally decode if b64
                t.close()
                return t.name
            
            conf['ssl.ca.location'] = write_temp(settings.KAFKA_SSL_CA)
            conf['ssl.certificate.location'] = write_temp(settings.KAFKA_SSL_CERT)
            conf['ssl.key.location'] = write_temp(settings.KAFKA_SSL_KEY)
            conf['security.protocol'] = 'SSL'

        self.producer = Producer(conf)

    def send_event(self, event: dict):
        try:
            self.producer.produce(
                settings.KAFKA_TOPIC_EVENTS,
                key=event['device_id'],
                value=json.dumps(event)
            )
            self.producer.poll(0)
            return True
        except Exception as e:
            logger.error(f"Failed to produce event: {e}")
            return False

    def flush(self):
        self.producer.flush()

ingest_service = IngestService()
