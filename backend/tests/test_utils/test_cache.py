"""
Comprehensive tests for cache implementations (MemoryCache and RedisCache).
"""

import asyncio

import pytest
import pytest_asyncio

from app.utils.cache import MemoryCache, RedisCache


class TestMemoryCache:
    """Test MemoryCache implementation."""

    @pytest_asyncio.fixture
    async def memory_cache(self):
        """Create MemoryCache instance for testing."""
        return MemoryCache(default_ttl=60)

    @pytest.mark.asyncio
    async def test_set_and_get(self, memory_cache):
        """Test basic set and get operations."""
        await memory_cache.set("test_key", "test_value")
        result = await memory_cache.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, memory_cache):
        """Test getting a key that doesn't exist."""
        result = await memory_cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, memory_cache):
        """Test setting a key with TTL."""
        await memory_cache.set("ttl_key", "ttl_value", ttl=2)
        result = await memory_cache.get("ttl_key")
        assert result == "ttl_value"

        # Wait for expiration
        await asyncio.sleep(2.1)
        result = await memory_cache.get("ttl_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_setex(self, memory_cache):
        """Test setex method (Redis-compatible)."""
        await memory_cache.setex("setex_key", 2, "setex_value")
        result = await memory_cache.get("setex_key")
        assert result == "setex_value"

        # Wait for expiration
        await asyncio.sleep(2.1)
        result = await memory_cache.get("setex_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing_key(self, memory_cache):
        """Test deleting an existing key."""
        await memory_cache.set("delete_key", "delete_value")
        result = await memory_cache.delete("delete_key")
        assert result is True

        # Key should not exist after deletion
        value = await memory_cache.get("delete_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, memory_cache):
        """Test deleting a key that doesn't exist."""
        result = await memory_cache.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, memory_cache):
        """Test checking if key exists."""
        await memory_cache.set("exists_key", "exists_value")
        assert await memory_cache.exists("exists_key") is True
        assert await memory_cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_exists_expired_key(self, memory_cache):
        """Test that exists returns False for expired keys."""
        await memory_cache.set("expired_key", "value", ttl=1)
        assert await memory_cache.exists("expired_key") is True

        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await memory_cache.exists("expired_key") is False

    @pytest.mark.asyncio
    async def test_clear(self, memory_cache):
        """Test clearing all cache entries."""
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")
        await memory_cache.set("key3", "value3")

        result = await memory_cache.clear()
        assert result is True

        # All keys should be gone
        assert await memory_cache.get("key1") is None
        assert await memory_cache.get("key2") is None
        assert await memory_cache.get("key3") is None

    @pytest.mark.asyncio
    async def test_default_ttl(self, memory_cache):
        """Test that default TTL is applied when not specified."""
        # Create cache with 2-second default TTL
        cache = MemoryCache(default_ttl=2)
        await cache.set("default_ttl_key", "value")

        # Should exist immediately
        assert await cache.get("default_ttl_key") == "value"

        # Wait for expiration
        await asyncio.sleep(2.1)
        assert await cache.get("default_ttl_key") is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, memory_cache):
        """Test that expired entries are cleaned up."""
        await memory_cache.set("expire1", "value1", ttl=1)
        await memory_cache.set("expire2", "value2", ttl=1)
        await memory_cache.set("permanent", "value3", ttl=100)

        # All should exist initially
        assert await memory_cache.exists("expire1") is True
        assert await memory_cache.exists("expire2") is True
        assert await memory_cache.exists("permanent") is True

        # Wait for first two to expire
        await asyncio.sleep(1.1)

        # Trigger cleanup by calling get
        await memory_cache.get("permanent")

        # Expired keys should be cleaned up
        assert await memory_cache.exists("expire1") is False
        assert await memory_cache.exists("expire2") is False
        assert await memory_cache.exists("permanent") is True


class TestRedisCache:
    """Test RedisCache implementation using pytest-mock-resources."""

    @pytest_asyncio.fixture
    async def redis_cache(self, redis_client):
        """Create RedisCache instance for testing."""

        # Create cache with injected client
        cache = RedisCache(redis_client=redis_client)

        yield cache

        # Cleanup
        await cache.clear()

    @pytest.mark.asyncio
    async def test_set_and_get(self, redis_cache):
        """Test basic set and get operations."""
        await redis_cache.set("test_key", "test_value")
        result = await redis_cache.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, redis_cache):
        """Test getting a key that doesn't exist."""
        result = await redis_cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, redis_cache):
        """Test setting a key with TTL."""
        await redis_cache.set("ttl_key", "ttl_value", ttl=2)
        result = await redis_cache.get("ttl_key")
        assert result == "ttl_value"

        # Wait for expiration
        await asyncio.sleep(2.1)
        result = await redis_cache.get("ttl_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_setex(self, redis_cache):
        """Test setex method."""
        result = await redis_cache.setex("setex_key", 2, "setex_value")
        assert result is True

        value = await redis_cache.get("setex_key")
        assert value == "setex_value"

        # Wait for expiration
        await asyncio.sleep(2.1)
        value = await redis_cache.get("setex_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete_existing_key(self, redis_cache):
        """Test deleting an existing key."""
        await redis_cache.set("delete_key", "delete_value")
        result = await redis_cache.delete("delete_key")
        assert result is True

        # Key should not exist after deletion
        value = await redis_cache.get("delete_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, redis_cache):
        """Test deleting a key that doesn't exist."""
        result = await redis_cache.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, redis_cache):
        """Test checking if key exists."""
        await redis_cache.set("exists_key", "exists_value")
        assert await redis_cache.exists("exists_key") is True
        assert await redis_cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_exists_expired_key(self, redis_cache):
        """Test that exists returns False for expired keys."""
        await redis_cache.setex("expired_key", 1, "value")
        assert await redis_cache.exists("expired_key") is True

        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await redis_cache.exists("expired_key") is False

    @pytest.mark.asyncio
    async def test_clear(self, redis_cache):
        """Test clearing all cache entries."""
        await redis_cache.set("key1", "value1")
        await redis_cache.set("key2", "value2")
        await redis_cache.set("key3", "value3")

        result = await redis_cache.clear()
        assert result is True

        # All keys should be gone
        assert await redis_cache.get("key1") is None
        assert await redis_cache.get("key2") is None
        assert await redis_cache.get("key3") is None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, redis_cache):
        """Test concurrent cache operations."""

        async def set_and_get(key: str, value: str):
            await redis_cache.set(key, value)
            return await redis_cache.get(key)

        # Run multiple operations concurrently
        results = await asyncio.gather(
            set_and_get("concurrent_1", "value1"),
            set_and_get("concurrent_2", "value2"),
            set_and_get("concurrent_3", "value3"),
            set_and_get("concurrent_4", "value4"),
            set_and_get("concurrent_5", "value5"),
        )

        assert results == ["value1", "value2", "value3", "value4", "value5"]

    @pytest.mark.asyncio
    async def test_set_without_ttl(self, redis_cache):
        """Test setting a key without TTL (should persist)."""
        await redis_cache.set("no_ttl_key", "no_ttl_value")
        result = await redis_cache.get("no_ttl_key")
        assert result == "no_ttl_value"

        # Wait a bit to ensure it doesn't expire
        await asyncio.sleep(1)
        result = await redis_cache.get("no_ttl_key")
        assert result == "no_ttl_value"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test that errors are handled gracefully."""

        # Create an invalid redis client to trigger errors
        class InvalidRedisClient:
            async def get(self, key):
                raise ConnectionError("Connection failed")

            async def aclose(self):
                pass

            async def flushdb(self):
                pass

        # Inject invalid client
        invalid_client = InvalidRedisClient()
        redis_cache = RedisCache(redis_client=invalid_client)

        # Should return None on error, not raise exception
        result = await redis_cache.get("error_key")
        assert result is None
