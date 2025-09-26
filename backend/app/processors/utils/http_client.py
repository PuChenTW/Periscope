import asyncio

import aiohttp
from aiohttp import ClientError, ClientSession, ClientTimeout
from loguru import logger

from app.processors.fetchers.exceptions import FetchTimeoutError, RateLimitError


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

    async def fetch_text(self, url: str, headers: dict[str, str] | None = None) -> str:
        """Fetch URL content as text."""
        await self._ensure_session()
        assert self._session is not None

        last_exception: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                async with self._session.get(url, headers=headers) as response:
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            await asyncio.sleep(float(retry_after))
                        raise RateLimitError(f"Rate limited for URL: {url}")

                    response.raise_for_status()
                    return await response.text()

            except TimeoutError:
                last_exception = FetchTimeoutError(f"Timeout fetching {url}")
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")

            except ClientError as e:
                last_exception = e
                logger.warning(f"Client error on attempt {attempt + 1} for {url}: {e}")

            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1} for {url}: {e}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2**attempt))

        if isinstance(last_exception, (FetchTimeoutError, RateLimitError)):
            raise last_exception
        raise Exception(f"Failed to fetch {url} after {self.max_retries} attempts: {last_exception}")

    async def fetch_bytes(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        """Fetch URL content as bytes."""
        await self._ensure_session()
        assert self._session is not None

        last_exception: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                async with self._session.get(url, headers=headers) as response:
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            await asyncio.sleep(float(retry_after))
                        raise RateLimitError(f"Rate limited for URL: {url}")

                    response.raise_for_status()
                    return await response.read()

            except TimeoutError:
                last_exception = FetchTimeoutError(f"Timeout fetching {url}")
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")

            except ClientError as e:
                last_exception = e
                logger.warning(f"Client error on attempt {attempt + 1} for {url}: {e}")

            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1} for {url}: {e}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2**attempt))

        if isinstance(last_exception, FetchTimeoutError):
            raise last_exception
        raise Exception(f"Failed to fetch {url} after {self.max_retries} attempts: {last_exception}")
