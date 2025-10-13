"""
Domain exception hierarchy for Temporal workflow error handling.

This module defines the base exception classes used throughout the application,
with clear semantics for Temporal retry behavior:
- RetryableError: Transient failures that should trigger retry with backoff
- NonRetryableError: Permanent failures that should fail fast without retry
"""


class RetryableError(Exception):
    """
    Base for transient errors that should trigger Temporal retry.

    Use for:
    - External service timeouts (AI providers, HTTP requests)
    - Rate limiting (429 responses)
    - Temporary network failures
    - Database connection pool exhaustion
    """

    pass


class NonRetryableError(Exception):
    """
    Base for permanent errors that should fail fast without retry.

    Use for:
    - Input validation failures
    - Authentication/authorization errors
    - Data integrity violations
    - Misconfiguration errors
    """

    pass


class ValidationError(NonRetryableError):
    """
    Input validation or configuration error.

    Raised when user input, profile data, or system configuration is invalid.
    These errors cannot be resolved by retry and should abort immediately.
    """

    pass


class ExternalServiceError(RetryableError):
    """
    External service temporarily unavailable.

    Raised when AI providers, email services, or RSS feeds fail with transient
    errors (timeouts, 5xx responses). Safe to retry with exponential backoff.
    """

    pass


class ConfigurationError(NonRetryableError):
    """
    System misconfiguration detected.

    Raised when required settings are missing or invalid. These errors indicate
    deployment issues and cannot be resolved by retry.
    """

    pass
