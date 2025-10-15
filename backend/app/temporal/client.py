"""
Temporal client utilities and factory functions.

This module provides helpers for creating and managing Temporal clients,
starting workflows, and querying workflow status.

The client uses a singleton pattern with async lock to avoid connection exhaustion.

NOTE: The Temporal Python SDK client does not require an explicit close() method call.
The client connection is backed by a Rust core and handles its own cleanup when it is no longer referenced.
"""

import asyncio
from typing import Any

from loguru import logger
from temporalio.client import Client, WorkflowHandle
from temporalio.contrib.pydantic import pydantic_data_converter

from app.config import get_settings

# Module-level singleton for Temporal client with lock for thread safety
_temporal_client: Client | None = None
_temporal_client_lock = asyncio.Lock()


async def get_temporal_client() -> Client:
    """
    Get or create singleton Temporal client instance.

    Uses module-level singleton with async lock to prevent race conditions
    when multiple coroutines try to create the client simultaneously.

    Returns:
        Connected Temporal client

    Raises:
        RuntimeError: If connection to Temporal server fails
    """
    global _temporal_client  # noqa: PLW0603

    # Fast path: return existing client without acquiring lock
    if _temporal_client is not None:
        return _temporal_client

    # Slow path: acquire lock and create client
    async with _temporal_client_lock:
        # Double-check after acquiring lock (another coroutine may have created it)
        if _temporal_client is not None:
            return _temporal_client

        settings = get_settings()
        temporal_config = settings.temporal

        try:
            _temporal_client = await Client.connect(
                temporal_config.server_url,
                namespace=temporal_config.namespace,
                identity=temporal_config.client_identity,
                data_converter=pydantic_data_converter,
            )
            logger.info(
                f"Connected to Temporal server at {temporal_config.server_url} (namespace: {temporal_config.namespace})"
            )

            return _temporal_client

        except Exception as e:
            error_msg = f"Failed to connect to Temporal server at {temporal_config.server_url}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


async def start_workflow(
    client: Client,
    workflow_type: str,
    workflow_id: str,
    workflow_args: list[Any],
    task_queue: str | None = None,
) -> WorkflowHandle:
    """
    Start a Temporal workflow.

    Args:
        client: Temporal client instance
        workflow_type: Workflow type name
        workflow_id: Unique workflow ID
        workflow_args: List of arguments to pass to workflow
        task_queue: Task queue name (uses settings default if not provided)

    Returns:
        WorkflowHandle for the started workflow

    Raises:
        RuntimeError: If workflow start fails
    """
    if task_queue is None:
        task_queue = get_settings().temporal.task_queue

    try:
        handle = await client.start_workflow(
            workflow_type,
            *workflow_args,
            id=workflow_id,
            task_queue=task_queue,
        )
        logger.info(f"Started workflow '{workflow_type}' with ID: {workflow_id}")
        return handle

    except Exception as e:
        error_msg = f"Failed to start workflow '{workflow_type}' (ID: {workflow_id}): {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def get_workflow_handle(
    client: Client,
    workflow_id: str,
    run_id: str | None = None,
) -> WorkflowHandle:
    """
    Get a handle to an existing workflow.

    Args:
        client: Temporal client instance
        workflow_id: Workflow ID
        run_id: Optional run ID for specific execution

    Returns:
        WorkflowHandle for the workflow
    """
    return client.get_workflow_handle(workflow_id, run_id=run_id)


async def query_workflow_status(
    client: Client,
    workflow_id: str,
) -> dict[str, Any]:
    """
    Query workflow status and metadata.

    Args:
        client: Temporal client instance
        workflow_id: Workflow ID to query

    Returns:
        Dictionary with workflow status information

    Raises:
        RuntimeError: If workflow query fails
    """
    try:
        handle = await get_workflow_handle(client, workflow_id)
        description = await handle.describe()

        return {
            "workflow_id": workflow_id,
            "run_id": description.run_id,
            "status": description.status.name,
            "start_time": description.start_time,
            "execution_time": description.execution_time,
            "close_time": description.close_time,
        }

    except Exception as e:
        error_msg = f"Failed to query workflow status for ID '{workflow_id}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def cancel_workflow(
    client: Client,
    workflow_id: str,
) -> None:
    """
    Cancel a running workflow.

    Args:
        client: Temporal client instance
        workflow_id: Workflow ID to cancel

    Raises:
        RuntimeError: If workflow cancellation fails
    """
    try:
        handle = await get_workflow_handle(client, workflow_id)
        await handle.cancel()
        logger.info(f"Cancelled workflow: {workflow_id}")

    except Exception as e:
        error_msg = f"Failed to cancel workflow '{workflow_id}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


if __name__ == "__main__":
    import asyncio
    from uuid import uuid4

    from app.temporal.workflows import DigestWorkflowInput

    async def main():
        client = await get_temporal_client()
        workflow_id = uuid4().hex
        handle = await start_workflow(
            client,
            workflow_type="daily_digest",
            workflow_id=workflow_id,
            workflow_args=[DigestWorkflowInput(user_id="user_1", source_urls=[], interest_keywords=[])],
        )
        print(f"Started workflow with ID: {handle.id}, Run ID: {handle.run_id}")

        status = await query_workflow_status(client, workflow_id)
        print(f"Workflow status: {status}")

    asyncio.run(main())
