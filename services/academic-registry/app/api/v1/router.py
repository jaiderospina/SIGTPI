from fastapi import APIRouter
from app.api.v1.endpoints import health, programs, enrollments

router = APIRouter()
router.include_router(health.router,       prefix="/health-detail", tags=["Health"])
router.include_router(programs.router,     prefix="/programs",      tags=["Programas"])
router.include_router(enrollments.router,  prefix="/enrollments",   tags=["Matrículas y Notas"])
