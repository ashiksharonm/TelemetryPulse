import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "telemetry.events")
    EVENTS_PER_SECOND: int = int(os.getenv("EVENTS_PER_SECOND", "5"))
    
    # Simulation Config
    NUM_SITES: int = 3
    ZONES_PER_SITE: int = 5
    DEVICES_PER_ZONE: int = 3

    class Config:
        env_case_sensitive = True

settings = Settings()
