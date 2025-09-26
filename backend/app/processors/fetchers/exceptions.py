class FetcherError(Exception):
    """Base exception for all fetcher-related errors."""

    pass


class InvalidUrlError(FetcherError):
    """Raised when a URL is invalid or inaccessible."""

    pass


class FetchTimeoutError(FetcherError):
    """Raised when a fetch operation times out."""

    pass


class ParseError(FetcherError):
    """Raised when content cannot be parsed."""

    pass


class RateLimitError(FetcherError):
    """Raised when rate limiting is triggered."""

    pass


class ValidationError(FetcherError):
    """Raised when source validation fails."""

    pass
