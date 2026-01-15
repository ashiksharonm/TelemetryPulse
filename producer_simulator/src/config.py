import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "telemetry.events")
    EVENTS_PER_SECOND: int = int(os.getenv("EVENTS_PER_SECOND", "5"))
    
    # Kafka Security
    KAFKA_SASL_USERNAME: str = os.getenv("KAFKA_SASL_USERNAME", "")
    KAFKA_SASL_PASSWORD: str = os.getenv("KAFKA_SASL_PASSWORD", "")
    KAFKA_SECURITY_PROTOCOL: str = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    KAFKA_SASL_MECHANISM: str = os.getenv("KAFKA_SASL_MECHANISM", "SCRAM-SHA-256")
    
    # SSL Auth (Aiven)
    KAFKA_SSL_CA: str = os.getenv("KAFKA_SSL_CA", "")
    KAFKA_SSL_CERT: str = os.getenv("KAFKA_SSL_CERT", "")
    KAFKA_SSL_KEY: str = os.getenv("KAFKA_SSL_KEY", "")


    
    # Simulation Config
    NUM_SITES: int = 3
    ZONES_PER_SITE: int = 5
    DEVICES_PER_ZONE: int = 3

    class Config:
        env_case_sensitive = True

settings = Settings()
