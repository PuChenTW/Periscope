"""
Tests for RSSFetcher implementation
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.processors.fetchers.base import FetchResult, SourceInfo
from app.processors.fetchers.rss import RSSFetcher
from tests.test_processors.fixtures import (
    EMPTY_RSS_FEED,
    INVALID_XML,
    MALFORMED_RSS_FEED,
    RSS_WITH_CONTENT_ENCODED,
    VALID_ATOM_FEED,
    VALID_RSS_FEED,
)


class TestRSSFetcher:
    """Test RSSFetcher functionality."""

    @pytest.fixture
    def rss_fetcher(self):
        """Create RSSFetcher instance for testing."""
        return RSSFetcher(timeout=10, max_articles=10)

    def test_source_type(self, rss_fetcher):
        """Test source type property."""
        assert rss_fetcher.source_type == "rss"

    @pytest.mark.asyncio
    async def test_validate_url_valid(self, rss_fetcher):
        """Test URL validation with valid RSS."""
        with patch("app.processors.fetchers.rss.validate_rss_feed") as mock_validate:
            mock_validate.return_value = {"title": "Test Feed"}

            result = await rss_fetcher.validate_url("https://example.com/feed.xml")

            assert result is True
            mock_validate.assert_called_once_with("https://example.com/feed.xml")

    @pytest.mark.asyncio
    async def test_validate_url_invalid(self, rss_fetcher):
        """Test URL validation with invalid RSS."""
        with patch("app.processors.fetchers.rss.validate_rss_feed") as mock_validate:
            mock_validate.side_effect = Exception("Invalid feed")

            result = await rss_fetcher.validate_url("https://example.com/invalid")

            assert result is False

    @pytest.mark.asyncio
    async def test_fetch_content_valid_rss(self, rss_fetcher):
        """Test fetching content from valid RSS feed."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await rss_fetcher.fetch_content("https://example.com/feed.xml")

            assert isinstance(result, FetchResult)
            assert result.success is True
            assert result.error_message is None
            assert len(result.articles) == 3
            assert result.source_info.title == "Test RSS Feed"
            assert result.source_info.description == "A test RSS feed for unit testing"

            # Check first article
            first_article = result.articles[0]
            assert first_article.title == "First Test Article"
            assert str(first_article.url) == "https://example.com/article-1"
            assert "first test article" in first_article.content.lower()
            assert first_article.author == "test@example.com (Test Author)"
            assert len(first_article.tags) == 2
            assert "Technology" in first_article.tags
            assert "Testing" in first_article.tags

    @pytest.mark.asyncio
    async def test_fetch_content_valid_atom(self, rss_fetcher):
        """Test fetching content from valid Atom feed."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_ATOM_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await rss_fetcher.fetch_content("https://example.com/atom.xml")

            assert result.success is True
            assert len(result.articles) == 2
            assert result.source_info.title == "Test Atom Feed"

            # Check Atom-specific parsing
            first_article = result.articles[0]
            assert first_article.title == "Atom Test Article"
            assert "Atom entry" in first_article.content

    @pytest.mark.asyncio
    async def test_fetch_content_with_content_encoded(self, rss_fetcher):
        """Test fetching RSS with content:encoded field."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = RSS_WITH_CONTENT_ENCODED
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await rss_fetcher.fetch_content("https://example.com/feed.xml")

            assert result.success is True
            assert len(result.articles) == 1

            article = result.articles[0]
            # Should prefer content:encoded over description
            assert "full article content" in article.content.lower()
            assert "html formatting" in article.content.lower()
            # HTML tags should be cleaned
            assert "<p>" not in article.content
            assert "<strong>" not in article.content

    @pytest.mark.asyncio
    async def test_fetch_content_malformed_rss(self, rss_fetcher):
        """Test fetching malformed RSS (should handle gracefully)."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = MALFORMED_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await rss_fetcher.fetch_content("https://example.com/malformed.xml")

            assert result.success is True
            # Should skip articles without required fields (link), but create default titles for missing titles
            assert len(result.articles) == 1  # One article has a link (gets "Untitled" title)

    @pytest.mark.asyncio
    async def test_fetch_content_empty_rss(self, rss_fetcher):
        """Test fetching empty RSS feed."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = EMPTY_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await rss_fetcher.fetch_content("https://example.com/empty.xml")

            assert result.success is False
            assert "No articles found" in result.error_message
            assert len(result.articles) == 0

    @pytest.mark.asyncio
    async def test_fetch_content_invalid_xml(self, rss_fetcher):
        """Test fetching invalid XML."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = INVALID_XML
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await rss_fetcher.fetch_content("https://example.com/invalid.xml")

            assert result.success is False
            assert result.error_message is not None
            assert len(result.articles) == 0

    @pytest.mark.asyncio
    async def test_fetch_content_invalid_url(self, rss_fetcher):
        """Test fetching with invalid URL format."""
        result = await rss_fetcher.fetch_content("not-a-url")

        assert result.success is False
        assert "Invalid URL format" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_content_network_error(self, rss_fetcher):
        """Test network error handling."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.side_effect = Exception("Network error")
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await rss_fetcher.fetch_content("https://example.com/feed.xml")

            assert result.success is False
            assert "Network error" in result.error_message

    @pytest.mark.asyncio
    async def test_get_source_info_success(self, rss_fetcher):
        """Test getting source info from RSS feed."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            source_info = await rss_fetcher.get_source_info("https://example.com/feed.xml")

            assert isinstance(source_info, SourceInfo)
            assert source_info.title == "Test RSS Feed"
            assert source_info.description == "A test RSS feed for unit testing"
            assert str(source_info.url) == "https://example.com/feed.xml"
            assert source_info.language == "en-US"

    @pytest.mark.asyncio
    async def test_get_source_info_error(self, rss_fetcher):
        """Test getting source info with error."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.side_effect = Exception("Connection failed")
            mock_http.return_value.__aenter__.return_value = mock_client

            source_info = await rss_fetcher.get_source_info("https://example.com/feed.xml")

            assert source_info.title == "Unknown Feed"
            assert "Unable to fetch" in source_info.description

    @pytest.mark.asyncio
    async def test_max_articles_limit(self, rss_fetcher):
        """Test that max_articles limit is respected."""
        # Create fetcher with low limit
        limited_fetcher = RSSFetcher(max_articles=2)

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await limited_fetcher.fetch_content("https://example.com/feed.xml")

            assert result.success is True
            assert len(result.articles) == 2  # Limited to 2 instead of 3

    def test_clean_text(self, rss_fetcher):
        """Test HTML cleaning functionality."""
        html_text = """<p>This is <strong>bold</strong> text with <a href="https://example.com">a link</a>.</p>
                       <br/>It has &nbsp; entities &amp; line breaks."""

        cleaned = rss_fetcher._clean_text(html_text)

        assert "<p>" not in cleaned
        assert "<strong>" not in cleaned
        assert "<a href" not in cleaned
        assert "<br/>" not in cleaned
        assert "&nbsp;" not in cleaned
        assert "&amp;" not in cleaned
        assert "bold" in cleaned
        assert "a link" in cleaned
        assert "entities & line breaks" in cleaned

    def test_clean_text_empty(self, rss_fetcher):
        """Test cleaning empty or None text."""
        assert rss_fetcher._clean_text("") == ""
        assert rss_fetcher._clean_text(None) == ""

    @pytest.mark.asyncio
    async def test_article_date_parsing(self, rss_fetcher):
        """Test various date formats are parsed correctly."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await rss_fetcher.fetch_content("https://example.com/feed.xml")

            assert result.success is True
            first_article = result.articles[0]
            assert isinstance(first_article.published_at, datetime)
            # Should parse "Wed, 22 Nov 2023 09:00:00 GMT"
            assert first_article.published_at.year == 2023
            assert first_article.published_at.month == 11
            assert first_article.published_at.day == 22
