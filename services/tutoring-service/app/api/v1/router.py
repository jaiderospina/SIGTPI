from fastapi import APIRouter
from app.api.v1.endpoints import health, assignments

router = APIRouter()
router.include_router(health.router,      prefix="/health-detail", tags=["Health"])
router.include_router(assignments.router, prefix="/assignments",   tags=["Asignaciones y Comités"])
