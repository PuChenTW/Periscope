from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.basic import get_db_session
from app.utils.redis_client import get_redis_client

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "Personal Daily Reading Digest Backend"}


@router.get("/ready")
async def readiness_check(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis_client)],
):
    try:
        await db.exec(text("SELECT 1"))
        await redis.ping()

        return {
            "status": "ready",
            "database": "connected",
            "cache": "connected",
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not ready") from e
