"""
Tests for HTTPClient utility
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientError, ClientResponse, ClientResponseError, ClientSession

from app.processors.utils.http_client import HTTPClient


class TestHTTPClient:
    """Test HTTPClient functionality."""

    @pytest.fixture
    def http_client(self):
        """Create HTTPClient instance for testing."""
        return HTTPClient(timeout=10, max_retries=2, retry_delay=0.1)

    @pytest.fixture
    def mock_session(self, monkeypatch):
        """Mock aiohttp.ClientSession."""
        mock_session = AsyncMock(spec=ClientSession)
        mock_session.closed = False

        # Mock session creation
        def mock_session_init(*args, **kwargs):
            return mock_session

        monkeypatch.setattr("aiohttp.ClientSession", mock_session_init)
        return mock_session

    @pytest.mark.asyncio
    async def test_context_manager(self, http_client, mock_session):
        """Test HTTPClient as async context manager."""
        async with http_client as client:
            assert client is http_client

        # Verify session was closed
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_text_success(self, http_client, mock_session):
        """Test successful text fetch."""
        # Setup mock response
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text.return_value = "Test content"
        mock_response.raise_for_status = Mock()

        mock_session.get.return_value.__aenter__.return_value = mock_response

        async with http_client:
            result = await http_client.fetch_text("https://example.com")

        assert result == "Test content"
        mock_response.text.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_bytes_success(self, http_client, mock_session):
        """Test successful bytes fetch."""
        test_data = b"Test binary content"

        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.read.return_value = test_data
        mock_response.raise_for_status = Mock()

        mock_session.get.return_value.__aenter__.return_value = mock_response

        async with http_client:
            result = await http_client.fetch_bytes("https://example.com")

        assert result == test_data
        mock_response.read.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiting(self, http_client, mock_session):
        """Test rate limiting handling."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = HTTPStatus.TOO_MANY_REQUESTS
        mock_response.headers = {"Retry-After": "1"}

        # Mock raise_for_status to raise ClientResponseError for 429
        rate_limit_error = ClientResponseError(
            request_info=Mock(), history=(), status=HTTPStatus.TOO_MANY_REQUESTS, headers={"Retry-After": "1"}
        )
        mock_response.raise_for_status.side_effect = rate_limit_error

        mock_session.get.return_value.__aenter__.return_value = mock_response

        async with http_client:
            with pytest.raises(ClientResponseError) as exc_info:
                await http_client.fetch_text("https://example.com")

            assert exc_info.value.status == HTTPStatus.TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, http_client, mock_session):
        """Test retry logic on timeout."""
        # First call times out, second succeeds
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text.return_value = "Success after retry"
        mock_response.raise_for_status = Mock()

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Timeout")
            return mock_response

        mock_session.get.return_value.__aenter__ = side_effect

        async with http_client:
            result = await http_client.fetch_text("https://example.com")

        assert result == "Success after retry"
        assert call_count == 2  # One timeout, one success

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, http_client, mock_session):
        """Test behavior when all retries are exhausted."""

        # Always timeout
        async def timeout_side_effect(*args, **kwargs):
            raise TimeoutError("Always timeout")

        mock_session.get.return_value.__aenter__ = timeout_side_effect

        async with http_client:
            with pytest.raises(TimeoutError):
                await http_client.fetch_text("https://example.com")

    @pytest.mark.asyncio
    async def test_client_error_retry(self, http_client, mock_session):
        """Test retry on client errors."""
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ClientError("Connection error")

            mock_response = AsyncMock(spec=ClientResponse)
            mock_response.status = 200
            mock_response.headers = {}
            mock_response.text.return_value = "Success"
            mock_response.raise_for_status = Mock()
            return mock_response

        mock_session.get.return_value.__aenter__ = side_effect

        async with http_client:
            result = await http_client.fetch_text("https://example.com")

        assert result == "Success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_http_error_no_retry(self, http_client, mock_session):
        """Test that HTTP errors don't trigger retries."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 404
        mock_response.headers = {}
        mock_response.raise_for_status.side_effect = ClientError("404 Not Found")

        mock_session.get.return_value.__aenter__.return_value = mock_response

        async with http_client:
            with pytest.raises(Exception) as exc_info:
                await http_client.fetch_text("https://example.com")

            # Should fail immediately without retries
            assert "404 Not Found" in str(exc_info.value) or "Failed to fetch" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_custom_headers(self, http_client, mock_session):
        """Test custom headers are passed through."""
        mock_response = AsyncMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text.return_value = "Content"
        mock_response.raise_for_status = Mock()

        mock_session.get.return_value.__aenter__.return_value = mock_response

        custom_headers = {"Authorization": "Bearer token", "Custom-Header": "value"}

        async with http_client:
            await http_client.fetch_text("https://example.com", headers=custom_headers)

        # Verify session.get was called with custom headers
        mock_session.get.assert_called_with("https://example.com", headers=custom_headers)

    def test_initialization(self):
        """Test HTTPClient initialization with custom parameters."""
        client = HTTPClient(timeout=60, max_retries=5, retry_delay=2.0, user_agent="Custom Agent")

        assert client.timeout == 60
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        assert client.user_agent == "Custom Agent"
