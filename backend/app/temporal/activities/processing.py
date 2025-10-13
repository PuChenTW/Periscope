"""
Content processing activities for Temporal workflows.

This module contains Temporal activities that wrap processor logic for
orchestrated execution within workflows. Activities are idempotent and
support retry logic defined in shared.py.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field
from temporalio import activity

from app.processors.fetchers.base import Article
from app.processors.relevance_scorer import RelevanceResult


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


@activity.defn(name="score_relevance_batch")
async def score_relevance_batch(request: BatchRelevanceRequest) -> BatchRelevanceResult:
    """
    Score relevance for a batch of articles against user interest profile.

    This activity wraps RelevanceScorer to provide idempotent batch processing
    with cache-based deduplication. The cache key pattern (profile_id + article_url)
    ensures that re-running this activity with the same inputs returns cached results.

    Idempotency Contract:
    - Cache key: f"relevance:{profile.id}:{article.url}"
    - Cache TTL: personalization.cache_ttl_minutes (default 720 min)
    - Behavior: Cached results are returned immediately, skipping AI scoring

    Args:
        request: BatchRelevanceRequest containing profile ID and articles

    Returns:
        BatchRelevanceResult containing articles and their relevance scores

    Raises:
        RuntimeError: If RelevanceScorer initialization fails
        ValueError: If profile or articles are invalid

    Activity Options:
        - Timeout: MEDIUM_TIMEOUT (30s)
        - Retry: MEDIUM_RETRY_POLICY (3 attempts, 5s-45s backoff)
        - Idempotent: Yes (via cache key check)
    """
    # Phase 2: Activity implementation pending
    # Return stub result for now to allow workflow execution
    start_timestamp = datetime.now(UTC)
    end_timestamp = datetime.now(UTC)

    return BatchRelevanceResult(
        articles=request.articles,
        relevance_results={},
        profile_id=request.profile_id,
        total_scored=0,
        cache_hits=0,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        ai_calls=0,
        errors_count=0,
    )
