"""
Integration tests for RSS Feed Fetching Layer
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.processors.fetchers.factory import auto_create_fetcher
from app.processors.fetchers.rss import RSSFetcher
from app.processors.utils.url_validation import check_url_health, validate_rss_feed
from tests.test_processors.fixtures import VALID_ATOM_FEED, VALID_RSS_FEED


class TestRSSFetchingIntegration:
    """Integration tests for complete RSS fetching workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_rss_fetching(self):
        """Test complete RSS fetching workflow from URL to articles."""
        url = "https://example.com/feed.xml"

        with (
            patch("app.processors.utils.url_validation.HTTPClient") as mock_validator,
            patch("app.processors.fetchers.rss.HTTPClient") as mock_fetcher_http,
        ):
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_RSS_FEED
            mock_validator.return_value.__aenter__.return_value = mock_client
            mock_fetcher_http.return_value.__aenter__.return_value = mock_client

            # Step 1: Validate the URL
            is_healthy = await check_url_health(url)
            assert is_healthy is True

            # Step 2: Validate RSS feed
            feed_info = await validate_rss_feed(url)
            assert feed_info["title"] == "Test RSS Feed"
            assert feed_info["entries_count"] == 3

            # Step 3: Create fetcher automatically
            fetcher = await auto_create_fetcher(url)
            assert isinstance(fetcher, RSSFetcher)
            assert fetcher.source_type == "rss"

            # Step 4: Validate URL with fetcher
            is_valid = await fetcher.validate_url(url)
            assert is_valid is True

            # Step 5: Get source information
            source_info = await fetcher.get_source_info(url)
            assert source_info.title == "Test RSS Feed"
            assert source_info.description == "A test RSS feed for unit testing"

            # Step 6: Fetch full content
            result = await fetcher.fetch_content(url)
            assert result.success is True
            assert len(result.articles) == 3
            assert result.source_info.title == "Test RSS Feed"

            # Verify article content
            first_article = result.articles[0]
            assert first_article.title == "First Test Article"
            assert str(first_article.url) == "https://example.com/article-1"
            assert first_article.author is not None
            assert len(first_article.tags) > 0

    @pytest.mark.asyncio
    async def test_end_to_end_atom_fetching(self):
        """Test complete Atom feed fetching workflow."""
        url = "https://example.com/atom.xml"

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_ATOM_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            # Complete workflow
            fetcher = await auto_create_fetcher(url, max_articles=5)
            result = await fetcher.fetch_content(url)

            assert result.success is True
            assert len(result.articles) == 2
            assert result.source_info.title == "Test Atom Feed"

            # Verify Atom-specific content
            first_article = result.articles[0]
            assert first_article.title == "Atom Test Article"
            assert "Atom entry" in first_article.content

    @pytest.mark.asyncio
    async def test_multiple_feeds_processing(self):
        """Test processing multiple RSS feeds in sequence."""
        feeds = [
            ("https://example.com/rss1.xml", VALID_RSS_FEED),
            ("https://example.com/atom1.xml", VALID_ATOM_FEED),
            ("https://example.com/rss2.xml", VALID_RSS_FEED),
        ]

        results = []

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:

            def mock_fetch_text(url):
                for feed_url, content in feeds:
                    if url == feed_url:
                        return content
                return VALID_RSS_FEED  # Default

            mock_client = AsyncMock()
            mock_client.fetch_text.side_effect = mock_fetch_text
            mock_http.return_value.__aenter__.return_value = mock_client

            # Process each feed
            for url, _ in feeds:
                fetcher = await auto_create_fetcher(url, max_articles=10)
                result = await fetcher.fetch_content(url)
                results.append((url, result))

            # Verify all feeds were processed successfully
            assert len(results) == 3
            for url, result in results:
                assert result.success is True, f"Failed for {url}"
                assert len(result.articles) > 0, f"No articles for {url}"

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error handling and recovery in the workflow."""
        urls = [
            "https://example.com/good-feed.xml",
            "https://example.com/bad-feed.xml",
            "https://example.com/timeout-feed.xml",
        ]

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:

            def mock_fetch_text(url):
                if "good-feed" in url:
                    return VALID_RSS_FEED
                elif "bad-feed" in url:
                    raise Exception("Invalid feed")
                elif "timeout-feed" in url:
                    raise TimeoutError("Request timeout")
                return ""

            mock_client = AsyncMock()
            mock_client.fetch_text.side_effect = mock_fetch_text
            mock_http.return_value.__aenter__.return_value = mock_client

            results = []
            for url in urls:
                try:
                    fetcher = await auto_create_fetcher(url)
                    result = await fetcher.fetch_content(url)
                    results.append((url, result, None))
                except Exception as e:
                    results.append((url, None, str(e)))

            # Verify mixed results
            good_result = next(r for r in results if "good-feed" in r[0])
            bad_result = next(r for r in results if "bad-feed" in r[0])
            timeout_result = next(r for r in results if "timeout-feed" in r[0])

            # Good feed should succeed
            assert good_result[1] is not None
            assert good_result[1].success is True

            # Bad feeds should fail gracefully
            assert bad_result[1] is None or not bad_result[1].success
            assert timeout_result[1] is None or not timeout_result[1].success

    @pytest.mark.asyncio
    async def test_configuration_integration(self):
        """Test RSS fetcher with different configurations."""
        url = "https://example.com/feed.xml"

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            # Test with different configurations
            configs = [
                {"timeout": 10, "max_articles": 1},
                {"timeout": 30, "max_articles": 5},
                {"timeout": 60, "max_articles": 100},
            ]

            for config in configs:
                fetcher = await auto_create_fetcher(url, **config)

                # Verify configuration applied
                assert fetcher.timeout == config["timeout"]
                assert fetcher.max_articles == config["max_articles"]

                # Test functionality
                result = await fetcher.fetch_content(url)
                assert result.success is True

                # Verify max_articles limit
                expected_count = min(config["max_articles"], 3)  # 3 articles in fixture
                assert len(result.articles) == expected_count

    @pytest.mark.asyncio
    async def test_validation_integration(self):
        """Test integration between URL validation and fetching."""
        test_cases = [
            ("https://valid-rss.com/feed.xml", VALID_RSS_FEED, True),
            ("https://valid-atom.com/feed.xml", VALID_ATOM_FEED, True),
            ("not-a-valid-url", "", False),
        ]

        for url, content, should_succeed in test_cases:
            with (
                patch("app.processors.fetchers.rss.HTTPClient") as mock_http,
                patch("app.processors.utils.url_validation.HTTPClient") as mock_validator,
            ):
                mock_client = AsyncMock()
                if content:
                    mock_client.fetch_text.return_value = content
                else:
                    mock_client.fetch_text.side_effect = Exception("Invalid URL")
                mock_http.return_value.__aenter__.return_value = mock_client
                mock_validator.return_value.__aenter__.return_value = mock_client

                try:
                    # Test validation first
                    if should_succeed:
                        feed_info = await validate_rss_feed(url)
                        assert "title" in feed_info

                        # Then test fetching
                        fetcher = await auto_create_fetcher(url)
                        result = await fetcher.fetch_content(url)
                        assert result.success is True
                    else:
                        # Should raise exception for invalid URLs
                        with pytest.raises(Exception):
                            await validate_rss_feed(url)

                except Exception as e:
                    if should_succeed:
                        pytest.fail(f"Unexpected failure for {url}: {e}")
                    # Expected failure for invalid URLs

    @pytest.mark.asyncio
    async def test_concurrent_fetching_simulation(self):
        """Simulate concurrent RSS fetching (though still sequential in test)."""
        urls = [f"https://example{i}.com/feed.xml" for i in range(1, 6)]

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = VALID_RSS_FEED
            mock_http.return_value.__aenter__.return_value = mock_client

            # Simulate concurrent processing
            tasks = []
            for i, url in enumerate(urls):
                # Each "task" represents a separate user's feed
                fetcher = await auto_create_fetcher(url, max_articles=2 + i)
                result = await fetcher.fetch_content(url)
                tasks.append((url, result, fetcher.max_articles))

            # Verify all tasks completed successfully
            assert len(tasks) == 5
            for url, result, max_articles in tasks:
                assert result.success is True, f"Failed for {url}"
                expected_articles = min(max_articles, 3)  # 3 in fixture
                assert len(result.articles) == expected_articles
