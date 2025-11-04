"""
Temporal workflow definitions for daily digest generation.

This module contains the main workflow orchestration logic for generating
personalized daily reading digests.
"""

from datetime import datetime, timedelta

from pydantic import BaseModel
from temporalio import workflow

from app.processors.fetchers.base import Article

with workflow.unsafe.imports_passed_through():
    import app.temporal.activities.schemas as sc
    from app.temporal import shared


class DigestWorkflowInput(BaseModel):
    """
    Input parameters for daily digest workflow.

    Attributes:
        user_id: Unique identifier for the user
        source_urls: List of RSS/blog URLs to fetch content from
        interest_keywords: User's interest keywords for relevance scoring
    """

    user_id: str
    source_urls: list[str]
    interest_keywords: list[str]


class DigestWorkflowResult(BaseModel):
    """
    Result of daily digest workflow execution.

    Attributes:
        user_id: User identifier
        workflow_id: Temporal workflow ID
        articles_fetched: Total articles fetched from all sources
        articles_processed: Articles that passed validation and processing
        articles_relevant: Articles that passed relevance threshold
        digest_sent: Whether email was successfully sent
        start_timestamp: When workflow started (UTC)
        end_timestamp: When workflow completed (UTC)
        total_ai_calls: Total AI API calls made across all activities
        total_errors: Total errors encountered (with fallbacks applied)
        error_messages: List of error descriptions
    """

    user_id: str
    workflow_id: str
    articles_fetched: int
    articles_processed: int
    articles_relevant: int
    digest_sent: bool
    start_timestamp: datetime
    end_timestamp: datetime
    total_ai_calls: int
    total_errors: int
    error_messages: list[str]


@workflow.defn(name="daily_digest")
class DailyDigestWorkflow:
    """
    Orchestrates daily digest generation pipeline.

    Workflow phases:
    1. Fetch content from all sources (parallel)
    2. Validate and filter articles (basic validation, AI spam detection)
    3. Normalize articles (URL normalization, metadata cleanup)
    4. Score content quality (optional AI-powered quality assessment)
    5. Extract topics (AI-powered topic extraction)
    6. Score relevance to user interests
    7. Summarize articles (AI-powered summarization)
    8. Detect similar articles and group them
    9. Assemble personalized digest email
    10. Send email with retry logic
    11. Record delivery status

    Each phase uses Temporal activities with appropriate timeout/retry policies.
    """

    @workflow.run
    async def run(self, digest: DigestWorkflowInput) -> DigestWorkflowResult:
        """
        Execute daily digest workflow.

        Args:
            digest: Workflow input parameters

        Returns:
            DigestWorkflowResult with execution metrics and status
        """
        # Initialize tracking
        start_timestamp = workflow.now()
        total_ai_calls = 0
        total_errors = 0
        error_messages: list[str] = []

        # TODO: Phase 1 - Fetch content from sources (parallel)
        # Activity: fetch_sources_parallel (not yet implemented)
        # Input: input.source_urls
        # Output: list[Article] (raw articles from all sources)
        # For now, use empty list until fetching is implemented
        raw_articles: list[Article] = []
        articles_fetched = len(raw_articles)

        # Phase 2: Validate and filter articles
        validation_result = await workflow.execute_activity(
            "validate_and_filter_batch",
            sc.BatchValidationRequest(articles=raw_articles),
            start_to_close_timeout=timedelta(seconds=shared.MEDIUM_TIMEOUT),
            retry_policy=shared.MEDIUM_RETRY_POLICY,
        )
        validation_result = sc.BatchValidationResult.model_validate(validation_result)
        total_ai_calls += validation_result.ai_calls
        total_errors += validation_result.errors_count
        validated_articles = validation_result.articles

        # Phase 3: Normalize articles
        norm_result = await workflow.execute_activity(
            "normalize_articles_batch",
            sc.BatchNormalizationRequest(articles=validated_articles),
            start_to_close_timeout=timedelta(seconds=shared.MEDIUM_TIMEOUT),
            retry_policy=shared.MEDIUM_RETRY_POLICY,
        )
        norm_result = sc.BatchNormalizationResult.model_validate(norm_result)
        total_ai_calls += norm_result.ai_calls
        total_errors += norm_result.errors_count
        normalized_articles = norm_result.articles

        # Phase 4: Score content quality
        quality_result = await workflow.execute_activity(
            "score_quality_batch",
            sc.BatchQualityRequest(articles=normalized_articles),
            start_to_close_timeout=timedelta(seconds=shared.LONG_TIMEOUT),
            retry_policy=shared.LONG_RETRY_POLICY,
        )
        quality_result = sc.BatchQualityResult.model_validate(quality_result)
        total_ai_calls += quality_result.ai_calls
        total_errors += quality_result.errors_count
        quality_scored_articles = quality_result.articles

        # Phase 5: Extract topics
        topics_result = await workflow.execute_activity(
            "extract_topics_batch",
            sc.BatchTopicExtractionRequest(articles=quality_scored_articles),
            start_to_close_timeout=timedelta(seconds=shared.LONG_TIMEOUT),
            retry_policy=shared.LONG_RETRY_POLICY,
        )
        topics_result = sc.BatchTopicExtractionResult.model_validate(topics_result)
        total_ai_calls += topics_result.ai_calls
        total_errors += topics_result.errors_count
        topic_extracted_articles = topics_result.articles

        # Phase 6: Score relevance to user interests
        # TODO: Get profile_id from digest input once user system is integrated
        # For now, skip relevance scoring if no raw articles
        articles_relevant = 0

        if topic_extracted_articles:
            relevance_result = await workflow.execute_activity(
                "score_relevance_batch",
                sc.BatchRelevanceRequest(
                    profile_id="placeholder_profile_id",  # TODO: Get from digest.profile_id
                    articles=topic_extracted_articles,
                    quality_scores={
                        str(url): result.quality_score for url, result in quality_result.quality_results.items()
                    },
                ),
                start_to_close_timeout=timedelta(seconds=shared.MEDIUM_TIMEOUT),
                retry_policy=shared.MEDIUM_RETRY_POLICY,
            )
            relevance_result = sc.BatchRelevanceResult.model_validate(relevance_result)
            total_ai_calls += relevance_result.ai_calls
            total_errors += relevance_result.errors_count
            articles_relevant = relevance_result.total_scored
            # TODO: Phase 7 will use relevance_result.articles for summarization

        # TODO: Phase 7 - Summarize articles
        # Activity: summarize_articles_batch
        # Input: relevance_result.articles
        # Output: list[Article] (with summary metadata)
        # Timeout: LONG_TIMEOUT (120s, AI summarization)
        # Retry: LONG_RETRY_POLICY (2 attempts, 15s-120s backoff)
        # Error handling: Fallback to excerpt on AI failure
        # Observability: Track AI calls, cache hits, summary length distribution
        # summarized_articles: list[Article] = []

        # TODO: Phase 8 - Detect similar articles
        # Activity: detect_similar_articles
        # Input: summarized_articles
        # Output: list[ArticleGroup] (grouped by similarity)
        # Timeout: LONG_TIMEOUT (120s, AI similarity detection)
        # Retry: LONG_RETRY_POLICY (2 attempts, 15s-120s backoff)
        # Error handling: Skip grouping on failure, use flat list
        # Observability: Track AI calls, group count, articles per group
        # article_groups: list = []  # type: list[ArticleGroup] when implemented

        # TODO: Phase 9 - Assemble digest
        # Activity: assemble_digest
        # Input: article_groups, input.user_id
        # Output: DigestPayload (HTML email body + metadata)
        # Timeout: FAST_TIMEOUT (5s, template rendering)
        # Retry: FAST_RETRY_POLICY (3 attempts, 2s-10s backoff)
        # Error handling: NonRetryableError (abort workflow if template fails)
        # Observability: Track template render time, email size
        # digest_payload = None  # type: DigestPayload when implemented

        # TODO: Phase 10 - Send email
        # Activity: send_email
        # Input: digest_payload, input.user_id
        # Output: bool (sent successfully)
        # Timeout: MEDIUM_TIMEOUT (30s, SMTP/API call)
        # Retry: EMAIL_RETRY_POLICY (4 attempts, 10s-2m backoff)
        # Error handling: Retry transient failures, fail on auth errors
        # Observability: Track delivery time, SMTP response codes
        digest_sent = False

        # TODO: Phase 11 - Record delivery status
        # Activity: record_delivery_status
        # Input: input.user_id, digest_sent, error_messages
        # Output: None
        # Timeout: FAST_TIMEOUT (5s, database write)
        # Retry: FAST_RETRY_POLICY (3 attempts, 2s-10s backoff)
        # Error handling: Log failure, do not fail workflow
        # Observability: Track delivery log write latency

        # Calculate final metrics
        end_timestamp = workflow.now()
        articles_processed = len(normalized_articles)

        return DigestWorkflowResult(
            user_id=digest.user_id,
            workflow_id=workflow.info().workflow_id,
            articles_fetched=articles_fetched,
            articles_processed=articles_processed,
            articles_relevant=articles_relevant,
            digest_sent=digest_sent,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            total_ai_calls=total_ai_calls,
            total_errors=total_errors,
            error_messages=error_messages,
        )
