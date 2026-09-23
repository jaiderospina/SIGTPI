from fastapi import APIRouter
from app.api.v1.endpoints import health, documents

router = APIRouter()
router.include_router(health.router,    prefix="/health-detail", tags=["Health"])
router.include_router(documents.router, prefix="/documents",     tags=["Documentos"])
