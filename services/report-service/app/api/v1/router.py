from fastapi import APIRouter
from app.api.v1.endpoints import health, reports

router = APIRouter()
router.include_router(health.router,  prefix="/health-detail", tags=["Health"])
router.include_router(reports.router, prefix="/reports",       tags=["Reportes y KPIs"])
