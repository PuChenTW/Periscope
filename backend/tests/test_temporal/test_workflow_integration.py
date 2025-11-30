"""
Integration tests for Temporal workflows using test server.

These tests validate that workflows and activities can be executed
in an isolated Temporal test environment.
"""

from datetime import UTC, datetime

import pytest
from temporalio import activity
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

import app.temporal.activities.schemas as sc
from app.temporal.workflows import DailyDigestWorkflow, DigestWorkflowInput


@activity.defn(name="validate_and_filter_batch")
async def validate_and_filter_batch_mock(request: sc.BatchValidationRequest) -> sc.BatchValidationResult:
    return sc.BatchValidationResult(
        articles=request.articles,
        validation_results={},
        total_processed=len(request.articles),
        valid_count=len(request.articles),
        invalid_count=0,
        start_timestamp=datetime.now(UTC),
        end_timestamp=datetime.now(UTC),
        ai_calls=0,
        errors_count=0,
    )


@activity.defn(name="normalize_articles_batch")
async def normalize_articles_batch_mock(request: sc.BatchNormalizationRequest) -> sc.BatchNormalizationResult:
    return sc.BatchNormalizationResult(
        articles=request.articles,
        total_processed=len(request.articles),
        rejected_count=0,
        spam_detected_count=0,
        start_timestamp=datetime.now(UTC),
        end_timestamp=datetime.now(UTC),
        ai_calls=0,
        errors_count=0,
    )


@activity.defn(name="score_quality_batch")
async def score_quality_batch_mock(request: sc.BatchQualityRequest) -> sc.BatchQualityResult:
    return sc.BatchQualityResult(
        articles=request.articles,
        quality_results={},
        total_scored=0,
        cache_hits=0,
        start_timestamp=datetime.now(UTC),
        end_timestamp=datetime.now(UTC),
        ai_calls=0,
        errors_count=0,
    )


@activity.defn(name="extract_topics_batch")
async def extract_topics_batch_mock(request: sc.BatchTopicExtractionRequest) -> sc.BatchTopicExtractionResult:
    return sc.BatchTopicExtractionResult(
        articles=request.articles,
        total_processed=len(request.articles),
        articles_with_topics=0,
        cache_hits=0,
        start_timestamp=datetime.now(UTC),
        end_timestamp=datetime.now(UTC),
        ai_calls=0,
        errors_count=0,
    )


@activity.defn(name="score_relevance_batch")
async def score_relevance_batch_mock(request: sc.BatchRelevanceRequest) -> sc.BatchRelevanceResult:
    return sc.BatchRelevanceResult(
        articles=request.articles,
        relevance_results={},
        profile_id=request.profile_id,
        total_scored=0,
        cache_hits=0,
        start_timestamp=datetime.now(UTC),
        end_timestamp=datetime.now(UTC),
        ai_calls=0,
        errors_count=0,
    )


@activity.defn(name="fetch_user_config")
async def fetch_user_config_mock(request: sc.FetchUserConfigRequest) -> sc.FetchUserConfigResult:
    return sc.FetchUserConfigResult(
        user_config=sc.DigestUserConfig(
            user_id=request.user_id,
            email="test@example.com",
            timezone="UTC",
            delivery_time=datetime.now(UTC).time(),
            summary_style="brief",
            is_active=True,
            sources=[
                sc.ContentSourceConfig(
                    id="source_1",
                    source_type="rss",
                    source_url="https://example.com/feed.xml",
                    source_name="Example Feed",
                    is_active=True,
                )
            ],
            interest_profile=sc.InterestProfileConfig(
                id="profile_1",
                keywords=["technology", "AI"],
                relevance_threshold=50,
                boost_factor=1.0,
            ),
        ),
        sources_count=1,
        keywords_count=2,
        start_timestamp=datetime.now(UTC),
        end_timestamp=datetime.now(UTC),
    )


@activity.defn(name="fetch_sources_parallel")
async def fetch_sources_parallel_mock(
    request: sc.FetchSourcesParallelRequest,
) -> sc.FetchSourcesParallelResult:
    """Mock fetch_sources_parallel activity for workflow integration tests."""
    # Return empty articles list for mock
    # In real scenario, this would fetch from sources
    return sc.FetchSourcesParallelResult(
        articles=[],
        total_sources=len(request.sources),
        successful_sources=len([s for s in request.sources if s.is_active]),
        failed_sources=0,
        total_articles=0,
        fetch_errors={},
        start_timestamp=datetime.now(UTC),
        end_timestamp=datetime.now(UTC),
    )


@pytest.mark.asyncio
@pytest.mark.timeout(20)
async def test_workflow_can_be_started():
    """
    Test that workflow stub can be instantiated and started.

    This validates that:
    1. Workflow registration is correct
    2. Input/output types serialize properly
    3. Workflow can be executed (even though activities are stubs)
    """
    workflow_input = DigestWorkflowInput(
        user_id="test_user_123",
        source_urls=["https://example.com/feed.xml"],
        interest_keywords=["technology", "AI", "Python"],
    )

    async with (
        await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter) as env,
        Worker(
            env.client,
            task_queue="tq1",
            workflows=[DailyDigestWorkflow],
            activities=[
                fetch_user_config_mock,
                fetch_sources_parallel_mock,
                validate_and_filter_batch_mock,
                normalize_articles_batch_mock,
                score_quality_batch_mock,
                extract_topics_batch_mock,
                score_relevance_batch_mock,
            ],
        ),
    ):
        result = await env.client.execute_workflow(DailyDigestWorkflow.run, workflow_input, id="wf1", task_queue="tq1")

        # Verify result structure
        assert result.user_id == "test_user_123"
        assert result.workflow_id is not None
        assert result.articles_fetched == 0  # Stubs return empty lists
        assert result.articles_processed == 0
        assert result.articles_relevant == 0
        assert result.digest_sent is False
        assert result.start_timestamp is not None
        assert result.end_timestamp is not None
        assert result.total_ai_calls == 0
        assert result.total_errors == 0
        assert isinstance(result.error_messages, list)
