"""Database engine and session factory for auth-service."""
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


async def create_tables():
    """Create auth tables in public schema (default)."""
    from sigtpi_common.utils.database import Base
    import app.models  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
