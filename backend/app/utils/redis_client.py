"""
Redis client factory and dependency injection utilities.

This module provides functions for creating and managing Redis client instances
that can be used for various Redis operations including caching, pub/sub,
queues, sessions, distributed locks, and more.
"""

from functools import cache

from redis.asyncio import ConnectionPool, Redis

from app.config import get_settings


@cache
def get_redis_pool() -> ConnectionPool:
    """Get the Redis connection pool"""
    settings = get_settings()
    return ConnectionPool.from_url(url=settings.redis_url, decode_responses=True)


@cache
def get_redis_client() -> Redis:
    """Get the Redis client"""
    settings = get_settings()
    client = Redis(connection_pool=get_redis_pool(), max_connections=settings.redis_max_connections)
    return client
