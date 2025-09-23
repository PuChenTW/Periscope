from functools import cache

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings


@cache
def create_engine_and_session():
    """Create the async engine and session maker."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)

    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, async_session
