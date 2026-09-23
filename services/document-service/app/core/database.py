"""Database engine and session factory for document-service."""
from sqlalchemy import text
from sigtpi_common.utils.database import build_engine, build_session_factory
from app.core.config import settings

engine = build_engine(settings.database_url, echo=settings.debug)
AsyncSessionLocal = build_session_factory(engine)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def ensure_schema():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS documents"))


async def create_tables():
    from sigtpi_common.utils.database import Base
    import app.models  # noqa
    await ensure_schema()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
