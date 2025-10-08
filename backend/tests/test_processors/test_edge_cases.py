"""
Edge cases and error scenario tests for RSS Feed Fetching Layer
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.processors.fetchers.exceptions import FetchTimeoutError, RateLimitError
from app.processors.fetchers.factory import auto_create_fetcher
from app.processors.fetchers.rss import RSSFetcher


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_extremely_large_rss_feed(self):
        """Test handling of very large RSS feed."""
        # Create a feed with many items
        large_feed = (
            """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Large RSS Feed</title>
                <description>A very large RSS feed</description>
                <link>https://example.com</link>

                """
            + "".join(
                [
                    f"""<item>
                        <title>Article {i}</title>
                        <link>https://example.com/article-{i}</link>
                        <description>Content for article {i}</description>
                    </item>"""
                    for i in range(1000)  # 1000 articles
                ]
            )
            + """
            </channel>
        </rss>"""
        )

        fetcher = RSSFetcher(max_articles=50)  # Limit to 50

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = large_feed
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await fetcher.fetch_content("https://example.com/large-feed.xml")

            assert result.success is True
            # Should be limited to max_articles
            assert len(result.articles) == 50
            assert result.source_info.title == "Large RSS Feed"

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters in RSS content."""
        unicode_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Unicode Feed 🔥 Testing</title>
                <description>Feed with émojis and spéciał characters</description>
                <link>https://example.com</link>

                <item>
                    <title>Article with 中文 Chinese & русский Russian</title>
                    <link>https://example.com/unicode-article</link>
                    <description><![CDATA[
                        Content with various Unicode:
                        - Emojis: 😀 🎉 🚀
                        - Symbols: © ® ™ € £ ¥
                        - Languages: 日本語 العربية Ελληνικά
                        - Math: ∑ ∞ ≈ ±
                    ]]></description>
                    <author>Test Üser</author>
                </item>
            </channel>
        </rss>"""

        fetcher = RSSFetcher()

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = unicode_feed
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await fetcher.fetch_content("https://example.com/unicode-feed.xml")

            assert result.success is True
            assert len(result.articles) == 1

            # Check Unicode handling
            assert "🔥" in result.source_info.title
            assert "émojis" in result.source_info.description

            article = result.articles[0]
            assert "中文" in article.title
            assert "русский" in article.title
            assert "😀" in article.content
            assert "日本語" in article.content
            assert "Test Üser" in article.author

    @pytest.mark.asyncio
    async def test_malformed_dates(self):
        """Test handling of various malformed date formats."""
        malformed_dates_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Malformed Dates Feed</title>
                <link>https://example.com</link>

                <item>
                    <title>Invalid Date Format 1</title>
                    <link>https://example.com/article-1</link>
                    <pubDate>Not a date at all</pubDate>
                </item>

                <item>
                    <title>Invalid Date Format 2</title>
                    <link>https://example.com/article-2</link>
                    <pubDate>2023-13-45 25:99:99</pubDate>
                </item>

                <item>
                    <title>Empty Date</title>
                    <link>https://example.com/article-3</link>
                    <pubDate></pubDate>
                </item>

                <item>
                    <title>No Date</title>
                    <link>https://example.com/article-4</link>
                </item>
            </channel>
        </rss>"""

        fetcher = RSSFetcher()

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = malformed_dates_feed
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await fetcher.fetch_content("https://example.com/dates-feed.xml")

            assert result.success is True
            assert len(result.articles) == 4

            # All articles should have published_at fallback to fetch_timestamp due to malformed dates
            for article in result.articles:
                assert article.published_at is not None
                # Published_at should equal fetch_timestamp when parsing fails
                assert article.published_at == article.fetch_timestamp

    @pytest.mark.asyncio
    async def test_deeply_nested_html_content(self):
        """Test handling of deeply nested HTML content."""
        nested_html_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Nested HTML Feed</title>
                <link>https://example.com</link>

                <item>
                    <title>Article with Complex HTML</title>
                    <link>https://example.com/complex-html</link>
                    <description><![CDATA[
                        <div class="outer">
                            <div class="inner">
                                <p>Nested paragraph with <strong>bold <em>and italic</em></strong> text.</p>
                                <ul>
                                    <li>List item with <a href="https://example.com">nested <span>link</span></a></li>
                                    <li>Another <code>item <var>with</var> code</code></li>
                                </ul>
                                <blockquote>
                                    <p>Quote with <cite>citation <abbr>abbreviation</abbr></cite></p>
                                </blockquote>
                            </div>
                        </div>
                    ]]></description>
                </item>
            </channel>
        </rss>"""

        fetcher = RSSFetcher()

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = nested_html_feed
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await fetcher.fetch_content("https://example.com/nested-feed.xml")

            assert result.success is True
            article = result.articles[0]

            # HTML tags should be stripped
            assert "<div>" not in article.content
            assert "<p>" not in article.content
            assert "<strong>" not in article.content

            # Text content should remain
            assert "Nested paragraph" in article.content
            assert "bold and italic" in article.content
            assert "List item" in article.content

    @pytest.mark.asyncio
    async def test_network_timeout_scenarios(self):
        """Test various network timeout scenarios."""
        fetcher = RSSFetcher(timeout=1)  # Very short timeout

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.side_effect = FetchTimeoutError("Request timeout")
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await fetcher.fetch_content("https://example.com/timeout-feed.xml")

            assert result.success is False
            assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_rate_limiting_scenarios(self):
        """Test rate limiting error handling."""
        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.side_effect = RateLimitError("Rate limited")
            mock_http.return_value.__aenter__.return_value = mock_client

            fetcher = RSSFetcher()
            result = await fetcher.fetch_content("https://example.com/rate-limited.xml")

            assert result.success is False
            assert "rate limit" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_empty_or_whitespace_content(self):
        """Test handling of empty or whitespace-only content."""
        empty_content_scenarios = [
            "",  # Completely empty
            "   \n\t  ",  # Only whitespace
            "<?xml version='1.0'?>",  # XML declaration only
            "<?xml version='1.0'?>\n<!-- Just comments -->\n",  # Only comments
        ]

        fetcher = RSSFetcher()

        for content in empty_content_scenarios:
            with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
                mock_client = AsyncMock()
                mock_client.fetch_text.return_value = content
                mock_http.return_value.__aenter__.return_value = mock_client

                result = await fetcher.fetch_content("https://example.com/empty.xml")

                assert result.success is False
                assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_extremely_long_urls(self):
        """Test handling of extremely long URLs."""
        # Create very long URL (over 2000 characters)
        long_url = "https://example.com/" + "a" * 2000 + ".xml"

        fetcher = RSSFetcher()

        # Should not crash, should handle gracefully
        result = await fetcher.fetch_content(long_url)
        assert result.success is False  # Will fail validation or fetch

    @pytest.mark.asyncio
    async def test_url_with_special_characters(self):
        """Test URLs with special characters and encodings."""
        special_urls = [
            "https://example.com/feed with spaces.xml",
            "https://example.com/féed.xml",
            "https://example.com/feed?param=value&other=test",
            "https://example.com/feed#fragment",
            "https://example.com:8080/path/to/feed.xml",
        ]

        for url in special_urls:
            fetcher = await auto_create_fetcher(url)
            # Should not crash during creation
            assert fetcher is not None
            assert fetcher.source_type == "rss"

    @pytest.mark.asyncio
    async def test_mixed_encoding_scenarios(self):
        """Test handling of different character encodings."""
        # Test with different encoding declarations
        encoding_scenarios = [
            ("utf-8", '<?xml version="1.0" encoding="UTF-8"?>'),
            ("iso-8859-1", '<?xml version="1.0" encoding="ISO-8859-1"?>'),
            ("windows-1252", '<?xml version="1.0" encoding="windows-1252"?>'),
            (None, '<?xml version="1.0"?>'),  # No encoding specified
        ]

        for encoding, xml_declaration in encoding_scenarios:
            feed_content = f"""{xml_declaration}
            <rss version="2.0">
                <channel>
                    <title>Encoding Test</title>
                    <link>https://example.com</link>
                    <item>
                        <title>Test Article</title>
                        <link>https://example.com/test</link>
                        <description>Test content</description>
                    </item>
                </channel>
            </rss>"""

            fetcher = RSSFetcher()

            with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
                mock_client = AsyncMock()
                mock_client.fetch_text.return_value = feed_content
                mock_http.return_value.__aenter__.return_value = mock_client

                result = await fetcher.fetch_content(f"https://example.com/{encoding or 'default'}.xml")

                # Should handle gracefully regardless of encoding
                assert result.success is True or result.error_message is not None

    @pytest.mark.asyncio
    async def test_concurrent_session_handling(self):
        """Test that concurrent requests don't interfere with each other."""
        fetcher = RSSFetcher()

        # Simulate multiple concurrent calls (though actually sequential in test)
        urls = [f"https://example{i}.com/feed.xml" for i in range(5)]

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            call_count = 0

            def track_calls(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                mock_client = AsyncMock()
                mock_client.fetch_text.return_value = f"""<?xml version="1.0"?>
                <rss version="2.0">
                    <channel>
                        <title>Feed {call_count}</title>
                        <item>
                            <title>Article {call_count}</title>
                            <link>https://example.com/article-{call_count}</link>
                        </item>
                    </channel>
                </rss>"""
                return mock_client

            mock_http.return_value.__aenter__.side_effect = track_calls

            results = [await fetcher.fetch_content(url) for url in urls]

            # Each should get its own unique content
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result.success is True
                assert f"Feed {i + 1}" in result.source_info.title

    @pytest.mark.asyncio
    async def test_memory_efficiency_with_large_content(self):
        """Test memory efficiency with large article content."""
        # Create feed with very large article content
        large_content = "A" * 100000  # 100KB of content per article

        large_feed = f"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Large Content Feed</title>
                <item>
                    <title>Large Article</title>
                    <link>https://example.com/large</link>
                    <description><![CDATA[{large_content}]]></description>
                </item>
            </channel>
        </rss>"""

        fetcher = RSSFetcher()

        with patch("app.processors.fetchers.rss.HTTPClient") as mock_http:
            mock_client = AsyncMock()
            mock_client.fetch_text.return_value = large_feed
            mock_http.return_value.__aenter__.return_value = mock_client

            result = await fetcher.fetch_content("https://example.com/large-content.xml")

            # Should handle large content without issues
            assert result.success is True
            assert len(result.articles) == 1
            assert len(result.articles[0].content) > 50000  # Should preserve large content
