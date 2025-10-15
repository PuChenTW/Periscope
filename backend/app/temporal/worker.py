"""
Temporal worker entry point.

This module provides the worker process that executes Temporal workflows
and activities. Run as a separate process from the FastAPI application.

Usage:
    uv run python -m app.temporal.worker
"""

import asyncio
import signal
from typing import Any

from loguru import logger
from temporalio.worker import Worker

from app.config import get_settings
from app.temporal.activities.processing import score_relevance_batch
from app.temporal.client import get_temporal_client
from app.temporal.workflows import DailyDigestWorkflow


async def create_worker() -> Worker:
    """
    Create and configure Temporal worker with registered workflows and activities.

    Returns:
        Configured Worker instance ready to run

    Raises:
        RuntimeError: If worker creation fails
    """
    settings = get_settings()
    client = await get_temporal_client()

    try:
        worker = Worker(
            client,
            task_queue=settings.temporal.task_queue,
            workflows=[DailyDigestWorkflow],
            activities=[score_relevance_batch],
        )

        logger.info(f"Worker configured for task queue: {settings.temporal.task_queue}")
        return worker

    except Exception as e:
        error_msg = f"Failed to create Temporal worker: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def run_worker() -> None:
    """
    Run Temporal worker until shutdown signal received.

    Handles graceful shutdown on SIGTERM/SIGINT.
    """
    logger.info("Starting Temporal worker...")

    # Setup graceful shutdown before creating worker
    shutdown_event = asyncio.Event()

    def signal_handler(signum: int, frame: Any) -> None:  # noqa: ARG001
        logger.info(f"Shutdown signal {signum} received, stopping worker...")
        shutdown_event.set()

    # Register signal handlers before worker creation
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create worker after signal handlers are registered
    worker = await create_worker()

    try:
        # Run worker until shutdown
        logger.info("Worker started successfully, processing tasks...")
        async with worker:
            await shutdown_event.wait()

    except Exception as e:
        logger.error(f"Worker encountered error: {e}")
        raise

    finally:
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(run_worker())
