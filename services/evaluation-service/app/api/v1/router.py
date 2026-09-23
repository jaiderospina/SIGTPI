from fastapi import APIRouter
from app.api.v1.endpoints import health, evaluations

router = APIRouter()
router.include_router(health.router,      prefix="/health-detail", tags=["Health"])
router.include_router(evaluations.router, prefix="/evaluations",   tags=["Evaluaciones y Rúbricas"])
