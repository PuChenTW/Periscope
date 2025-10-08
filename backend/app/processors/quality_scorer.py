"""
Content quality scoring service for article ranking and prioritization.

This module provides hybrid quality assessment combining rule-based metadata
scoring with AI-powered content quality analysis.
"""

import textwrap

from loguru import logger
from pydantic import BaseModel, Field

from app.config import get_settings
from app.processors.ai_provider import AIProvider, create_ai_provider
from app.processors.fetchers.base import Article


class ContentQualityResult(BaseModel):
    """AI-powered content quality assessment result."""

    writing_quality: int = Field(description="Writing quality and coherence score (0-20)", ge=0, le=20)
    informativeness: int = Field(description="Informativeness and depth score (0-20)", ge=0, le=20)
    credibility: int = Field(description="Credibility and sourcing score (0-10)", ge=0, le=10)
    reasoning: str = Field(description="Explanation of the quality assessment")


class QualityScorer:
    """
    Assesses article quality using hybrid scoring approach.

    Combines rule-based metadata scoring with AI-powered content quality assessment
    to produce a final quality score (0-100 scale). This score can be used for
    article ranking, filtering, and prioritization in the content pipeline.
    """

    def __init__(
        self,
        quality_scoring_enabled: bool = True,
        ai_provider: AIProvider | None = None,
    ):
        """
        Initialize quality scorer with configuration and AI provider.

        Args:
            quality_scoring_enabled: Enable AI-powered quality assessment (default: True)
            ai_provider: AI provider instance (creates default if not provided)
        """
        self.quality_scoring_enabled = quality_scoring_enabled

        # Create AI provider if not injected
        settings = get_settings()
        provider = ai_provider or create_ai_provider(settings)

        # Initialize PydanticAI agent for quality assessment
        self.quality_agent = provider.create_agent(
            output_type=ContentQualityResult,
            system_prompt=textwrap.dedent("""\
                You are an expert at assessing content quality.
                Your task is to evaluate article quality across three dimensions:

                1. Writing Quality (0-20 points):
                   - Clear and coherent writing style
                   - Proper grammar and structure
                   - Logical flow and organization
                   - Readability and engagement

                2. Informativeness (0-20 points):
                   - Depth of information provided
                   - Coverage of the topic
                   - Value and usefulness to readers
                   - Specific details and insights

                3. Credibility (0-10 points):
                   - Evidence of research or sources
                   - Balanced perspective
                   - Professional tone
                   - Trustworthiness indicators

                Provide scores for each dimension and clear reasoning for your assessment.
            """),
        )

    async def calculate_quality_score(self, article: Article) -> Article:
        """
        Calculate hybrid quality score combining rule-based and AI assessment.

        Args:
            article: Article to score

        Returns:
            Article with quality_score in metadata
        """
        # Calculate rule-based metadata score (0-50)
        metadata_score = self._calculate_metadata_score(article)

        # Calculate AI-powered content quality score (0-50) and combine
        ai_content_score = 0
        if self.quality_scoring_enabled:
            quality_result = await self._assess_content_quality(article)
            ai_content_score = (
                quality_result.writing_quality + quality_result.informativeness + quality_result.credibility
            )
            quality_score = metadata_score + ai_content_score
        else:
            # When AI scoring is disabled, scale metadata score to 0-100
            quality_score = metadata_score * 2

        # Store in metadata
        article.metadata["quality_score"] = quality_score
        article.metadata["quality_breakdown"] = {"metadata_score": metadata_score, "ai_content_score": ai_content_score}

        logger.debug(
            f"Quality score for '{article.title[:50]}...': "
            f"total={quality_score}, metadata={metadata_score}, ai={ai_content_score}"
        )

        return article

    def _calculate_metadata_score(self, article: Article) -> int:
        """
        Calculate rule-based metadata completeness score (0-50 points).

        Scoring:
        - Has author: +10
        - Has published_at: +10
        - Has tags (1+): +5
        - Content > 500 chars: +15
        - Content > 1000 chars: +10 bonus

        Args:
            article: Article to score

        Returns:
            Metadata score (0-50)
        """
        score = 0

        # Author presence
        if article.author and article.author.strip():
            score += 10

        # Published date presence
        if article.published_at:
            score += 10

        # Tags presence
        if article.tags and len(article.tags) > 0:
            score += 5

        # Content length scoring
        content_length = len(article.content) if article.content else 0
        if content_length > 500:
            score += 15
            if content_length > 1000:
                score += 10  # Bonus for longer content

        return score

    async def _assess_content_quality(self, article: Article) -> ContentQualityResult:
        """
        Assess content quality using AI (0-50 points).

        Args:
            article: Article to assess

        Returns:
            ContentQualityResult with scores for writing, informativeness, credibility
        """
        # Truncate content to avoid token limits (use first 1500 chars for quality assessment)
        content = article.content[:1500] if article.content else ""

        # Build prompt for AI quality assessment
        prompt = textwrap.dedent(f"""\
            Article Title: {article.title}
            Content: {content}

            Assess the quality of this article content across three dimensions:
            1. Writing Quality (0-20): Clarity, coherence, grammar, structure
            2. Informativeness (0-20): Depth, coverage, value, insights
            3. Credibility (0-10): Evidence, balance, professionalism
        """)

        try:
            # Run AI quality assessment
            result = await self.quality_agent.run(prompt)
            quality_result = result.output

            logger.debug(
                f"Quality assessment for '{article.title[:50]}...': "
                f"writing={quality_result.writing_quality}, "
                f"info={quality_result.informativeness}, "
                f"credibility={quality_result.credibility}"
            )

            return quality_result

        except Exception as e:
            logger.error(f"Error during AI quality assessment for article '{article.title[:50]}...': {e}")
            # On error, return neutral scores
            return ContentQualityResult(
                writing_quality=10,
                informativeness=10,
                credibility=5,
                reasoning="Error during assessment, using neutral scores",
            )
