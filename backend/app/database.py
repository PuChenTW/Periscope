from collections.abc import AsyncGenerator
from functools import cache

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings


@cache
def get_engine():
    settings = get_settings()
    return create_async_engine(settings.database.url, echo=settings.debug, future=True)


@cache
def get_async_sessionmaker():
    return async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    session_maker = get_async_sessionmaker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
