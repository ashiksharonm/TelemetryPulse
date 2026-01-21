from fastapi import FastAPI
from src.api.routes import router
from src.utils.logger import setup_logger
from contextlib import asynccontextmanager

logger = setup_logger("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: API is live")
    yield
    logger.info("Shutdown: API is stopping")

app = FastAPI(
    title="TelemetryPulse Oracle Edition",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(router)
