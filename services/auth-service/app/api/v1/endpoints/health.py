"""Health detail endpoint for auth-service."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()


@router.get("/db", summary="Database connectivity check")
async def check_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"database": "ok"}
    except Exception as e:
        return {"database": "error", "detail": str(e)}
