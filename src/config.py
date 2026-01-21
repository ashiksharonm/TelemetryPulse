import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Config
    ENV: str = os.getenv("ENV", "production")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:password@postgres:5432/telemetry")
    
    # Kafka Clusters
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_SECURITY_PROTOCOL: str = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    KAFKA_SASL_MECHANISM: str = os.getenv("KAFKA_SASL_MECHANISM", "SCRAM-SHA-256")
    KAFKA_SASL_USERNAME: str = os.getenv("KAFKA_SASL_USERNAME", "")
    KAFKA_SASL_PASSWORD: str = os.getenv("KAFKA_SASL_PASSWORD", "")
    
    # SSL Auth (Aiven)
    KAFKA_SSL_CA: str = os.getenv("KAFKA_SSL_CA", "")
    KAFKA_SSL_CERT: str = os.getenv("KAFKA_SSL_CERT", "")
    KAFKA_SSL_KEY: str = os.getenv("KAFKA_SSL_KEY", "")

    # Kafka Topics & Consumer
    KAFKA_TOPIC_EVENTS: str = os.getenv("KAFKA_TOPIC", "telemetry.events")
    KAFKA_TOPIC_DLQ: str = os.getenv("KAFKA_TOPIC_DLQ", "telemetry.dlq")
    KAFKA_GROUP_ID: str = os.getenv("KAFKA_GROUP_ID", "telemetry-processor-group")
    
    # Simulation Defaults
    EVENTS_PER_SECOND: int = int(os.getenv("EVENTS_PER_SECOND", "5"))
    NUM_SITES: int = 3
    ZONES_PER_SITE: int = 5
    DEVICES_PER_ZONE: int = 3

    class Config:
        env_case_sensitive = True

settings = Settings()
