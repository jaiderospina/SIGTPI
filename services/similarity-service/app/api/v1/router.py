"""API v1 router for similarity-service."""
from fastapi import APIRouter
from app.api.v1.endpoints import health

router = APIRouter()
router.include_router(health.router, prefix="/health-detail", tags=["Health Detail"])
# Uncomment as endpoints are implemented:
# from app.api.v1.endpoints import <module>
# router.include_router(<module>.router, prefix="/<prefix>", tags=["<Tag>"])
