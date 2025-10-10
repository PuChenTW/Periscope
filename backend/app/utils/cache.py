import threading
import time
from abc import ABC, abstractmethod

from loguru import logger
from redis import asyncio as aioredis

from app.config import get_settings
from app.utils.redis_client import get_redis_client


class CacheProtocol(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        pass

    @abstractmethod
    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set key with value and expiration time in seconds (Redis-compatible)."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear(self) -> bool:
        pass


class MemoryCache(CacheProtocol):
    def __init__(self, default_ttl: int = 3600):
        self._cache = {}
        self._expiry = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl

    def _cleanup_expired(self):
        current_time = time.time()
        expired_keys = [key for key, expiry_time in self._expiry.items() if expiry_time <= current_time]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)

    async def get(self, key: str) -> str | None:
        with self._lock:
            self._cleanup_expired()
            return self._cache.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        with self._lock:
            self._cache[key] = value
            if ttl is None:
                ttl = self.default_ttl
            self._expiry[key] = time.time() + ttl
            return True

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set key with value and expiration time in seconds (Redis-compatible)."""
        return await self.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        with self._lock:
            exists = key in self._cache
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
            return exists

    async def exists(self, key: str) -> bool:
        with self._lock:
            self._cleanup_expired()
            return key in self._cache

    async def clear(self) -> bool:
        with self._lock:
            self._cache.clear()
            self._expiry.clear()
            return True


class RedisCache(CacheProtocol):
    """Redis-based cache implementation using injected Redis client."""

    def __init__(self, redis_client: aioredis.Redis):
        """
        Initialize Redis cache with injected Redis client.

        Args:
            redis_client: Redis client instance (manages its own connection pool)
        """
        self.redis_client = redis_client

    async def get(self, key: str) -> str | None:
        """Get value from Redis cache."""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Error getting key '{key}' from Redis: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Set value in Redis cache with optional TTL."""
        try:
            if ttl is not None:
                await self.redis_client.setex(key, ttl, value)
            else:
                await self.redis_client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting key '{key}' in Redis: {e}")
            return False

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set key with value and expiration time in seconds (Redis-compatible)."""
        try:
            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Error setting key '{key}' with TTL in Redis: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key '{key}' from Redis: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error checking existence of key '{key}' in Redis: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all keys in Redis cache."""
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return False


async def get_cache() -> CacheProtocol:
    """
    Get cache instance for dependency injection.

    Creates RedisCache with injected Redis client if REDIS_URL is configured,
    otherwise falls back to MemoryCache.
    """
    try:
        # Create Redis client
        redis_client = await get_redis_client()

        # Test connection
        await redis_client.exists("__connection_test__")

        # Create cache with injected client
        redis_cache = RedisCache(redis_client=redis_client)

        logger.debug("Redis cache created")
        return redis_cache

    except Exception as e:
        logger.warning(f"Failed to create Redis cache: {e}. Falling back to MemoryCache.")
        settings = get_settings()
        return MemoryCache(default_ttl=settings.cache.ttl_minutes * 60)
