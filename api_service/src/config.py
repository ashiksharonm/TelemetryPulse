import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:password@postgres:5432/telemetry")

    class Config:
        env_case_sensitive = True

settings = Settings()
