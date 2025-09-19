from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.cache import CacheProtocol, get_cache

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "Personal Daily Reading Digest Backend"}


@router.get("/ready")
async def readiness_check(
    db: Annotated[AsyncSession, Depends(get_db)],
    cache: Annotated[CacheProtocol, Depends(get_cache)],
):
    try:
        await db.execute(text("SELECT 1"))
        await cache.set("health_check", "ok", ttl=10)
        cache_test = await cache.get("health_check")

        return {
            "status": "ready",
            "database": "connected",
            "cache": "connected" if cache_test == "ok" else "error",
        }
    except Exception as e:
        return {"status": "not ready", "error": str(e)}
