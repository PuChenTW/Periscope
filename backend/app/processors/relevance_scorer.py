"""
Relevance scoring processor for personalized content ranking.

This module provides deterministic keyword-based scoring with optional AI-powered
semantic enhancement for personalizing article relevance to user interests.
"""

import json
import textwrap
from datetime import UTC, datetime

from loguru import logger
from pydantic import BaseModel, Field

from app.config import PersonalizationSettings, get_settings
from app.models.users import InterestProfile
from app.processors.ai_provider import AIProvider, create_ai_provider
from app.processors.fetchers.base import Article
from app.utils.cache import CacheProtocol
from app.utils.text_processing import normalize_term_list, normalize_text


class SemanticRelevanceResult(BaseModel):
    """AI-determined semantic relevance with reasoning."""

    semantic_score: float = Field(
        ge=0.0,
        le=30.0,
        description="Semantic relevance score from 0.0 to 30.0",
    )
    matched_interests: list[str] = Field(
        default_factory=list,
        description="Top matched interest keywords (max 5)",
    )
    reasoning: str = Field(description="Brief explanation of relevance assessment")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in semantic scoring (0.0-1.0)",
    )


class RelevanceBreakdown(BaseModel):
    """Detailed breakdown of relevance scoring for explainability."""

    keyword_score: int = Field(ge=0, le=60, description="Keyword match score (0-60)")
    semantic_score: float = Field(ge=0.0, le=30.0, description="AI semantic score (0-30)")
    temporal_boost: int = Field(ge=0, le=5, description="Freshness boost (0-5)")
    quality_boost: int = Field(ge=0, le=5, description="Quality boost (0-5)")
    final_score: int = Field(ge=0, le=100, description="Final relevance score (0-100)")
    matched_keywords: list[str] = Field(default_factory=list, description="Matched interest keywords")
    threshold_passed: bool = Field(description="Whether score exceeds threshold")


class RelevanceResult(BaseModel):
    """Complete relevance scoring result for an article."""

    relevance_score: int = Field(ge=0, le=100, description="Final relevance score (0-100)")
    breakdown: RelevanceBreakdown = Field(description="Detailed scoring breakdown")
    passes_threshold: bool = Field(description="Whether article passes relevance threshold")
    matched_keywords: list[str] = Field(default_factory=list, description="Matched interest keywords")


class RelevanceScorer:
    """
    Scores article relevance to user interests using hybrid approach.

    Uses deterministic keyword matching (Stage 1: 0-60 points) with optional
    AI semantic enhancement (Stage 2: 0-30 points) plus temporal/quality boosts
    (Stage 3: 0-10 points) for personalized content ranking.
    """

    def __init__(
        self,
        cache: CacheProtocol,
        settings: PersonalizationSettings | None = None,
        ai_provider: AIProvider | None = None,
    ):
        """
        Initialize relevance scorer with configuration and dependencies.

        Args:
            cache: Cache instance for storing relevance results
            settings: Personalization settings (uses get_settings().personalization if not provided)
            ai_provider: AI provider instance (creates from settings if not provided)
        """
        self.settings = settings or get_settings().personalization
        self.cache = cache

        # Create AI provider if not injected
        if ai_provider is None:
            ai_provider = create_ai_provider(get_settings())

        # Initialize PydanticAI agent for semantic scoring
        self.agent = ai_provider.create_agent(
            output_type=SemanticRelevanceResult,
            system_prompt=textwrap.dedent("""\
                You are an expert at assessing content relevance to user interests.

                Your task is to determine how relevant an article is to a user's interest keywords
                based on semantic understanding, not just exact keyword matches.

                Consider:
                1. Topical alignment with user interests
                2. Conceptual overlap with interest areas
                3. Relevance to user's knowledge domain
                4. Value for the user's interests

                Provide a semantic score from 0.0 to 30.0:
                - 25-30: Highly relevant, directly addresses user interests
                - 15-24: Moderately relevant, related to user interests
                - 5-14: Somewhat relevant, tangentially related
                - 0-4: Not relevant, minimal connection

                Also identify the top 5 matched user interests and provide brief reasoning.
            """),
        )

    async def score_article(
        self,
        article: Article,
        profile: InterestProfile,
        quality_score: int | None = None,
    ) -> RelevanceResult:
        """
        Score article relevance to user profile.

        Args:
            article: Article to score
            profile: User interest profile
            quality_score: Optional quality score from QualityScorer (used for quality boost)

        Returns:
            RelevanceResult with scoring details
        """
        # Handle empty profile: score 0 but pass threshold (users without interests see content)
        if not profile.keywords:
            logger.debug("Empty interest profile, setting relevance score to 0 (threshold passed)")
            breakdown = RelevanceBreakdown(
                keyword_score=0,
                semantic_score=0.0,
                temporal_boost=0,
                quality_boost=0,
                final_score=0,
                matched_keywords=[],
                threshold_passed=True,
            )
            return RelevanceResult(
                relevance_score=0,
                breakdown=breakdown,
                passes_threshold=True,
                matched_keywords=[],
            )

        # Check cache first
        cache_key = self._generate_cache_key(profile, article)
        cached_result = await self._get_cached_relevance(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for article: {article.title[:50]}...")
            return cached_result

        # Parse and normalize keywords
        keywords = normalize_term_list(profile.keywords, self.settings.max_keywords)

        # Stage 1: Keyword matching (0-60 points)
        keyword_index = self._build_keyword_index(article)
        keyword_score, matched_keywords = self._score_keyword_matches(keywords, keyword_index)

        # Stage 2: Semantic scoring (skip if score obviously too high/low)
        semantic_score = 0.0
        should_run_ai = (
            self.settings.enable_semantic_scoring
            and keyword_score < 55  # Don't waste AI on clearly relevant articles
            and (keyword_score > 15 or profile.boost_factor > 1.0)  # Skip obviously irrelevant unless boosted
        )
        if should_run_ai:
            semantic_score = await self._score_semantic_relevance(article, keywords)

        # Stage 3: Temporal & quality boost (0-10 points)
        temporal_boost = self._calculate_temporal_boost(article)
        quality_boost = self._calculate_quality_boost(quality_score, len(matched_keywords))

        # Calculate final score with boost factor
        raw_score = keyword_score + semantic_score + temporal_boost + quality_boost
        final_score = min(100, max(0, int(raw_score * profile.boost_factor)))

        # Check threshold
        threshold = profile.relevance_threshold
        passes_threshold = final_score >= threshold

        # Build result
        breakdown = RelevanceBreakdown(
            keyword_score=keyword_score,
            semantic_score=semantic_score,
            temporal_boost=temporal_boost,
            quality_boost=quality_boost,
            final_score=final_score,
            matched_keywords=matched_keywords,
            threshold_passed=passes_threshold,
        )

        result = RelevanceResult(
            relevance_score=final_score,
            breakdown=breakdown,
            passes_threshold=passes_threshold,
            matched_keywords=matched_keywords,
        )

        # Cache the result
        await self._cache_relevance(cache_key, result)

        logger.debug(
            f"Scored article '{article.title[:50]}...': "
            f"keyword={keyword_score}, semantic={semantic_score:.1f}, "
            f"temporal={temporal_boost}, quality={quality_boost}, "
            f"final={final_score} (threshold={threshold}, passes={passes_threshold})"
        )

        return result

    def _build_keyword_index(self, article: Article) -> dict[str, list[str]]:
        """
        Build searchable keyword index from article content.

        Args:
            article: Article to index

        Returns:
            Dictionary with 'title', 'content', 'tags' keys containing normalized tokens
        """
        return {
            "title": normalize_text(article.title),
            "content": normalize_text(article.content),
            "tags": normalize_text(" ".join(article.tags)) if article.tags else [],
        }

    def _score_keyword_matches(
        self,
        keywords: list[str],
        keyword_index: dict[str, list[str]],
    ) -> tuple[int, list[str]]:
        """
        Score keyword matches across article fields with weights.

        Args:
            keywords: Normalized user interest keywords
            keyword_index: Article keyword index (title, content, tags)

        Returns:
            Tuple of (total_score, matched_keywords)
        """
        matched_keywords = set()
        score = 0

        # Convert article tokens to set for fast lookup
        title_tokens = set(keyword_index["title"])
        content_tokens = set(keyword_index["content"])
        tag_tokens = set(keyword_index["tags"])

        for keyword in keywords:
            # Split multi-word keywords and check if all tokens present
            keyword_tokens = keyword.split()

            # Title matches (weight 3)
            if all(token in title_tokens for token in keyword_tokens):
                score += self.settings.keyword_weight_title
                matched_keywords.add(keyword)

            # Content matches (weight 2)
            elif all(token in content_tokens for token in keyword_tokens):
                score += self.settings.keyword_weight_content
                matched_keywords.add(keyword)

            # Tag/topic matches (weight 4)
            elif all(token in tag_tokens for token in keyword_tokens):
                score += self.settings.keyword_weight_tags
                matched_keywords.add(keyword)

        # Clamp to 60 points max
        score = min(60, score)

        return score, sorted(matched_keywords)

    async def _score_semantic_relevance(self, article: Article, keywords: list[str]) -> float:
        """
        Score semantic relevance using AI.

        Args:
            article: Article to score
            keywords: Normalized user interest keywords

        Returns:
            Semantic relevance score (0.0-30.0), 0.0 on error
        """
        try:
            prompt = self._build_semantic_prompt(article, keywords)
            result = await self.agent.run(prompt)
            semantic_result = result.output

            logger.debug(
                f"AI semantic score for '{article.title[:50]}...': {semantic_result.semantic_score:.1f} "
                f"(confidence: {semantic_result.confidence:.2f}, "
                f"matched: {', '.join(semantic_result.matched_interests[:3])})"
            )

            return semantic_result.semantic_score

        except Exception as e:
            logger.warning(f"AI semantic scoring failed for article '{article.title[:50]}...': {e}")
            return 0.0

    def _build_semantic_prompt(self, article: Article, keywords: list[str]) -> str:
        """
        Build prompt for AI semantic relevance scoring.

        Args:
            article: Article to score
            keywords: User interest keywords

        Returns:
            Formatted prompt string
        """
        # Truncate content to 800 chars
        content_preview = article.content[:800] if article.content else ""

        # Include existing summary and topics if available
        summary = article.summary or "No summary available"
        topics = ", ".join(article.ai_topics) if article.ai_topics else "No topics extracted"

        return textwrap.dedent(f"""\
            User Interest Keywords: {", ".join(keywords)}

            Article:
            Title: {article.title}
            Summary: {summary}
            Topics: {topics}
            Content Preview: {content_preview}
            Tags: {", ".join(article.tags) if article.tags else "None"}

            Assess how relevant this article is to the user's interests.
        """)

    def _calculate_temporal_boost(self, article: Article) -> int:
        """
        Calculate temporal boost for fresh content (0-5 points for articles <= 24h old).

        Args:
            article: Article to evaluate

        Returns:
            Temporal boost points (0-5)
        """
        if not article.published_at:
            return 0

        age_hours = (datetime.now(UTC) - article.published_at.replace(tzinfo=UTC)).total_seconds() / 3600
        return max(0, min(5, int(5 * (1 - age_hours / 24)))) if age_hours <= 24 else 0

    def _calculate_quality_boost(self, quality_score: int | None, keyword_matches: int) -> int:
        """
        Calculate quality boost for high-quality content.

        High quality articles (score >= 80) with at least one keyword match get +5 points.

        Args:
            quality_score: Quality score from QualityScorer (0-100), or None if not available
            keyword_matches: Number of matched keywords

        Returns:
            Quality boost points (0-5)
        """
        # Require at least one keyword match
        if keyword_matches == 0:
            return 0

        # Check quality score
        if quality_score is not None and quality_score >= 80:
            return 5

        return 0

    def _generate_cache_key(self, profile: InterestProfile, article: Article) -> str:
        """
        Generate cache key for relevance result.

        Uses profile ID and article URL for unique identification.
        URL is sufficient as it uniquely identifies articles.

        Args:
            profile: User interest profile
            article: Article being scored

        Returns:
            Cache key string
        """
        # Use URL directly - it's unique per article and more debuggable than hashes
        return f"relevance:{profile.id}:{article.url}"

    async def _get_cached_relevance(self, cache_key: str) -> RelevanceResult | None:
        """
        Retrieve cached relevance result.

        Args:
            cache_key: Cache key

        Returns:
            Cached RelevanceResult or None if not found
        """
        try:
            cached = await self.cache.get(cache_key)
            if cached:
                data = json.loads(cached)
                return RelevanceResult(**data)
        except Exception as e:
            logger.warning(f"Error retrieving cached relevance: {e}")
        return None

    async def _cache_relevance(self, cache_key: str, result: RelevanceResult) -> None:
        """
        Cache relevance result.

        Args:
            cache_key: Cache key
            result: RelevanceResult to cache
        """
        try:
            ttl_seconds = self.settings.cache_ttl_minutes * 60
            await self.cache.setex(cache_key, ttl_seconds, result.model_dump_json())
        except Exception as e:
            logger.warning(f"Error caching relevance result: {e}")
