"""
Shared Temporal activity utilities and option presets.

This module provides reusable ActivityOptions configurations, logging hooks,
and common utilities for Temporal activities.
"""

import textwrap
from datetime import timedelta

from loguru import logger
from temporalio.common import RetryPolicy

from app.exceptions import ConfigurationError, NonRetryableError, ValidationError

# Timeout constants (in seconds) - aligned with temporal-workflows.md
FAST_TIMEOUT = 5
MEDIUM_TIMEOUT = 30
LONG_TIMEOUT = 120

# Non-retryable error types (fully-qualified module paths)
# These exceptions abort workflow execution immediately without retry
NON_RETRYABLE_ERROR_TYPES = [
    NonRetryableError,
    ValidationError,
    ConfigurationError,
]

# Retry policies with exponential backoff (jitter disabled for determinism)
FAST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=3,
    backoff_coefficient=2.0,
    non_retryable_error_types=NON_RETRYABLE_ERROR_TYPES,
)

MEDIUM_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(seconds=45),
    maximum_attempts=3,
    backoff_coefficient=2.0,
    non_retryable_error_types=NON_RETRYABLE_ERROR_TYPES,
)

LONG_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=15),
    maximum_interval=timedelta(seconds=120),
    maximum_attempts=2,
    backoff_coefficient=2.0,
    non_retryable_error_types=NON_RETRYABLE_ERROR_TYPES,
)

EMAIL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=10),
    maximum_interval=timedelta(minutes=2),
    maximum_attempts=4,
    backoff_coefficient=2.0,
    non_retryable_error_types=NON_RETRYABLE_ERROR_TYPES,
)


def log_activity_start(activity_name: str, workflow_id: str, **kwargs) -> None:
    """
    Log activity start with correlation ID.

    Args:
        activity_name: Name of the activity
        workflow_id: Workflow ID for correlation
        **kwargs: Additional context to log
    """
    context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"[{workflow_id}/{activity_name}] Starting activity ({context_str})")


def log_activity_end(activity_name: str, workflow_id: str, success: bool = True, **kwargs) -> None:
    """
    Log activity completion with correlation ID.

    Args:
        activity_name: Name of the activity
        workflow_id: Workflow ID for correlation
        success: Whether activity completed successfully
        **kwargs: Additional context to log
    """
    status = "completed" if success else "failed"
    context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    log_fn = logger.info if success else logger.error
    log_fn(f"[{workflow_id}/{activity_name}] Activity {status} ({context_str})")


def format_activity_error(error: Exception, activity_name: str) -> str:
    """
    Format activity error message consistently.

    Args:
        error: Exception that occurred
        activity_name: Name of the activity where error occurred

    Returns:
        Formatted error message
    """
    return textwrap.dedent(f"""\
        Activity '{activity_name}' failed with error:
        {type(error).__name__}: {error!s}
    """).strip()
