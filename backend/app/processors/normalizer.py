"""
Content normalization service for standardizing article structure and metadata.

This module provides business-level validation and enrichment beyond what the RSS
fetcher provides, ensuring consistent data quality before AI processing.
"""

import textwrap
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from loguru import logger
from pydantic import BaseModel, Field

from app.config import get_settings
from app.processors.ai_provider import AIProvider, create_ai_provider
from app.processors.fetchers.base import Article


class SpamDetectionResult(BaseModel):
    """AI-powered spam detection result with reasoning."""

    is_spam: bool = Field(description="Whether the content is spam")
    confidence: float = Field(description="Confidence score (0.0-1.0)")
    reasoning: str = Field(description="Explanation of the spam determination")


class ContentNormalizer:
    """
    Normalizes article content and metadata for consistent processing.

    This class ensures articles meet quality standards and have standardized
    structure before AI processing. It never raises exceptions - uses fallbacks
    and logs warnings instead.
    """

    def __init__(
        self,
        content_min_length: int = 100,
        content_max_length: int = 50000,
        spam_detection_enabled: bool = True,
        title_max_length: int = 500,
        author_max_length: int = 100,
        tag_max_length: int = 50,
        max_tags_per_article: int = 20,
        ai_provider: AIProvider | None = None,
    ):
        """
        Initialize normalizer with configuration and AI provider.

        Args:
            content_min_length: Minimum content length in characters (default: 100)
            content_max_length: Maximum content length in characters (default: 50000)
            spam_detection_enabled: Enable AI-powered spam detection (default: True)
            title_max_length: Maximum title length in characters (default: 500)
            author_max_length: Maximum author name length (default: 100)
            tag_max_length: Maximum tag length (default: 50)
            max_tags_per_article: Maximum tags per article (default: 20)
            ai_provider: AI provider instance (creates default if not provided)
        """
        self.content_min_length = content_min_length
        self.content_max_length = content_max_length
        self.spam_detection_enabled = spam_detection_enabled
        self.title_max_length = title_max_length
        self.author_max_length = author_max_length
        self.tag_max_length = tag_max_length
        self.max_tags_per_article = max_tags_per_article

        # Create AI provider if not injected
        settings = get_settings()
        provider = ai_provider or create_ai_provider(settings)

        # Initialize PydanticAI agent for spam detection
        self.spam_agent = provider.create_agent(
            output_type=SpamDetectionResult,
            system_prompt=textwrap.dedent("""\
                You are an expert at detecting spam and low-quality content.
                Your task is to analyze article content and determine if it is spam.

                Spam indicators include:
                - Excessive promotional language or calls to action
                - Repeated characters, words, or phrases
                - Misleading clickbait with no substance
                - Excessive capitalization or punctuation
                - Obvious advertising or marketing content
                - Low-quality automated or bot-generated content
                - Scam or fraudulent content patterns

                Legitimate content that should NOT be marked as spam:
                - News articles with some promotional elements
                - Product announcements from legitimate companies
                - Educational or informational content
                - Opinion pieces or blog posts

                Provide a confidence score (0.0-1.0) and clear reasoning for your determination.
            """),
        )

    async def normalize(self, article: Article) -> Article | None:
        """
        Normalize an article's content and metadata.

        Args:
            article: Raw article from fetcher

        Returns:
            Normalized article, or None if article should be rejected
        """
        # Phase 1: Content validation - reject low-quality articles
        if not await self._validate_content(article):
            logger.debug(f"Article '{article.title[:50]}...' rejected during content validation")
            return None

        # Phase 2: Metadata standardization
        article = self._normalize_title(article)
        article = self._normalize_author(article)
        article = self._normalize_tags(article)
        article = self._normalize_url(article)
        article = self._enforce_content_length(article)

        return article

    async def _validate_content(self, article: Article) -> bool:
        """
        Validate whether an Article's textual content meets minimum quality standards before further processing.

        Quality checks performed (in order):
        1. Non-empty content: Rejects if content is None, empty, or only whitespace.
        2. Minimum length: Rejects if stripped content length is below the configured
            threshold (self.settings.content_min_length). This prevents extremely short,
            low-signal items such as placeholders or link stubs.
        3. AI-powered spam detection (optional): If spam detection is enabled
            (self.settings.spam_detection_enabled), uses AI to identify spam content
            patterns including promotional content, scams, and low-quality automated content.

        Args:
            article: Article to validate

        Returns:
            True if content is valid, False if should be rejected
        """
        # Check for empty or whitespace-only content
        if not article.content or not article.content.strip():
            logger.debug(f"Article '{article.title[:50]}...' has empty content")
            return False

        # Check minimum content length
        content_length = len(article.content.strip())
        if content_length < self.content_min_length:
            logger.debug(
                f"Article '{article.title[:50]}...' content too short "
                f"({content_length} chars, minimum {self.content_min_length})"
            )
            return False

        # Check for spam using AI if enabled
        if self.spam_detection_enabled and await self._detect_spam(article):
            logger.debug(f"Article '{article.title[:50]}...' detected as spam")
            return False

        return True

    async def _detect_spam(self, article: Article) -> bool:
        """
        Detect spam content using AI-powered analysis.

        Args:
            article: Article to check for spam

        Returns:
            True if spam detected, False otherwise
        """
        # Truncate content to avoid token limits (use first 1000 chars)
        content = article.content[:1000] if article.content else ""

        # Build prompt for AI spam detection
        prompt = textwrap.dedent(f"""\
            Article Title: {article.title}
            Content: {content}

            Analyze this article and determine if it is spam or low-quality content.
        """)

        try:
            # Run AI spam detection
            result = await self.spam_agent.run(prompt)
            detection_result = result.output

            logger.debug(
                f"Spam detection for '{article.title[:50]}...': "
                f"is_spam={detection_result.is_spam}, "
                f"confidence={detection_result.confidence:.2f}, "
                f"reasoning={detection_result.reasoning}"
            )

            return detection_result.is_spam

        except Exception as e:
            logger.error(f"Error during AI spam detection for article '{article.title[:50]}...': {e}")
            # On error, return False (not spam) to avoid false rejections
            return False

    def _normalize_title(self, article: Article) -> Article:
        """
        Normalize article title: cleanup whitespace, enforce max length, fallback.

        Args:
            article: Article to normalize

        Returns:
            Article with normalized title
        """
        if not article.title or not article.title.strip():
            article.title = "Untitled Article"
            logger.debug("Article has empty title, using fallback")
            return article

        # Clean up whitespace
        title = " ".join(article.title.split())

        # Enforce max length with smart truncation
        if len(title) > self.title_max_length:
            title = title[: self.title_max_length].rsplit(" ", 1)[0] + "..."
            logger.debug(f"Title truncated to {self.title_max_length} chars")

        article.title = title
        return article

    def _normalize_author(self, article: Article) -> Article:
        """
        Normalize author name: title case, cleanup whitespace, enforce max length.

        Args:
            article: Article to normalize

        Returns:
            Article with normalized author
        """
        if not article.author or not article.author.strip():
            return article

        # Clean up whitespace and apply title case
        author = " ".join(article.author.split())
        author = author.title()

        # Enforce max length with truncation
        if len(author) > self.author_max_length:
            author = author[: self.author_max_length].rsplit(" ", 1)[0] + "..."
            logger.debug(f"Author name truncated to {self.author_max_length} chars")

        article.author = author
        return article

    def _normalize_tags(self, article: Article) -> Article:
        """
        Normalize tags: lowercase, deduplicate, enforce limits.

        Args:
            article: Article to normalize

        Returns:
            Article with normalized tags
        """
        if not article.tags:
            return article

        # Normalize and deduplicate tags
        normalized_tags = []
        seen = set()

        for t in article.tags:
            # Clean up and lowercase
            tag = t.strip().lower()

            # Skip empty tags
            if not tag:
                continue

            tag = tag[: self.tag_max_length]

            # Deduplicate
            if tag not in seen:
                normalized_tags.append(tag)
                seen.add(tag)

            # Stop at max tags
            if len(normalized_tags) >= self.max_tags_per_article:
                break

        article.tags = normalized_tags
        return article

    def _normalize_url(self, article: Article) -> Article:
        """
        Normalize article URL: remove tracking params, ensure https.

        Args:
            article: Article to normalize

        Returns:
            Article with normalized URL
        """
        url_str = str(article.url)

        # Remove common tracking parameters
        tracking_params = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "campaign"]

        # Parse URL and rebuild without tracking params

        parsed = urlparse(url_str)

        # Filter out tracking params
        if parsed.query:
            query_params = parse_qs(parsed.query)
            filtered_params = {k: v for k, v in query_params.items() if k not in tracking_params}

            # Rebuild query string
            new_query = urlencode(filtered_params, doseq=True) if filtered_params else ""

            # Rebuild URL
            url_str = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

        # Ensure https (upgrade http to https)
        if url_str.startswith("http://"):
            url_str = "https://" + url_str[7:]

        article.url = url_str  # type: ignore
        return article

    def _enforce_content_length(self, article: Article) -> Article:
        """
        Enforce maximum content length with smart truncation.

        Args:
            article: Article to normalize

        Returns:
            Article with content truncated if needed
        """
        if not article.content or len(article.content) <= self.content_max_length:
            return article

        # Capture original length before truncation
        original_length = len(article.content)

        # Truncate at word boundary
        truncated = article.content[: self.content_max_length]
        truncated = truncated.rsplit(" ", 1)[0]

        article.content = truncated
        logger.debug(f"Content truncated from {original_length} to {len(truncated)} chars")

        return article


if __name__ == "__main__":
    import asyncio
    from datetime import datetime

    from pydantic import HttpUrl

    from app.processors.fetchers.base import Article

    async def test_normalizer():
        """Test script to verify ContentNormalizer functionality with real AI."""
        print("=" * 80)
        print("ContentNormalizer Test Script")
        print("=" * 80)

        # Initialize normalizer with default settings
        normalizer = ContentNormalizer()
        print("\n✓ Initialized ContentNormalizer with AI-powered spam detection")

        # Test 1: Valid article (should pass)
        print("\n" + "-" * 80)
        print("Test 1: Valid news article")
        print("-" * 80)
        valid_article = Article(
            title="OpenAI Announces GPT-5 with Revolutionary Capabilities",
            url=HttpUrl("https://example.com/article1"),
            content=textwrap.dedent("""\
                OpenAI has announced the release of GPT-5, their latest language model with groundbreaking
                capabilities. The new model features improved reasoning, better context handling, and multimodal
                understanding. Industry experts are calling it a significant leap forward in artificial
                intelligence technology. The release comes after months of rigorous testing and safety evaluations.
            """),
            published_at=datetime(2024, 1, 15, 10, 0),
            author="Tech Reporter",
            tags=["AI", "Technology"],
        )

        result = await normalizer.normalize(valid_article)
        if result:
            print(f"✓ Article ACCEPTED: '{result.title[:60]}...'")
        else:
            print(f"✗ Article REJECTED: '{valid_article.title[:60]}...'")

        # Test 2: Spam article (should be rejected)
        print("\n" + "-" * 80)
        print("Test 2: Obvious spam content")
        print("-" * 80)
        spam_article = Article(
            title="BUY NOW!!! AMAZING OFFER!!!",
            url=HttpUrl("https://example.com/spam"),
            content=textwrap.dedent("""\
                BUY NOW!!! Don't miss this AMAZING offer!!! Click here for LIMITED TIME DEAL!!!
                Act now and get 100% FREE with NO COST!!! WINNER WINNER WINNER!!!
                Call now! Order now! Subscribe now! Sign up now! Earn money fast!!!
                This is your chance to WIN BIG!!! Congratulations you are selected!!!
            """),
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        result = await normalizer.normalize(spam_article)
        if result:
            print(f"✗ Article ACCEPTED (should be rejected): '{spam_article.title[:60]}...'")
        else:
            print(f"✓ Article REJECTED (spam detected): '{spam_article.title[:60]}...'")

        # Test 3: Article too short (should be rejected)
        print("\n" + "-" * 80)
        print("Test 3: Content too short")
        print("-" * 80)
        short_article = Article(
            title="Short Article",
            url=HttpUrl("https://example.com/short"),
            content="This is too short.",
            published_at=datetime(2024, 1, 15, 10, 0),
        )

        result = await normalizer.normalize(short_article)
        if result:
            print(f"✗ Article ACCEPTED (should be rejected): '{short_article.title}'")
        else:
            print(f"✓ Article REJECTED (content too short): '{short_article.title}'")

        # Test 4: Legitimate article with promotional elements (should pass)
        print("\n" + "-" * 80)
        print("Test 4: Legitimate product announcement")
        print("-" * 80)
        product_article = Article(
            title="Apple Unveils New iPhone 16 with Advanced Features",
            url=HttpUrl("https://example.com/apple"),
            content=textwrap.dedent("""\
                Apple today announced the iPhone 16, featuring a revolutionary new A18 chip and enhanced
                camera system. The device will be available for pre-order starting next week at $999.
                The new phone includes improved battery life, 5G connectivity, and advanced AI capabilities.
                Industry analysts expect strong demand for the latest iteration of Apple's flagship product.
            """),
            published_at=datetime(2024, 1, 15, 10, 0),
            author="Apple Press",
            tags=["Apple", "iPhone", "Technology"],
        )

        result = await normalizer.normalize(product_article)
        if result:
            print(f"✓ Article ACCEPTED: '{result.title[:60]}...'")
        else:
            print(f"✗ Article REJECTED: '{product_article.title[:60]}...'")

        print("\n" + "=" * 80)
        print("Test Complete!")
        print("=" * 80)

    # Run the async test
    asyncio.run(test_normalizer())
