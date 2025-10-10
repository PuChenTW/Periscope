"""
Tests for ContentNormalizer implementation
"""

from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.config import ContentNormalizationSettings
from app.processors.fetchers.base import Article
from app.processors.normalizer import ContentNormalizer, SpamDetectionResult


class TestContentNormalizer:
    """Test ContentNormalizer functionality."""

    @pytest.fixture
    def mock_ai_provider(self):
        """Create a mock AI provider for testing with pre-configured TestModel based on output_type."""
        mock_provider = MagicMock()

        def create_agent_mock(output_type, system_prompt):
            # Return appropriate TestModel based on output_type for realistic default behavior
            if output_type == SpamDetectionResult:
                test_model = TestModel(
                    custom_output_args=SpamDetectionResult(is_spam=False, confidence=0.9, reasoning="Valid article")
                )
            else:
                # Default for unknown types
                test_model = TestModel()

            return Agent(test_model, output_type=output_type, system_prompt=system_prompt)

        mock_provider.create_agent = create_agent_mock
        return mock_provider

    @pytest.fixture
    def normalizer(self, mock_ai_provider):
        """Create ContentNormalizer instance for testing with default settings."""
        return ContentNormalizer(ai_provider=mock_ai_provider, settings=ContentNormalizationSettings(min_length=50))

    @pytest.fixture
    def normalizer_no_spam(self, mock_ai_provider):
        """Create ContentNormalizer with spam detection disabled."""
        return ContentNormalizer(
            ai_provider=mock_ai_provider,
            settings=ContentNormalizationSettings(min_length=50, spam_detection_enabled=False),
        )

    @pytest.fixture
    def valid_article(self):
        """Create a valid article for testing."""
        return Article(
            title="OpenAI Launches GPT-5 with Revolutionary Features",
            url=HttpUrl("https://example.com/article1"),
            content=(
                "OpenAI has announced the release of GPT-5, their latest language model with groundbreaking "
                "capabilities. The new model features improved reasoning, better context handling, and multimodal "
                "understanding. Industry experts are calling it a significant leap forward in artificial "
                "intelligence technology. This represents a major milestone in AI development."
            ),
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
            author="John Doe",
            tags=["AI", "OpenAI", "GPT"],
        )

    @pytest.mark.asyncio
    async def test_normalize_valid_article(self, normalizer, valid_article):
        """Test normalization of a complete, valid article."""
        result = await normalizer.normalize(valid_article)

        assert result is not None
        assert result.title == valid_article.title
        assert result.content == valid_article.content

    @pytest.mark.asyncio
    async def test_normalize_empty_content(self, normalizer):
        """Test rejection of article with empty content."""
        article = Article(
            title="Empty Content Article",
            url=HttpUrl("https://example.com/empty"),
            content="",
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)
        assert result is None

    @pytest.mark.asyncio
    async def test_normalize_whitespace_only_content(self, normalizer):
        """Test rejection of article with only whitespace content."""
        article = Article(
            title="Whitespace Article",
            url=HttpUrl("https://example.com/whitespace"),
            content="   \n\t  \n   ",
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)
        assert result is None

    @pytest.mark.asyncio
    async def test_normalize_content_too_short(self, normalizer):
        """Test rejection of article with content below minimum length."""
        article = Article(
            title="Short Article",
            url=HttpUrl("https://example.com/short"),
            content="Short.",  # Only 6 characters, below 50 char minimum
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)
        assert result is None

    @pytest.mark.asyncio
    async def test_normalize_content_exactly_minimum_length(self, normalizer):
        """Test article with exactly minimum content length is accepted."""
        # Create content that is exactly 50 characters (realistic text to avoid spam detection)
        content = "The quick brown fox jumps over the lazy doggggggg."

        article = Article(
            title="Minimum Length Article",
            url=HttpUrl("https://example.com/min"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.content.strip()) == 50

    @pytest.mark.asyncio
    async def test_normalize_with_unicode_content(self, normalizer):
        """Test handling of unicode characters in content."""
        content = (
            "这是一篇关于人工智能的文章。AI技术正在快速发展，影响着我们的日常生活。"  # noqa: RUF001
            "机器学习和深度学习是当前最热门的研究方向。专家预测，未来十年AI将带来重大变革。"  # noqa: RUF001
            "This article discusses artificial intelligence and its impact on society."
        )

        article = Article(
            title="AI Article with Unicode",
            url=HttpUrl("https://example.com/unicode"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None

    @pytest.mark.asyncio
    async def test_normalize_with_emojis(self, normalizer):
        """Test handling of emoji characters in content."""
        content = (
            "Technology companies are innovating rapidly 🚀. The new AI models show impressive capabilities 🤖. "
            "Researchers are excited about the potential applications 💡. This could transform many industries ⚡. "
            "The future looks bright for artificial intelligence and machine learning technologies worldwide."
        )

        article = Article(
            title="Tech Article with Emojis",
            url=HttpUrl("https://example.com/emoji"),
            content=content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None

    @pytest.mark.asyncio
    async def test_spam_detection_enabled(self, normalizer):
        """Test spam detection for excessive uppercase content."""
        # Create content with >70% uppercase letters
        spam_content = "BUY NOW!!! THIS IS AN AMAZING DEAL!!! " * 10

        article = Article(
            title="Spam Article",
            url=HttpUrl("https://example.com/spam"),
            content=spam_content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        # Mock AI to return spam
        test_model = TestModel(
            custom_output_args=SpamDetectionResult(
                is_spam=True, confidence=0.98, reasoning="Excessive uppercase and promotional language"
            )
        )

        with normalizer.spam_agent.override(model=test_model):
            result = await normalizer.normalize(article)

        assert result is None

    @pytest.mark.asyncio
    async def test_spam_detection_disabled(self, normalizer_no_spam):
        """Test that spam detection can be disabled via settings."""
        # Create obvious spam content
        spam_content = "BUY NOW!!! CLICK HERE!!! " * 20

        article = Article(
            title="Spam Article",
            url=HttpUrl("https://example.com/spam"),
            content=spam_content,
            published_at=datetime(2024, 1, 15, 10, 0),
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer_no_spam.normalize(article)
        # Should NOT be rejected since spam detection is disabled
        assert result is not None

    @pytest.mark.asyncio
    async def test_normalize_article_with_minimal_metadata(self, normalizer):
        """Test normalization of article with only required fields."""
        fetch_timestamp = datetime.now(UTC)
        article = Article(
            title="Minimal Article",
            url=HttpUrl("https://example.com/minimal"),
            content=(
                "This is a minimal article with just enough content to pass validation. "
                "It has realistic text to avoid spam detection patterns during testing."
            ),
            fetch_timestamp=fetch_timestamp,
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.title == "Minimal Article"
        assert result.author is None
        # After normalization, published_at should never be None - it falls back to fetch_timestamp
        assert result.published_at == fetch_timestamp
        assert result.tags == []

    @pytest.mark.asyncio
    async def test_normalize_preserves_article_fields(self, normalizer, valid_article):
        """Test that normalization preserves all article fields."""
        result = await normalizer.normalize(valid_article)

        assert result is not None
        assert result.title == valid_article.title
        assert result.url == valid_article.url
        assert result.content == valid_article.content
        assert result.author == valid_article.author
        assert result.published_at == valid_article.published_at
        assert result.tags == valid_article.tags
        assert result.summary == valid_article.summary
        assert result.ai_topics == valid_article.ai_topics
        # metadata will have quality_score added, so only check it contains original keys
        for key in valid_article.metadata:
            assert key in result.metadata

    # ========== Metadata Normalization Tests ==========

    @pytest.mark.asyncio
    async def test_normalize_title_whitespace_cleanup(self, normalizer):
        """Test title whitespace normalization."""
        article = Article(
            title="  Multiple   spaces   and\n  newlines  ",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.title == "Multiple spaces and newlines"

    @pytest.mark.asyncio
    async def test_normalize_title_truncation(self, mock_ai_provider):
        """Test title truncation at word boundary."""
        # Need custom title_max_length, so create a specific normalizer
        normalizer = ContentNormalizer(
            settings=ContentNormalizationSettings(title_max_length=50, min_length=50),
            ai_provider=mock_ai_provider,
        )

        long_title = "This is a very long title that definitely exceeds fifty characters and should be truncated"

        article = Article(
            title=long_title,
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.title) <= 53  # 50 + "..."
        assert result.title.endswith("...")
        assert " " not in result.title[47:]  # No partial words before ...

    @pytest.mark.asyncio
    async def test_normalize_title_empty_fallback(self, normalizer):
        """Test empty title fallback to 'Untitled Article'."""

        article = Article(
            title="   ",  # Whitespace-only
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.title == "Untitled Article"

    @pytest.mark.asyncio
    async def test_normalize_author_title_case(self, normalizer):
        """Test author name title case normalization."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            author="  john   doe  ",
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.author == "John Doe"

    @pytest.mark.asyncio
    async def test_normalize_author_truncation(self, mock_ai_provider):
        """Test author name truncation."""
        # Need custom author_max_length, so create a specific normalizer
        normalizer = ContentNormalizer(
            ai_provider=mock_ai_provider, settings=ContentNormalizationSettings(author_max_length=30, min_length=50)
        )

        long_author = "Dr. Johnathan Christopher Alexander Davidson III"

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            author=long_author,
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.author) <= 33  # 30 + "..."
        assert result.author.endswith("...")

    @pytest.mark.asyncio
    async def test_normalize_tags_deduplication(self, normalizer):
        """Test tag deduplication and normalization."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            tags=["AI", "Machine Learning", "ai", "ML", "machine learning", "AI"],
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.tags) == 3
        assert "ai" in result.tags
        assert "machine learning" in result.tags
        assert "ml" in result.tags
        # No duplicates
        assert result.tags.count("ai") == 1

    @pytest.mark.asyncio
    async def test_normalize_tags_max_limit(self, mock_ai_provider):
        """Test max tags per article limit."""
        # Need custom max_tags_per_article, so create a specific normalizer
        normalizer = ContentNormalizer(
            ai_provider=mock_ai_provider,
            settings=ContentNormalizationSettings(min_length=50, max_tags_per_article=5),
        )

        tags = [f"tag{i}" for i in range(25)]  # 25 tags

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            tags=tags,
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.tags) == 5  # Limited to 5

    @pytest.mark.asyncio
    async def test_normalize_tags_length_limit(self, mock_ai_provider):
        """Test individual tag length limit."""
        # Need custom tag_max_length, so create a specific normalizer
        normalizer = ContentNormalizer(
            ai_provider=mock_ai_provider, settings=ContentNormalizationSettings(tag_max_length=20, min_length=50)
        )

        long_tag = "this-is-a-very-long-tag-that-exceeds-limit"

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            tags=[long_tag, "short"],
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.tags[0]) == 20  # Truncated
        assert result.tags[1] == "short"

    @pytest.mark.asyncio
    async def test_normalize_url_remove_tracking_params(self, normalizer):
        """Test URL tracking parameter removal."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/article?utm_source=rss&utm_campaign=feed&ref=twitter&id=123"),
            content="Valid content with enough length to pass validation checks.",
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        url_str = str(result.url)
        assert "utm_source" not in url_str
        assert "utm_campaign" not in url_str
        assert "ref" not in url_str
        assert "id=123" in url_str  # Non-tracking param preserved

    @pytest.mark.asyncio
    async def test_normalize_url_upgrade_to_https(self, normalizer):
        """Test URL upgrade from http to https."""

        article = Article(
            title="Test Article",
            url=HttpUrl("http://example.com/article"),
            content="Valid content with enough length to pass validation checks.",
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert str(result.url).startswith("https://")

    @pytest.mark.asyncio
    async def test_enforce_content_length_truncation(self, mock_ai_provider):
        """Test content truncation at word boundary."""
        # Need custom content_max_length, so create a specific normalizer
        normalizer = ContentNormalizer(
            ai_provider=mock_ai_provider, settings=ContentNormalizationSettings(max_length=200)
        )

        long_content = "This is a test article with very long content. " * 20  # Much longer than 200 chars

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content=long_content,
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.content) <= 200
        # Should end at word boundary
        assert not result.content.endswith(" ")

    # ========== Date Normalization Tests ==========

    @pytest.mark.asyncio
    async def test_normalize_date_missing_published_at(self, normalizer):
        """Test that missing published_at falls back to fetch_timestamp."""
        fetch_timestamp = datetime.now(UTC)
        article = Article(
            title="Article Without Date",
            url=HttpUrl("https://example.com/no-date"),
            content="Valid content with enough length to pass validation checks for testing.",
            published_at=None,  # No published date
            fetch_timestamp=fetch_timestamp,
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.published_at == fetch_timestamp
        assert result.published_at.tzinfo == UTC

    @pytest.mark.asyncio
    async def test_normalize_date_naive_datetime(self, normalizer):
        """Test that naive datetime is converted to UTC-aware."""
        naive_date = datetime(2024, 1, 15, 10, 30, 0)  # Naive (no timezone)

        article = Article(
            title="Article With Naive Date",
            url=HttpUrl("https://example.com/naive-date"),
            content="Valid content with enough length to pass validation checks for testing.",
            published_at=naive_date,
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.published_at is not None
        assert result.published_at.tzinfo == UTC
        # Should preserve the date/time values, just add UTC timezone
        assert result.published_at.year == 2024
        assert result.published_at.month == 1
        assert result.published_at.day == 15
        assert result.published_at.hour == 10
        assert result.published_at.minute == 30

    @pytest.mark.asyncio
    async def test_normalize_date_non_utc_timezone(self, normalizer):
        """Test that non-UTC aware datetime is converted to UTC."""
        # Create a datetime in Eastern Time (UTC-5)
        eastern_date = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone(timedelta(hours=-5)))

        article = Article(
            title="Article With Eastern Time",
            url=HttpUrl("https://example.com/eastern-date"),
            content="Valid content with enough length to pass validation checks for testing.",
            published_at=eastern_date,
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.published_at is not None
        assert result.published_at.tzinfo == UTC
        # Time should be converted: 10:30 EST = 15:30 UTC
        assert result.published_at.hour == 15
        assert result.published_at.minute == 30

    @pytest.mark.asyncio
    async def test_normalize_date_already_utc(self, normalizer):
        """Test that UTC-aware datetime is preserved unchanged."""
        utc_date = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        article = Article(
            title="Article With UTC Date",
            url=HttpUrl("https://example.com/utc-date"),
            content="Valid content with enough length to pass validation checks for testing.",
            published_at=utc_date,
            fetch_timestamp=datetime.now(UTC),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.published_at == utc_date
        assert result.published_at.tzinfo == UTC

    @pytest.mark.asyncio
    async def test_normalize_date_never_none(self, normalizer):
        """Test that published_at is never None after normalization."""
        # Test with various date scenarios
        test_articles = [
            Article(
                title="No Date",
                url=HttpUrl("https://example.com/1"),
                content="Valid content with enough length to pass validation checks for testing.",
                published_at=None,
                fetch_timestamp=datetime.now(UTC),
            ),
            Article(
                title="Naive Date",
                url=HttpUrl("https://example.com/2"),
                content="Valid content with enough length to pass validation checks for testing.",
                published_at=datetime(2024, 1, 15, 10, 0),
                fetch_timestamp=datetime.now(UTC),
            ),
            Article(
                title="UTC Date",
                url=HttpUrl("https://example.com/3"),
                content="Valid content with enough length to pass validation checks for testing.",
                published_at=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
                fetch_timestamp=datetime.now(UTC),
            ),
        ]

        for article in test_articles:
            result = await normalizer.normalize(article)
            assert result is not None
            assert result.published_at is not None, f"published_at is None for article: {article.title}"
            assert result.published_at.tzinfo == UTC, f"published_at not UTC for: {article.title}"
