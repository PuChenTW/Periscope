"""
Tests for ContentNormalizer implementation
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from app.processors.fetchers.base import Article
from app.processors.normalizer import ContentNormalizer, ContentQualityResult, SpamDetectionResult


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
            elif output_type == ContentQualityResult:
                test_model = TestModel(
                    custom_output_args=ContentQualityResult(
                        writing_quality=15, informativeness=16, credibility=8, reasoning="Good quality article"
                    )
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
        return ContentNormalizer(ai_provider=mock_ai_provider, content_min_length=50)

    @pytest.fixture
    def normalizer_no_quality(self, mock_ai_provider):
        """Create ContentNormalizer with quality scoring disabled."""
        return ContentNormalizer(ai_provider=mock_ai_provider, content_min_length=50, quality_scoring_enabled=False)

    @pytest.fixture
    def normalizer_no_spam(self, mock_ai_provider):
        """Create ContentNormalizer with spam detection disabled."""
        return ContentNormalizer(ai_provider=mock_ai_provider, content_min_length=50, spam_detection_enabled=False)

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
        )

        result = await normalizer_no_spam.normalize(article)
        # Should NOT be rejected since spam detection is disabled
        assert result is not None

    @pytest.mark.asyncio
    async def test_normalize_article_with_minimal_metadata(self, normalizer):
        """Test normalization of article with only required fields."""
        article = Article(
            title="Minimal Article",
            url=HttpUrl("https://example.com/minimal"),
            content=(
                "This is a minimal article with just enough content to pass validation. "
                "It has realistic text to avoid spam detection patterns during testing."
            ),
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert result.title == "Minimal Article"
        assert result.author is None
        assert result.published_at is None
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
    async def test_normalize_title_whitespace_cleanup(self, normalizer_no_quality):
        """Test title whitespace normalization."""
        article = Article(
            title="  Multiple   spaces   and\n  newlines  ",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
        )

        result = await normalizer_no_quality.normalize(article)

        assert result is not None
        assert result.title == "Multiple spaces and newlines"

    @pytest.mark.asyncio
    async def test_normalize_title_truncation(self, mock_ai_provider):
        """Test title truncation at word boundary."""
        # Need custom title_max_length, so create a specific normalizer
        normalizer = ContentNormalizer(
            title_max_length=50, ai_provider=mock_ai_provider, quality_scoring_enabled=False, content_min_length=50
        )

        long_title = "This is a very long title that definitely exceeds fifty characters and should be truncated"

        article = Article(
            title=long_title,
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.title) <= 53  # 50 + "..."
        assert result.title.endswith("...")
        assert " " not in result.title[47:]  # No partial words before ...

    @pytest.mark.asyncio
    async def test_normalize_title_empty_fallback(self, normalizer_no_quality):
        """Test empty title fallback to 'Untitled Article'."""

        article = Article(
            title="   ",  # Whitespace-only
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
        )

        result = await normalizer_no_quality.normalize(article)

        assert result is not None
        assert result.title == "Untitled Article"

    @pytest.mark.asyncio
    async def test_normalize_author_title_case(self, normalizer_no_quality):
        """Test author name title case normalization."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            author="  john   doe  ",
        )

        result = await normalizer_no_quality.normalize(article)

        assert result is not None
        assert result.author == "John Doe"

    @pytest.mark.asyncio
    async def test_normalize_author_truncation(self, mock_ai_provider):
        """Test author name truncation."""
        # Need custom author_max_length, so create a specific normalizer
        normalizer = ContentNormalizer(
            author_max_length=30, ai_provider=mock_ai_provider, quality_scoring_enabled=False, content_min_length=50
        )

        long_author = "Dr. Johnathan Christopher Alexander Davidson III"

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            author=long_author,
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.author) <= 33  # 30 + "..."
        assert result.author.endswith("...")

    @pytest.mark.asyncio
    async def test_normalize_tags_deduplication(self, normalizer_no_quality):
        """Test tag deduplication and normalization."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            tags=["AI", "Machine Learning", "ai", "ML", "machine learning", "AI"],
        )

        result = await normalizer_no_quality.normalize(article)

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
            max_tags_per_article=5, ai_provider=mock_ai_provider, quality_scoring_enabled=False, content_min_length=50
        )

        tags = [f"tag{i}" for i in range(25)]  # 25 tags

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            tags=tags,
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.tags) == 5  # Limited to 5

    @pytest.mark.asyncio
    async def test_normalize_tags_length_limit(self, mock_ai_provider):
        """Test individual tag length limit."""
        # Need custom tag_max_length, so create a specific normalizer
        normalizer = ContentNormalizer(
            tag_max_length=20, ai_provider=mock_ai_provider, quality_scoring_enabled=False, content_min_length=50
        )

        long_tag = "this-is-a-very-long-tag-that-exceeds-limit"

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            tags=[long_tag, "short"],
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.tags[0]) == 20  # Truncated
        assert result.tags[1] == "short"

    @pytest.mark.asyncio
    async def test_normalize_url_remove_tracking_params(self, normalizer_no_quality):
        """Test URL tracking parameter removal."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/article?utm_source=rss&utm_campaign=feed&ref=twitter&id=123"),
            content="Valid content with enough length to pass validation checks.",
        )

        result = await normalizer_no_quality.normalize(article)

        assert result is not None
        url_str = str(result.url)
        assert "utm_source" not in url_str
        assert "utm_campaign" not in url_str
        assert "ref" not in url_str
        assert "id=123" in url_str  # Non-tracking param preserved

    @pytest.mark.asyncio
    async def test_normalize_url_upgrade_to_https(self, normalizer_no_quality):
        """Test URL upgrade from http to https."""

        article = Article(
            title="Test Article",
            url=HttpUrl("http://example.com/article"),
            content="Valid content with enough length to pass validation checks.",
        )

        result = await normalizer_no_quality.normalize(article)

        assert result is not None
        assert str(result.url).startswith("https://")

    @pytest.mark.asyncio
    async def test_enforce_content_length_truncation(self, mock_ai_provider):
        """Test content truncation at word boundary."""
        # Need custom content_max_length, so create a specific normalizer
        normalizer = ContentNormalizer(
            content_max_length=200, ai_provider=mock_ai_provider, quality_scoring_enabled=False
        )

        long_content = "This is a test article with very long content. " * 20  # Much longer than 200 chars

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content=long_content,
        )

        result = await normalizer.normalize(article)

        assert result is not None
        assert len(result.content) <= 200
        # Should end at word boundary
        assert not result.content.endswith(" ")

    # ========== Quality Scoring Tests ==========

    @pytest.mark.asyncio
    async def test_metadata_score_calculation(self, normalizer_no_quality):
        """Test rule-based metadata score calculation."""

        # Complete article: author, published_at, tags, >1000 chars content
        complete_article = Article(
            title="Complete Article",
            url=HttpUrl("https://example.com/test"),
            content="A" * 1200,  # >1000 chars
            author="John Doe",
            published_at=datetime(2024, 1, 15, 10, 0),
            tags=["ai", "tech"],
        )

        result = await normalizer_no_quality.normalize(complete_article)

        assert result is not None
        # When AI scoring disabled, metadata score is scaled to 0-100
        # Expected: 10 (author) + 10 (date) + 5 (tags) + 15 (>500 chars) + 10 (>1000 chars) = 50
        # Scaled: 50 * 2 = 100
        assert result.metadata["quality_score"] == 100

    @pytest.mark.asyncio
    async def test_metadata_score_minimal_article(self, normalizer_no_quality):
        """Test metadata score for minimal article."""

        # Minimal article: no author, no date, no tags, short content
        minimal_article = Article(
            title="Minimal Article",
            url=HttpUrl("https://example.com/test"),
            content="A" * 300,  # >100 but <500 chars
        )

        result = await normalizer_no_quality.normalize(minimal_article)

        assert result is not None
        # Expected: 0 (no metadata), scaled to 0-100 = 0
        assert result.metadata["quality_score"] == 0

    @pytest.mark.asyncio
    async def test_hybrid_quality_scoring_enabled(self, normalizer):
        """Test hybrid quality scoring with AI enabled."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="Valid content with enough length to pass validation checks.",
            author="John Doe",
            published_at=datetime(2024, 1, 15, 10, 0),
            tags=["ai"],
        )

        result = await normalizer.normalize(article)

        assert result is not None
        # Metadata score: 10 (author) + 10 (date) + 5 (tags) + 0 (content <500) = 25
        # AI score from default mock: 15 + 16 + 8 = 39
        # Total: 25 + 39 = 64
        assert result.metadata["quality_score"] == 64
        assert result.metadata["quality_breakdown"]["metadata_score"] == 25
        assert result.metadata["quality_breakdown"]["ai_content_score"] == 39

    @pytest.mark.asyncio
    async def test_quality_scoring_disabled(self, normalizer_no_quality):
        """Test that AI quality scoring can be disabled."""

        article = Article(
            title="Test Article",
            url=HttpUrl("https://example.com/test"),
            content="A" * 600,  # >500 chars
            author="John Doe",
        )

        result = await normalizer_no_quality.normalize(article)

        assert result is not None
        # When disabled, metadata score scaled to 0-100
        # Expected: (10 + 15) * 2 = 50
        assert "quality_score" in result.metadata
        assert result.metadata["quality_score"] == 50
        assert result.metadata["quality_breakdown"]["ai_content_score"] == 0
