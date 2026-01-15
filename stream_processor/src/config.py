import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_EVENTS: str = os.getenv("KAFKA_TOPIC_EVENTS", "telemetry.events")
    KAFKA_TOPIC_DLQ: str = os.getenv("KAFKA_TOPIC_DLQ", "telemetry.dlq")
    KAFKA_GROUP_ID: str = os.getenv("KAFKA_GROUP_ID", "telemetry-processor-group")
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:password@postgres:5432/telemetry")

    class Config:
        env_case_sensitive = True

settings = Settings()
