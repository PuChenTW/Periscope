import asyncio
from http import HTTPStatus

import aiohttp
from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout
from loguru import logger


class HTTPClient:
    """HTTP client with retry logic and rate limiting."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        user_agent: str = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        ),
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        self._session: ClientSession | None = None

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        _ = exc_type, exc_val, exc_tb  # Unused parameters
        await self.close()

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=self.timeout)
            headers = {"User-Agent": self.user_agent}
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _make_request(self, url: str, headers: dict[str, str] | None = None):
        """Make a single HTTP request."""
        async with self._session.get(url, headers=headers) as response:
            response.raise_for_status()
            return response

    async def _fetch_with_retry(self, url: str, headers: dict[str, str] | None = None, response_processor=None):
        """Fetch with retry logic."""
        await self._ensure_session()
        assert self._session is not None

        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._make_request(url, headers)
                return await response_processor(response)

            except (ClientResponseError, TimeoutError, ClientError) as e:
                last_exception = e
                # Handle rate limiting with proper delay
                if isinstance(e, ClientResponseError) and e.status == HTTPStatus.TOO_MANY_REQUESTS:
                    retry_after = e.headers.get("Retry-After")
                    if retry_after:
                        await asyncio.sleep(float(retry_after))
                logger.warning(f"Retryable error on attempt {attempt + 1} for {url}: {e}")

            except Exception as e:
                last_exception = e
                logger.error(f"Non-retryable error on attempt {attempt + 1} for {url}: {e}")
                break  # Don't retry non-retryable errors

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)

        # Re-raise the original exception - no conversion needed
        if last_exception:
            raise last_exception
        raise Exception(f"Failed to fetch {url} after {self.max_retries} attempts")

    async def fetch_text(self, url: str, headers: dict[str, str] | None = None) -> str:
        """Fetch URL content as text."""
        return await self._fetch_with_retry(url, headers, lambda r: r.text())

    async def fetch_bytes(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        """Fetch URL content as bytes."""
        return await self._fetch_with_retry(url, headers, lambda r: r.read())
