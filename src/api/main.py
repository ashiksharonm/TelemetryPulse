from fastapi import FastAPI, Request
from src.api.routes import router
from src.utils.logger import setup_logger
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
import time
import uuid

logger = setup_logger("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: API is live")
    yield
    logger.info("Shutdown: API is stopping")

app = FastAPI(
    title="TelemetryPulse API",
    version="1.0.0",
    lifespan=lifespan
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.middleware("http")
async def structured_log_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        "Request processed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": round(process_time * 1000, 2)
        }
    )
    return response

app.include_router(router)
