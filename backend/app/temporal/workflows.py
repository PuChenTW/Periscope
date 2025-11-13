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
    from loguru import logger

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

    def _process_activity_result(
        self, result: dict, result_class: type, ai_calls: int, errors: int
    ) -> tuple[BaseModel, int, int]:
        """
        Validate activity result and update cumulative metrics.

        Args:
            result: Raw activity result dict
            result_class: Pydantic model class to validate against
            ai_calls: Current total AI calls
            errors: Current total error count

        Returns:
            Tuple of (validated_result, updated_ai_calls, updated_errors)
        """
        validated = result_class.model_validate(result)
        return validated, ai_calls + validated.ai_calls, errors + validated.errors_count

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

        # Phase 1: Fetch user configuration
        config_result = await workflow.execute_activity(
            "fetch_user_config",
            sc.FetchUserConfigRequest(user_id=digest.user_id),
            start_to_close_timeout=timedelta(seconds=shared.FAST_TIMEOUT),
            retry_policy=shared.FAST_RETRY_POLICY,
        )
        config_result = sc.FetchUserConfigResult.model_validate(config_result)
        user_config = config_result.user_config
        profile_id = user_config.interest_profile.id
        summary_style = user_config.summary_style

        # Phase 1b: Fetch content from sources (parallel)
        # Activity: fetch_sources_parallel (not yet implemented)
        # Input: user_config.sources
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
        validation_result, total_ai_calls, total_errors = self._process_activity_result(
            validation_result, sc.BatchValidationResult, total_ai_calls, total_errors
        )
        validated_articles = validation_result.articles

        # Phase 3: Normalize articles
        norm_result = await workflow.execute_activity(
            "normalize_articles_batch",
            sc.BatchNormalizationRequest(articles=validated_articles),
            start_to_close_timeout=timedelta(seconds=shared.MEDIUM_TIMEOUT),
            retry_policy=shared.MEDIUM_RETRY_POLICY,
        )
        norm_result, total_ai_calls, total_errors = self._process_activity_result(
            norm_result, sc.BatchNormalizationResult, total_ai_calls, total_errors
        )
        normalized_articles = norm_result.articles

        # Phase 4: Score content quality
        quality_result = await workflow.execute_activity(
            "score_quality_batch",
            sc.BatchQualityRequest(articles=normalized_articles),
            start_to_close_timeout=timedelta(seconds=shared.LONG_TIMEOUT),
            retry_policy=shared.LONG_RETRY_POLICY,
        )
        quality_result, total_ai_calls, total_errors = self._process_activity_result(
            quality_result, sc.BatchQualityResult, total_ai_calls, total_errors
        )
        quality_scored_articles = quality_result.articles

        # Phase 5: Extract topics
        topics_result = await workflow.execute_activity(
            "extract_topics_batch",
            sc.BatchTopicExtractionRequest(articles=quality_scored_articles),
            start_to_close_timeout=timedelta(seconds=shared.LONG_TIMEOUT),
            retry_policy=shared.LONG_RETRY_POLICY,
        )
        topics_result, total_ai_calls, total_errors = self._process_activity_result(
            topics_result, sc.BatchTopicExtractionResult, total_ai_calls, total_errors
        )
        topic_extracted_articles = topics_result.articles

        # Phase 6: Score relevance to user interests
        articles_relevant = 0
        relevance_result = None
        if topic_extracted_articles:
            relevance_result = await workflow.execute_activity(
                "score_relevance_batch",
                sc.BatchRelevanceRequest(
                    profile_id=profile_id,
                    articles=topic_extracted_articles,
                    quality_scores={
                        str(url): result.quality_score for url, result in quality_result.quality_results.items()
                    },
                ),
                start_to_close_timeout=timedelta(seconds=shared.MEDIUM_TIMEOUT),
                retry_policy=shared.MEDIUM_RETRY_POLICY,
            )
            relevance_result, total_ai_calls, total_errors = self._process_activity_result(
                relevance_result, sc.BatchRelevanceResult, total_ai_calls, total_errors
            )
            articles_relevant = relevance_result.total_scored

        # Phase 7: Summarize articles
        summarized_articles = topic_extracted_articles
        if topic_extracted_articles:
            summary_result = await workflow.execute_activity(
                "summarize_articles_batch",
                sc.BatchSummarizationRequest(
                    articles=topic_extracted_articles,
                    summary_style=summary_style,
                ),
                start_to_close_timeout=timedelta(seconds=shared.LONG_TIMEOUT),
                retry_policy=shared.LONG_RETRY_POLICY,
            )
            summary_result, total_ai_calls, total_errors = self._process_activity_result(
                summary_result, sc.BatchSummarizationResult, total_ai_calls, total_errors
            )
            summarized_articles = summary_result.articles

        # Phase 8: Detect similar articles
        article_groups = []
        if summarized_articles:
            similarity_result = await workflow.execute_activity(
                "detect_similar_articles_batch",
                sc.BatchSimilarityRequest(articles=summarized_articles),
                start_to_close_timeout=timedelta(seconds=shared.LONG_TIMEOUT),
                retry_policy=shared.LONG_RETRY_POLICY,
            )
            similarity_result, total_ai_calls, total_errors = self._process_activity_result(
                similarity_result, sc.BatchSimilarityResult, total_ai_calls, total_errors
            )
            article_groups = similarity_result.article_groups

        # Phase 9: Assemble digest
        digest_sent = False
        _digest_payload = None  # Will be used in Phase 10
        if article_groups:
            try:
                relevance_dict = relevance_result.relevance_results if relevance_result else {}
                _digest_payload = await workflow.execute_activity(
                    "assemble_digest",
                    {
                        "user_id": digest.user_id,
                        "user_email": user_config.email,
                        "article_groups": article_groups,
                        "relevance_results": relevance_dict,
                    },
                    start_to_close_timeout=timedelta(seconds=shared.FAST_TIMEOUT),
                    retry_policy=shared.FAST_RETRY_POLICY,
                )
            except Exception as e:
                error_msg = f"Digest assembly failed: {e}"
                error_messages.append(error_msg)
                logger.error(error_msg)

        # Phase 10 - Send email (using mock sender for MVP)
        # Will be implemented with real SMTP/API in future phases
        # TODO: Use _digest_payload once email sending activity is implemented

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
