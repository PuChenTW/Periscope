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
from app.processors.relevance_scorer import RelevanceResult, RelevanceScorer
from app.repositories import ProfileRepository
from app.utils.redis_client import get_redis_client


class BatchRelevanceResult(BaseModel):
    """
    Result object for batch relevance scoring activity.

    Contains original articles and their computed relevance results,
    preserving immutability and enabling clear data flow in workflows.
    Includes observability metrics for monitoring and debugging.
    """

    articles: list[Article] = Field(description="Original articles (unchanged)")
    relevance_results: dict[str, RelevanceResult] = Field(description="Relevance results keyed by article.url")
    profile_id: str = Field(description="Interest profile ID used for scoring")
    total_scored: int = Field(description="Total articles scored")
    cache_hits: int = Field(description="Number of results served from cache")

    # Observability fields
    start_timestamp: datetime = Field(description="When activity started (UTC)")
    end_timestamp: datetime = Field(description="When activity completed (UTC)")
    ai_calls: int = Field(default=0, description="Number of AI calls made (excluding cache hits)")
    errors_count: int = Field(default=0, description="Number of errors encountered (with fallbacks applied)")


class BatchRelevanceRequest(BaseModel):
    """
    Request object for batch relevance scoring activity.

    Encapsulates all inputs required to perform relevance scoring
    for a batch of articles against a user interest profile.
    """

    profile_id: str = Field(description="Interest profile ID to score against")
    articles: list[Article] = Field(description="List of articles to score")
    quality_scores: dict[str, int] | None = Field(
        default=None,
        description="Optional quality scores keyed by article.url (from QualityScorer activity)",
    )


def compute_relevance_cache_key(
    article: Article, profile_keywords: list[str], relevance_threshold: int, boost_factor: float
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


@activity.defn(name="score_relevance_batch")
async def score_relevance_batch(request: BatchRelevanceRequest) -> BatchRelevanceResult:
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

    # Initialize dependencies
    settings = get_settings()
    redis_client = get_redis_client()
    async_session_maker = get_async_sessionmaker()

    # Fetch profile from database
    async with async_session_maker() as session:
        profile_repo = ProfileRepository(session)
        profile = await profile_repo.get_by_id(request.profile_id)

    if profile is None:
        raise ValidationError(f"Interest profile not found: {request.profile_id}")

    # Initialize RelevanceScorer
    ai_provider = create_ai_provider(settings)
    scorer = RelevanceScorer(
        settings=settings.personalization,
        ai_provider=ai_provider,
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
            cache_key = compute_relevance_cache_key(
                article,
                profile.keywords,
                profile.relevance_threshold,
                profile.boost_factor,
            )

            # Check cache for idempotency
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                # Cache hit: deserialize and use cached result
                result = RelevanceResult.model_validate_json(cached_result)
                relevance_results[str(article.url)] = result
                cache_hits += 1
                logger.debug(f"Cache hit for article: {article.url}")
                continue

            # Cache miss: score article
            quality_score = request.quality_scores.get(str(article.url)) if request.quality_scores else None

            result = await scorer.score_article(article, profile, quality_score)

            # Count AI call if semantic scoring was enabled and score changed
            # (RelevanceScorer logs when AI runs, we infer from score > keyword_score)
            if settings.personalization.enable_semantic_scoring and result.breakdown.semantic_score > 0:
                ai_calls += 1

            # Cache result
            cache_ttl_seconds = settings.personalization.cache_ttl_minutes * 60
            await redis_client.setex(cache_key, cache_ttl_seconds, result.model_dump_json())

            relevance_results[str(article.url)] = result
            logger.debug(f"Scored article: {article.url} (score={result.relevance_score})")

        except Exception as e:
            # Log error and continue with remaining articles
            errors_count += 1
            logger.error(f"Failed to score article {article.url}: {e}")
            # Don't add to results - partial results only include successful scores

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
