from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.basic import get_db_session
from app.utils.cache import CacheProtocol, get_cache

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "Personal Daily Reading Digest Backend"}


@router.get("/ready")
async def readiness_check(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    cache: Annotated[CacheProtocol, Depends(get_cache)],
):
    try:
        await db.exec(text("SELECT 1"))
        await cache.set("health_check", "ok", ttl=10)
        cache_test = await cache.get("health_check")

        return {
            "status": "ready",
            "database": "connected",
            "cache": "connected" if cache_test == "ok" else "error",
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not ready") from e
