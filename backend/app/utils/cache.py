import threading
import time
from abc import ABC, abstractmethod


class CacheProtocol(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
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
        expired_keys = [
            key
            for key, expiry_time in self._expiry.items()
            if expiry_time <= current_time
        ]
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


cache_instance: CacheProtocol = MemoryCache()


async def get_cache() -> CacheProtocol:
    return cache_instance
