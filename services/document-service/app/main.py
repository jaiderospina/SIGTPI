"""
SIGTPI — Document Service
Document repository, version control, PDF/A
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import router as api_v1_router
from sigtpi_common.utils.logging import configure_logging
from sigtpi_common.schemas.base import HealthResponse

configure_logging(settings.service_name, settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import models so SQLAlchemy registers them (Alembic handles actual table creation)
    import app.models  # noqa: F401
    yield
    from app.core.database import engine
    await engine.dispose()


app = FastAPI(
    title="SIGTPI — Document Service",
    description="Document repository, version control, PDF/A",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version="2.0.0",
        environment=settings.environment,
    )


@app.get("/", include_in_schema=False)
async def root():
    return {"service": settings.service_name, "status": "running", "docs": "/docs"}
