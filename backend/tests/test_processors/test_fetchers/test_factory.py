"""
Tests for fetcher factory functionality
"""

import pytest

from app.processors.fetchers.base import BaseFetcher, SourceType
from app.processors.fetchers.exceptions import InvalidUrlError
from app.processors.fetchers.factory import (
    FetcherRegistry,
    auto_create_fetcher,
    create_fetcher,
    detect_source_type,
    registry,
)
from app.processors.fetchers.rss import RSSFetcher


class TestFetcherRegistry:
    """Test FetcherRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry is initialized with default fetchers."""
        test_registry = FetcherRegistry()
        test_registry.register(SourceType.RSS, RSSFetcher)

        assert SourceType.RSS in test_registry.list_supported_types()
        assert test_registry.get_fetcher(SourceType.RSS) == RSSFetcher

    def test_register_new_fetcher(self):
        """Test registering a new fetcher type."""
        test_registry = FetcherRegistry()

        class TestFetcher(BaseFetcher):
            @property
            def source_type(self):
                return "test"

            async def validate_url(self, url):
                return True

            async def fetch_content(self, url):
                pass

            async def get_source_info(self, url):
                pass

        test_registry.register("test", TestFetcher)

        assert "test" in test_registry.list_supported_types()
        assert test_registry.get_fetcher("test") == TestFetcher

    def test_get_nonexistent_fetcher(self):
        """Test getting a fetcher type that doesn't exist."""
        test_registry = FetcherRegistry()

        with pytest.raises(ValueError, match="No fetcher registered"):
            test_registry.get_fetcher("nonexistent")

    def test_list_supported_types(self):
        """Test listing supported source types."""
        test_registry = FetcherRegistry()
        test_registry.register(SourceType.RSS, RSSFetcher)
        test_registry.register("blog", RSSFetcher)  # Same class, different type

        types = test_registry.list_supported_types()
        assert SourceType.RSS in types
        assert "blog" in types
        assert len(types) == 2


class TestFetcherFactory:
    """Test factory functions."""

    def test_create_fetcher_rss(self):
        """Test creating RSS fetcher with factory."""
        fetcher = create_fetcher(SourceType.RSS, timeout=30, max_articles=50)

        assert isinstance(fetcher, RSSFetcher)
        assert fetcher.timeout == 30
        assert fetcher.max_articles == 50

    def test_create_fetcher_invalid_type(self):
        """Test creating fetcher with invalid type."""
        with pytest.raises(ValueError, match="No fetcher registered"):
            create_fetcher("invalid_type")

    @pytest.mark.asyncio
    async def test_detect_source_type_rss_indicators(self):
        """Test source type detection with RSS indicators in URL."""
        test_cases = [
            "https://example.com/rss.xml",
            "https://example.com/feed.xml",
            "https://example.com/atom.xml",
            "https://example.com/feeds/all.xml",
            "https://example.com/feed/",
            "https://example.com/rss/",
            "https://blog.example.com/feeds/posts/default",
        ]

        for url in test_cases:
            source_type = await detect_source_type(url)
            assert source_type == SourceType.RSS, f"Failed for URL: {url}"

    @pytest.mark.asyncio
    async def test_detect_source_type_default_rss(self):
        """Test source type detection defaults to RSS."""
        # URLs without obvious RSS indicators should default to RSS
        test_cases = ["https://example.com", "https://blog.example.com/posts", "https://news.example.com/latest"]

        for url in test_cases:
            source_type = await detect_source_type(url)
            assert source_type == SourceType.RSS, f"Failed for URL: {url}"

    @pytest.mark.asyncio
    async def test_detect_source_type_invalid_url(self):
        """Test source type detection with invalid URLs."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com",  # No scheme/netloc
            "https://",  # Missing netloc
        ]

        for url in invalid_urls:
            with pytest.raises(InvalidUrlError):
                await detect_source_type(url)

    @pytest.mark.asyncio
    async def test_auto_create_fetcher(self):
        """Test automatic fetcher creation."""
        url = "https://example.com/feed.xml"

        fetcher = await auto_create_fetcher(url, timeout=45)

        assert isinstance(fetcher, RSSFetcher)
        assert fetcher.source_type == SourceType.RSS
        assert fetcher.timeout == 45

    @pytest.mark.asyncio
    async def test_auto_create_fetcher_with_kwargs(self):
        """Test automatic fetcher creation with custom parameters."""
        url = "https://example.com/rss.xml"

        fetcher = await auto_create_fetcher(url, timeout=60, max_articles=25)

        assert isinstance(fetcher, RSSFetcher)
        assert fetcher.timeout == 60
        assert fetcher.max_articles == 25

    @pytest.mark.asyncio
    async def test_auto_create_fetcher_invalid_url(self):
        """Test automatic fetcher creation with invalid URL."""
        with pytest.raises(InvalidUrlError):
            await auto_create_fetcher("")


class TestGlobalRegistry:
    """Test the global registry instance."""

    def test_global_registry_has_rss(self):
        """Test global registry is initialized with RSS fetcher."""
        assert SourceType.RSS in registry.list_supported_types()
        assert registry.get_fetcher(SourceType.RSS) == RSSFetcher

    def test_global_registry_create_rss_fetcher(self):
        """Test creating RSS fetcher through global registry."""
        fetcher = create_fetcher(SourceType.RSS)
        assert isinstance(fetcher, RSSFetcher)
        assert fetcher.source_type == "rss"
