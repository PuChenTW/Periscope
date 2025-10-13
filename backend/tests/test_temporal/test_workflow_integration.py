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

from app.temporal.activities.processing import BatchRelevanceRequest, BatchRelevanceResult
from app.temporal.workflows import DailyDigestWorkflow, DigestWorkflowInput


@activity.defn(name="score_relevance_batch")
async def score_relevance_batch_mock(request: BatchRelevanceRequest) -> BatchRelevanceResult:
    return BatchRelevanceResult(
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


@pytest.mark.asyncio
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
        scheduled_time=datetime.now(UTC),
        source_urls=["https://example.com/feed.xml"],
        interest_keywords=["technology", "AI", "Python"],
    )

    async with (
        await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter) as env,
        Worker(env.client, task_queue="tq1", workflows=[DailyDigestWorkflow], activities=[score_relevance_batch_mock]),
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
