"""
Tests for URL validation utilities
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.processors.fetchers.exceptions import InvalidUrlError, ValidationError
from app.processors.utils.url_validation import check_url_health, is_valid_url, validate_rss_feed
from tests.test_processors.fixtures import EMPTY_RSS_FEED, INVALID_XML, VALID_RSS_FEED


class TestUrlValidation:
    """Test URL validation functions."""

    def test_is_valid_url_valid(self):
        """Test valid URL detection."""
        valid_urls = [
            "https://example.com",
            "http://example.com/path",
            "https://sub.example.com/path?query=value",
            "https://example.com:8080/feed.xml",
            "ftp://files.example.com/file.txt",
        ]

        for url in valid_urls:
            assert is_valid_url(url) is True, f"Should be valid: {url}"

    def test_is_valid_url_invalid(self):
        """Test invalid URL detection."""
        invalid_urls = [
            "",
            "not-a-url",
            "https://",
            "://example.com",
            "example.com",  # Missing scheme
            "https:// ",  # Invalid netloc
        ]

        for url in invalid_urls:
            assert is_valid_url(url) is False, f"Should be invalid: {url}"

    @pytest.mark.asyncio
    async def test_validate_rss_feed_success(self):
        """Test successful RSS feed validation."""
        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await validate_rss_feed("https://example.com/feed.xml")

            assert isinstance(result, dict)
            assert result["title"] == "Test RSS Feed"
            assert result["description"] == "A test RSS feed for unit testing"
            assert result["link"] == "https://example.com"
            assert result["version"] is not None
            assert result["language"] == "en-US"
            assert result["entries_count"] == 3
            assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_validate_rss_feed_invalid_url(self):
        """Test RSS validation with invalid URL."""
        with pytest.raises(InvalidUrlError, match="Invalid URL"):
            await validate_rss_feed("not-a-url")

    @pytest.mark.asyncio
    async def test_validate_rss_feed_no_entries(self):
        """Test RSS validation with feed that has no entries."""
        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = EMPTY_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValidationError, match="No entries found"):
                await validate_rss_feed("https://example.com/empty.xml")

    @pytest.mark.asyncio
    async def test_validate_rss_feed_invalid_xml(self):
        """Test RSS validation with invalid XML."""
        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = INVALID_XML
            mock_http.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValidationError, match="No entries found in feed:"):
                await validate_rss_feed("https://example.com/invalid.xml")

    @pytest.mark.asyncio
    async def test_validate_rss_feed_network_error(self):
        """Test RSS validation with network error."""
        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.side_effect = Exception("Connection failed")
            mock_http.return_value.__aenter__.return_value = mock_client

            with pytest.raises(ValidationError, match="Failed to validate RSS feed"):
                await validate_rss_feed("https://example.com/feed.xml")

    @pytest.mark.asyncio
    async def test_validate_rss_feed_minimal_content(self):
        """Test RSS validation with minimal valid feed."""
        minimal_rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Minimal Feed</title>
                <item>
                    <title>Test Item</title>
                    <link>https://example.com/item</link>
                </item>
            </channel>
        </rss>"""

        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = minimal_rss
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await validate_rss_feed("https://example.com/minimal.xml")

            assert result["title"] == "Minimal Feed"
            assert result["entries_count"] == 1
            assert result["description"] == ""  # Should handle missing description

    @pytest.mark.asyncio
    async def test_check_url_health_success(self):
        """Test successful URL health check."""
        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = "Some content"
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await check_url_health("https://example.com")

            assert result is True
            mock_client.fetch_text.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_check_url_health_failure(self):
        """Test URL health check with failure."""
        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.side_effect = Exception("Connection failed")
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await check_url_health("https://example.com")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_url_health_timeout(self):
        """Test URL health check uses correct timeout."""
        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http_class:
            mock_http = AsyncMock()
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = "Content"
            mock_http.__aenter__.return_value = mock_client
            mock_http_class.return_value = mock_http

            await check_url_health("https://example.com")

            # Verify HTTPClient was created with timeout=10
            mock_http_class.assert_called_once_with(timeout=10)

    @pytest.mark.asyncio
    async def test_validate_rss_feed_atom_format(self):
        """Test RSS validation with Atom feed."""
        atom_feed = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test Atom Feed</title>
            <subtitle>An Atom feed</subtitle>
            <link href="https://example.com"/>
            <id>https://example.com</id>

            <entry>
                <title>Atom Entry</title>
                <link href="https://example.com/entry"/>
                <id>https://example.com/entry</id>
                <summary>Entry summary</summary>
            </entry>
        </feed>"""

        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = atom_feed
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await validate_rss_feed("https://example.com/atom.xml")

            assert result["title"] == "Test Atom Feed"
            assert result["entries_count"] == 1
            assert result["version"] is not None  # Atom feeds have version info

    @pytest.mark.asyncio
    async def test_validate_rss_feed_with_metadata(self):
        """Test RSS validation preserves metadata correctly."""
        rss_with_metadata = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Metadata Feed</title>
                <description>Feed with metadata</description>
                <link>https://example.com</link>
                <language>fr-FR</language>
                <lastBuildDate>Wed, 22 Nov 2023 10:00:00 GMT</lastBuildDate>
                <item>
                    <title>Test</title>
                    <link>https://example.com/test</link>
                </item>
            </channel>
        </rss>"""

        with patch("app.processors.utils.url_validation.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = rss_with_metadata
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await validate_rss_feed("https://example.com/metadata.xml")

            assert result["language"] == "fr-FR"
            assert result["last_updated"] is not None  # Should parse lastBuildDate
