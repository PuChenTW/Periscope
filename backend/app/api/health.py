from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession
from temporalio.client import Client

from app.database import get_async_session
from app.temporal.client import get_temporal_client
from app.utils.redis_client import get_redis_client

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "Personal Daily Reading Digest Backend"}


@router.get("/ready")
async def readiness_check(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    redis: Annotated[Redis, Depends(get_redis_client)],
    temporal_client: Annotated[Client, Depends(get_temporal_client)],
):
    try:
        await session.exec(text("SELECT 1"))
        await redis.ping()
        health = await temporal_client.service_client.check_health()
        if not health:
            raise Exception("Temporal service is not healthy")

        return {
            "status": "ready",
            "database": "connected",
            "cache": "connected",
            "temporal": "connected",
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not ready") from e
