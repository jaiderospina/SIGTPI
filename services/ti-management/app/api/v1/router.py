from fastapi import APIRouter
from app.api.v1.endpoints import health, research_works

router = APIRouter()
router.include_router(health.router,          prefix="/health-detail", tags=["Health"])
router.include_router(research_works.router,  prefix="/ti",            tags=["Trabajos de Investigación"])
