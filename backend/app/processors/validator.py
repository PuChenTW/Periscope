"""
Content validation service for article quality checks.

This module provides validation logic for articles including empty content checks,
minimum length requirements, and AI-powered spam detection. Validation returns
detailed results for observability and downstream decision-making.
"""

import textwrap

from loguru import logger
from pydantic import BaseModel, Field

from app.config import ContentNormalizationSettings, get_settings
from app.processors.ai_provider import AIProvider, create_ai_provider
from app.processors.fetchers.base import Article


class ValidationResult(BaseModel):
    """Result of content validation for a single article."""

    is_empty: bool = Field(description="Content is empty/whitespace-only")
    is_too_short: bool = Field(description="Below min_length threshold")
    is_spam: bool = Field(description="AI-detected spam")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Spam confidence score")
    validation_message: str = Field(description="Human-readable validation status")

    @property
    def is_valid(self) -> bool:
        """Returns True if article passed all validation checks."""
        return not (self.is_empty or self.is_too_short or self.is_spam)


class SpamDetectionResult(BaseModel):
    """AI-powered spam detection result with reasoning."""

    is_spam: bool = Field(description="Whether the content is spam")
    confidence: float = Field(description="Confidence score (0.0-1.0)")
    reasoning: str = Field(description="Explanation of the spam determination")


class ContentValidator:
    """
    Validates article content for quality and spam detection.

    This class performs stateless validation checks on articles:
    - Empty/whitespace-only content detection
    - Minimum length enforcement
    - AI-powered spam detection (optional)

    Returns detailed ValidationResult for observability.
    Does not mutate articles or cache results (caching handled by callers).
    """

    def __init__(
        self,
        settings: ContentNormalizationSettings | None = None,
        ai_provider: AIProvider | None = None,
    ):
        """
        Initialize validator with configuration and AI provider.

        Args:
            settings: Content normalization settings (uses get_settings().content if not provided)
            ai_provider: AI provider instance (creates default if not provided)
        """
        self.settings = settings or get_settings().content

        # Extract validation settings
        self.content_min_length = self.settings.min_length
        self.spam_detection_enabled = self.settings.spam_detection_enabled

        # Create AI provider if not injected
        provider = ai_provider or create_ai_provider(get_settings())

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

    async def validate_article(self, article: Article) -> ValidationResult:
        """
        Validate article content for quality standards.

        Performs three checks in sequence:
        1. Empty content check (non-empty, non-whitespace)
        2. Minimum length check
        3. AI-powered spam detection (if enabled)

        Args:
            article: Article to validate

        Returns:
            ValidationResult with validation status and details
        """
        # Check 1: Empty or whitespace-only content
        is_empty = not article.content or not article.content.strip()
        if is_empty:
            logger.debug(f"Article rejected - empty: {article.title[:50]}...")
            return ValidationResult(
                is_empty=True,
                is_too_short=False,
                is_spam=False,
                confidence=0.0,
                validation_message="Content is empty or whitespace-only",
            )

        # Check 2: Minimum content length
        content_length = len(article.content.strip())
        is_too_short = content_length < self.content_min_length
        if is_too_short:
            logger.debug(f"Article rejected - too short: {article.title[:50]}...")
            return ValidationResult(
                is_empty=False,
                is_too_short=True,
                is_spam=False,
                confidence=0.0,
                validation_message=f"Content too short ({content_length} chars, minimum {self.content_min_length})",
            )

        # Check 3: AI spam detection (if enabled)
        is_spam = False
        confidence = 0.0

        if self.spam_detection_enabled:
            is_spam = await self._detect_spam(article)
            confidence = 1.0 if is_spam else 0.0

            if is_spam:
                logger.debug(f"Article rejected - spam: {article.title[:50]}...")
                return ValidationResult(
                    is_empty=False,
                    is_too_short=False,
                    is_spam=True,
                    confidence=confidence,
                    validation_message="Detected as spam",
                )

        # All checks passed
        return ValidationResult(
            is_empty=False,
            is_too_short=False,
            is_spam=False,
            confidence=confidence,
            validation_message="Valid",
        )

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
