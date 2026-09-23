from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_SEARCH_PATH = (
    "public,users,academic,tutoring,ti,"
    "sessions,evaluation,documents,notif,pki"
)

_CONNECT_ARGS = {
    "server_settings": {"search_path": _SEARCH_PATH}
}


def build_engine(database_url: str, echo: bool = False):
    """Create async engine with search_path set via asyncpg server_settings."""
    return create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args=_CONNECT_ARGS,
    )


def build_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
