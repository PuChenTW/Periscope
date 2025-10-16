"""
Content processing activities for Temporal workflows.

This module contains Temporal activities that wrap processor logic for
orchestrated execution within workflows. Activities are idempotent and
support retry logic defined in shared.py.
"""

import hashlib
from datetime import UTC, datetime

from loguru import logger
from pydantic import BaseModel, Field
from temporalio import activity

from app.config import get_settings
from app.database import get_async_sessionmaker
from app.exceptions import ValidationError
from app.processors.ai_provider import create_ai_provider
from app.processors.fetchers.base import Article
from app.processors.normalizer import ContentNormalizer
from app.processors.quality_scorer import ContentQualityResult, QualityScorer
from app.processors.relevance_scorer import RelevanceResult, RelevanceScorer
from app.processors.topic_extractor import TopicExtractor
from app.repositories import ProfileRepository
from app.utils.redis_client import get_redis_client

# ============================================================================
# Request/Result Models
# ============================================================================


class BatchNormalizationRequest(BaseModel):
    """Request for batch article normalization."""

    articles: list[Article] = Field(description="Articles to normalize")


class BatchNormalizationResult(BaseModel):
    """Result of batch article normalization."""

    articles: list[Article] = Field(description="Normalized articles (rejected articles filtered out)")
    total_processed: int = Field(description="Total articles processed")
    rejected_count: int = Field(description="Articles rejected (spam, too short, etc.)")
    spam_detected_count: int = Field(description="Articles rejected as spam")

    # Standard observability
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made (spam detection)")
    errors_count: int = Field(default=0, description="Number of errors encountered")


class BatchQualityRequest(BaseModel):
    """Request for batch quality scoring."""

    articles: list[Article] = Field(description="Articles to score")


class BatchQualityResult(BaseModel):
    """Result of batch quality scoring."""

    articles: list[Article] = Field(description="Original articles (unchanged)")
    quality_results: dict[str, ContentQualityResult] = Field(description="Quality results keyed by article.url")
    total_scored: int = Field(description="Total articles scored")
    cache_hits: int = Field(description="Number of results served from cache")

    # Standard observability
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made")
    errors_count: int = Field(default=0, description="Number of errors encountered")


class BatchTopicExtractionRequest(BaseModel):
    """Request for batch topic extraction."""

    articles: list[Article] = Field(description="Articles to extract topics from")


class BatchTopicExtractionResult(BaseModel):
    """Result of batch topic extraction."""

    articles: list[Article] = Field(description="Articles with ai_topics populated")
    total_processed: int = Field(description="Total articles processed")
    articles_with_topics: int = Field(description="Articles that got non-empty topics")
    cache_hits: int = Field(description="Number of results served from cache")

    # Standard observability
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made")
    errors_count: int = Field(default=0, description="Number of errors encountered")


class BatchRelevanceRequest(BaseModel):
    """Request for batch relevance scoring."""

    profile_id: str = Field(description="Interest profile ID to score against")
    articles: list[Article] = Field(description="List of articles to score")
    quality_scores: dict[str, int] | None = Field(
        default=None,
        description="Optional quality scores keyed by article.url (from QualityScorer activity)",
    )


class BatchRelevanceResult(BaseModel):
    """Result of batch relevance scoring."""

    articles: list[Article] = Field(description="Original articles (unchanged)")
    relevance_results: dict[str, RelevanceResult] = Field(description="Relevance results keyed by article.url")
    profile_id: str = Field(description="Interest profile ID used for scoring")
    total_scored: int = Field(description="Total articles scored")
    cache_hits: int = Field(description="Number of results served from cache")

    # Standard observability
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made (excluding cache hits)")
    errors_count: int = Field(default=0, description="Number of errors encountered (with fallbacks applied)")


# ============================================================================
# ProcessingActivities Class
# ============================================================================


class ProcessingActivities:
    """
    Activity class managing all content processing activities.

    Centralizes dependency initialization (settings, Redis, DB, AI provider)
    and provides activity methods decorated with @activity.defn.
    """

    def __init__(self):
        """Initialize shared dependencies for all activities."""
        self.settings = get_settings()
        self.redis_client = get_redis_client()
        self.async_session_maker = get_async_sessionmaker()
        self.ai_provider = create_ai_provider(self.settings)

    # ========================================================================
    # Activity 1: Normalize Articles
    # ========================================================================

    @activity.defn(name="normalize_articles_batch")
    async def normalize_articles_batch(self, request: BatchNormalizationRequest) -> BatchNormalizationResult:
        """
        Normalize a batch of articles with validation and spam detection.

        This activity wraps ContentNormalizer to provide batch processing with
        spam detection caching. Rejected articles (spam, too short, empty content)
        are filtered out from the result.

        Idempotency Contract:
        - Cache key (spam only): f"spam:{content_hash}"
        - Cache TTL: ai_validation.cache_ttl_minutes (default 1440 min)
        - Behavior: Cached spam results skip AI detection

        Args:
            request: BatchNormalizationRequest containing articles

        Returns:
            BatchNormalizationResult with normalized articles and metrics

        Activity Options:
            - Timeout: MEDIUM_TIMEOUT (30s)
            - Retry: MEDIUM_RETRY_POLICY (3 attempts, 5s-45s backoff)
            - Idempotent: Yes (via spam detection cache)
        """
        start_timestamp = datetime.now(UTC)

        # Initialize normalizer
        normalizer = ContentNormalizer(
            settings=self.settings.content,
            ai_provider=self.ai_provider,
        )

        # Track metrics
        normalized_articles: list[Article] = []
        rejected_count = 0
        spam_detected_count = 0
        ai_calls = 0
        errors_count = 0

        # Process each article
        for article in request.articles:
            try:
                # Normalize article (returns None if rejected)
                normalized = await normalizer.normalize(article)

                if normalized is None:
                    rejected_count += 1
                    # Check if it was spam by re-running spam detection with cache
                    if self.settings.content.spam_detection_enabled:
                        cache_key = self._compute_spam_cache_key(article)
                        cached_spam = await self.redis_client.get(cache_key)
                        if cached_spam and cached_spam.decode() == "true":
                            spam_detected_count += 1
                    logger.debug(f"Article rejected: {article.title[:50]}...")
                else:
                    normalized_articles.append(normalized)
                    # Count AI call if spam detection was enabled and ran
                    if self.settings.content.spam_detection_enabled:
                        cache_key = self._compute_spam_cache_key(article)
                        cached_spam = await self.redis_client.get(cache_key)
                        if not cached_spam:  # Cache miss means AI ran
                            ai_calls += 1

            except Exception as e:
                errors_count += 1
                rejected_count += 1
                logger.error(f"Failed to normalize article {article.url}: {e}")

        end_timestamp = datetime.now(UTC)

        return BatchNormalizationResult(
            articles=normalized_articles,
            total_processed=len(request.articles),
            rejected_count=rejected_count,
            spam_detected_count=spam_detected_count,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            ai_calls=ai_calls,
            errors_count=errors_count,
        )

    def _compute_spam_cache_key(self, article: Article) -> str:
        """Compute cache key for spam detection based on content hash."""
        content = f"{article.title}:{article.content[:1000] if article.content else ''}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"spam:{content_hash}"

    # ========================================================================
    # Activity 2: Score Quality
    # ========================================================================

    @activity.defn(name="score_quality_batch")
    async def score_quality_batch(self, request: BatchQualityRequest) -> BatchQualityResult:
        """
        Score quality for a batch of articles using hybrid scoring.

        This activity wraps QualityScorer to provide idempotent batch processing
        with cache-based deduplication. The cache key uses article URL hash.

        Idempotency Contract:
        - Cache key: f"quality:{url_hash}"
        - Cache TTL: content.quality_cache_ttl_minutes (default 720 min)
        - Behavior: Cached results are returned immediately, skipping AI scoring

        Args:
            request: BatchQualityRequest containing articles

        Returns:
            BatchQualityResult containing articles and their quality scores

        Activity Options:
            - Timeout: LONG_TIMEOUT (120s)
            - Retry: LONG_RETRY_POLICY (2 attempts, 15s-120s backoff)
            - Idempotent: Yes (via cache key check)
        """
        start_timestamp = datetime.now(UTC)

        # Initialize quality scorer
        scorer = QualityScorer(
            settings=self.settings.content,
            ai_provider=self.ai_provider,
        )

        # Track metrics
        quality_results: dict[str, ContentQualityResult] = {}
        cache_hits = 0
        ai_calls = 0
        errors_count = 0

        # Score each article with caching and error handling
        for article in request.articles:
            try:
                # Compute cache key based on URL hash
                cache_key = self._compute_quality_cache_key(article)

                # Check cache for idempotency
                cached_result = await self.redis_client.get(cache_key)
                if cached_result:
                    # Cache hit: deserialize and use cached result
                    result = ContentQualityResult.model_validate_json(cached_result)
                    quality_results[str(article.url)] = result
                    cache_hits += 1
                    logger.debug(f"Cache hit for quality: {article.url}")
                    continue

                # Cache miss: score article
                result = await scorer.calculate_quality_score(article)

                # Count AI call if quality scoring was enabled and score > metadata-only
                if self.settings.content.quality_scoring_enabled and result.ai_content_score > 0:
                    ai_calls += 1

                # Cache result
                cache_ttl_seconds = self.settings.content.quality_cache_ttl_minutes * 60
                await self.redis_client.setex(cache_key, cache_ttl_seconds, result.model_dump_json())

                quality_results[str(article.url)] = result
                logger.debug(f"Scored quality: {article.url} (score={result.quality_score})")

            except Exception as e:
                # Log error and continue with remaining articles
                errors_count += 1
                logger.error(f"Failed to score quality for article {article.url}: {e}")

        end_timestamp = datetime.now(UTC)

        return BatchQualityResult(
            articles=request.articles,
            quality_results=quality_results,
            total_scored=len(quality_results),
            cache_hits=cache_hits,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            ai_calls=ai_calls,
            errors_count=errors_count,
        )

    def _compute_quality_cache_key(self, article: Article) -> str:
        """Compute cache key for quality scoring based on URL hash."""
        url_hash = hashlib.sha256(str(article.url).encode()).hexdigest()[:16]
        return f"quality:{url_hash}"

    # ========================================================================
    # Activity 3: Extract Topics
    # ========================================================================

    @activity.defn(name="extract_topics_batch")
    async def extract_topics_batch(self, request: BatchTopicExtractionRequest) -> BatchTopicExtractionResult:
        """
        Extract topics from a batch of articles using AI.

        This activity wraps TopicExtractor to provide idempotent batch processing
        with cache-based deduplication. Articles are mutated to populate ai_topics field.

        Idempotency Contract:
        - Cache key: f"topics:{url_hash}"
        - Cache TTL: topic_extraction.cache_ttl_minutes (default 1440 min)
        - Behavior: Cached results are returned immediately, skipping AI extraction

        Args:
            request: BatchTopicExtractionRequest containing articles

        Returns:
            BatchTopicExtractionResult with articles containing ai_topics

        Activity Options:
            - Timeout: LONG_TIMEOUT (120s)
            - Retry: LONG_RETRY_POLICY (2 attempts, 15s-120s backoff)
            - Idempotent: Yes (via cache key check)
        """
        start_timestamp = datetime.now(UTC)

        # Initialize topic extractor
        extractor = TopicExtractor(
            settings=self.settings.topic_extraction,
            ai_provider=self.ai_provider,
        )

        # Track metrics
        articles_with_topics: list[Article] = []
        cache_hits = 0
        ai_calls = 0
        errors_count = 0
        topics_count = 0

        # Extract topics for each article with caching
        for article in request.articles:
            try:
                # Compute cache key based on URL hash
                cache_key = self._compute_topics_cache_key(article)

                # Check cache for idempotency
                cached_topics = await self.redis_client.get(cache_key)
                if cached_topics:
                    # Cache hit: deserialize topics list
                    topics = [t.strip() for t in cached_topics.decode().split(",") if t.strip()]
                    cache_hits += 1
                    logger.debug(f"Cache hit for topics: {article.url}")
                else:
                    # Cache miss: extract topics
                    topics = await extractor.extract_topics(article)

                    # Count AI call if topics were extracted (non-empty result or AI ran)
                    if topics or (article.content and len(article.content.strip()) >= 50):
                        ai_calls += 1

                    # Cache result (even if empty list)
                    cache_ttl_seconds = self.settings.topic_extraction.cache_ttl_minutes * 60
                    topics_str = ",".join(topics) if topics else ""
                    await self.redis_client.setex(cache_key, cache_ttl_seconds, topics_str)

                    logger.debug(f"Extracted topics: {article.url} (topics={topics})")

                # Mutate article to add topics
                article_with_topics = article.model_copy(update={"ai_topics": topics})
                articles_with_topics.append(article_with_topics)

                if topics:
                    topics_count += 1

            except Exception as e:
                # Log error and continue with remaining articles (use article without topics)
                errors_count += 1
                logger.error(f"Failed to extract topics for article {article.url}: {e}")
                # Add article without topics
                articles_with_topics.append(article.model_copy(update={"ai_topics": []}))

        end_timestamp = datetime.now(UTC)

        return BatchTopicExtractionResult(
            articles=articles_with_topics,
            total_processed=len(request.articles),
            articles_with_topics=topics_count,
            cache_hits=cache_hits,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            ai_calls=ai_calls,
            errors_count=errors_count,
        )

    def _compute_topics_cache_key(self, article: Article) -> str:
        """Compute cache key for topic extraction based on URL hash."""
        url_hash = hashlib.sha256(str(article.url).encode()).hexdigest()[:16]
        return f"topics:{url_hash}"

    # ========================================================================
    # Activity 4: Score Relevance
    # ========================================================================

    @activity.defn(name="score_relevance_batch")
    async def score_relevance_batch(self, request: BatchRelevanceRequest) -> BatchRelevanceResult:
        """
        Score relevance for a batch of articles against user interest profile.

        This activity wraps RelevanceScorer to provide idempotent batch processing
        with cache-based deduplication. The cache key uses a hash of profile content
        (keywords, threshold, boost_factor) combined with article URL, enabling
        cache sharing across users with identical interest profiles.

        Idempotency Contract:
        - Cache key: f"relevance:{profile_hash}:{article.url}"
        - Cache TTL: personalization.cache_ttl_minutes (default 720 min)
        - Behavior: Cached results are returned immediately, skipping AI scoring

        Args:
            request: BatchRelevanceRequest containing profile ID and articles

        Returns:
            BatchRelevanceResult containing articles and their relevance scores

        Raises:
            ValidationError: If profile not found or invalid
            ExternalServiceError: If AI provider fails (retryable)

        Activity Options:
            - Timeout: MEDIUM_TIMEOUT (30s)
            - Retry: MEDIUM_RETRY_POLICY (3 attempts, 5s-45s backoff)
            - Idempotent: Yes (via cache key check)
        """
        start_timestamp = datetime.now(UTC)

        # Fetch profile from database
        async with self.async_session_maker() as session:
            profile_repo = ProfileRepository(session)
            profile = await profile_repo.get_by_id(request.profile_id)

        if profile is None:
            raise ValidationError(f"Interest profile not found: {request.profile_id}")

        # Initialize RelevanceScorer
        scorer = RelevanceScorer(
            settings=self.settings.personalization,
            ai_provider=self.ai_provider,
        )

        # Track metrics
        relevance_results: dict[str, RelevanceResult] = {}
        cache_hits = 0
        ai_calls = 0
        errors_count = 0

        # Score each article with caching and error handling
        for article in request.articles:
            try:
                # Compute cache key based on profile content hash
                cache_key = self._compute_relevance_cache_key(
                    article,
                    profile.keywords,
                    profile.relevance_threshold,
                    profile.boost_factor,
                )

                # Check cache for idempotency
                cached_result = await self.redis_client.get(cache_key)
                if cached_result:
                    # Cache hit: deserialize and use cached result
                    result = RelevanceResult.model_validate_json(cached_result)
                    relevance_results[str(article.url)] = result
                    cache_hits += 1
                    logger.debug(f"Cache hit for relevance: {article.url}")
                    continue

                # Cache miss: score article
                quality_score = request.quality_scores.get(str(article.url)) if request.quality_scores else None

                result = await scorer.score_article(article, profile, quality_score)

                # Count AI call if semantic scoring was enabled and score changed
                if self.settings.personalization.enable_semantic_scoring and result.breakdown.semantic_score > 0:
                    ai_calls += 1

                # Cache result
                cache_ttl_seconds = self.settings.personalization.cache_ttl_minutes * 60
                await self.redis_client.setex(cache_key, cache_ttl_seconds, result.model_dump_json())

                relevance_results[str(article.url)] = result
                logger.debug(f"Scored relevance: {article.url} (score={result.relevance_score})")

            except Exception as e:
                # Log error and continue with remaining articles
                errors_count += 1
                logger.error(f"Failed to score relevance for article {article.url}: {e}")

        end_timestamp = datetime.now(UTC)

        return BatchRelevanceResult(
            articles=request.articles,
            relevance_results=relevance_results,
            profile_id=request.profile_id,
            total_scored=len(relevance_results),
            cache_hits=cache_hits,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            ai_calls=ai_calls,
            errors_count=errors_count,
        )

    def _compute_relevance_cache_key(
        self, article: Article, profile_keywords: list[str], relevance_threshold: int, boost_factor: float
    ) -> str:
        """
        Compute cache key for relevance scoring based on profile content hash.

        Uses SHA256 hash of profile content (keywords, threshold, boost_factor)
        combined with article URL. This enables cache sharing across users with
        identical interest profiles.

        Args:
            article: Article to score
            profile_keywords: List of interest keywords from profile
            relevance_threshold: Relevance threshold from profile
            boost_factor: Boost factor from profile

        Returns:
            Cache key string in format "relevance:{profile_hash}:{article_url}"
        """
        profile_content = f"{sorted(profile_keywords)}:{relevance_threshold}:{boost_factor}"
        profile_hash = hashlib.sha256(profile_content.encode()).hexdigest()[:16]
        return f"relevance:{profile_hash}:{article.url}"
