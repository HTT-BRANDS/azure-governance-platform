"""Unit tests for app/core/retry.py."""

import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.retry import (
    COST_SYNC_POLICY,
    GRAPH_API_POLICY,
    RetryPolicy,
    is_retryable_error,
    retry_with_backoff,
)


def _get_real_azure_exceptions():
    """Get real Azure exception classes, bypassing any sys.modules mocks.

    Several test files (test_graph_*.py, test_riverside_sync.py) replace
    sys.modules["azure.core.exceptions"] with a MagicMock at module level.
    This pollutes isinstance() checks for the rest of the suite.

    Returns all needed classes from a single fresh import to ensure
    class identity is consistent (e.g. ClientAuthenticationError IS-A
    HttpResponseError).
    """
    key = "azure.core.exceptions"
    current = sys.modules.get(key)

    if current is not None and not isinstance(current, MagicMock):
        # Module is real — use it directly
        return (
            getattr(current, "ClientAuthenticationError"),
            getattr(current, "HttpResponseError"),
        )

    # Module has been mocked — temporarily remove ALL azure entries and re-import
    saved = {}
    for k in list(sys.modules):
        if k.startswith("azure"):
            saved[k] = sys.modules.pop(k)

    try:
        real_mod = importlib.import_module(key)
        result = (
            getattr(real_mod, "ClientAuthenticationError"),
            getattr(real_mod, "HttpResponseError"),
        )
    finally:
        # Clean up the fresh imports
        for k in list(sys.modules):
            if k.startswith("azure") and k not in saved:
                del sys.modules[k]
        # Restore the mocked modules so other tests aren't affected
        sys.modules.update(saved)

    return result


# Get real classes once at module level (handles both clean and polluted states)
_RealClientAuthError, _RealHttpResponseError = _get_real_azure_exceptions()


@pytest.fixture(autouse=True)
def _ensure_real_retry_internals():
    """Ensure app.core.retry uses real Azure classes for isinstance() checks.

    If azure.core.exceptions was mocked before retry.py was imported,
    the NON_RETRYABLE_EXCEPTIONS tuple contains MagicMock objects instead
    of real exception classes. This fixture patches them back using the
    SAME class objects we use to create test instances.
    """
    import app.core.retry as retry_mod
    from sqlalchemy.exc import SQLAlchemyError

    orig_non_retryable = retry_mod.NON_RETRYABLE_EXCEPTIONS
    orig_auth = getattr(retry_mod, "ClientAuthenticationError", None)
    orig_http = getattr(retry_mod, "HttpResponseError", None)

    # Patch real classes into retry module — same objects as our test uses
    retry_mod.ClientAuthenticationError = _RealClientAuthError
    retry_mod.HttpResponseError = _RealHttpResponseError
    retry_mod.NON_RETRYABLE_EXCEPTIONS = (
        _RealClientAuthError,
        ValueError,
        TypeError,
        KeyError,
        SQLAlchemyError,
    )

    yield

    # Restore originals
    retry_mod.NON_RETRYABLE_EXCEPTIONS = orig_non_retryable
    if orig_auth is not None:
        retry_mod.ClientAuthenticationError = orig_auth
    if orig_http is not None:
        retry_mod.HttpResponseError = orig_http


class TestRetryPolicy:
    """Tests for RetryPolicy dataclass."""

    def test_default_values(self):
        """Test that RetryPolicy has correct default values."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.backoff_factor == 1.0
        assert policy.max_wait == 60.0
        assert policy.retryable_exceptions == (Exception,)

    def test_custom_values(self):
        """Test that RetryPolicy accepts custom values."""
        policy = RetryPolicy(
            max_retries=5,
            backoff_factor=2.0,
            max_wait=30.0,
            retryable_exceptions=(ValueError,),
        )
        assert policy.max_retries == 5
        assert policy.backoff_factor == 2.0
        assert policy.max_wait == 30.0
        assert policy.retryable_exceptions == (ValueError,)

    def test_predefined_policies(self):
        """Test that predefined policies have expected values."""
        assert COST_SYNC_POLICY.max_retries == 3
        assert COST_SYNC_POLICY.backoff_factor == 2.0

        assert GRAPH_API_POLICY.max_retries == 3
        assert GRAPH_API_POLICY.max_wait == 30.0


class TestIsRetryableError:
    """Tests for is_retryable_error function."""

    def test_non_retryable_value_error(self):
        """Test that ValueError is not retryable."""
        error = ValueError("Invalid value")
        assert is_retryable_error(error) is False

    def test_non_retryable_type_error(self):
        """Test that TypeError is not retryable."""
        error = TypeError("Invalid type")
        assert is_retryable_error(error) is False

    def test_non_retryable_key_error(self):
        """Test that KeyError is not retryable."""
        error = KeyError("missing_key")
        assert is_retryable_error(error) is False

    def test_non_retryable_auth_error(self):
        """Test that ClientAuthenticationError is not retryable."""
        error = _RealClientAuthError("Auth failed")
        assert is_retryable_error(error) is False

    def test_retryable_timeout_error(self):
        """Test that TimeoutError is retryable."""
        error = TimeoutError("Request timed out")
        assert is_retryable_error(error) is True

    def test_retryable_connection_error(self):
        """Test that ConnectionError is retryable."""
        error = ConnectionError("Connection lost")
        assert is_retryable_error(error) is True

    def test_retryable_http_429(self):
        """Test that HTTP 429 (rate limit) is retryable."""
        error = _RealHttpResponseError("Too many requests")
        error.status_code = 429
        assert is_retryable_error(error) is True

    def test_retryable_http_502(self):
        """Test that HTTP 502 (bad gateway) is retryable."""
        error = _RealHttpResponseError("Bad gateway")
        error.status_code = 502
        assert is_retryable_error(error) is True

    def test_retryable_http_503(self):
        """Test that HTTP 503 (service unavailable) is retryable."""
        error = _RealHttpResponseError("Service unavailable")
        error.status_code = 503
        assert is_retryable_error(error) is True

    def test_retryable_http_504(self):
        """Test that HTTP 504 (gateway timeout) is retryable."""
        error = _RealHttpResponseError("Gateway timeout")
        error.status_code = 504
        assert is_retryable_error(error) is True

    def test_non_retryable_http_400(self):
        """Test that HTTP 400 (bad request) is not retryable."""
        error = _RealHttpResponseError("Bad request")
        error.status_code = 400
        assert is_retryable_error(error) is False

    def test_non_retryable_http_404(self):
        """Test that HTTP 404 (not found) is not retryable."""
        error = _RealHttpResponseError("Not found")
        error.status_code = 404
        assert is_retryable_error(error) is False

    def test_http_error_without_status_code(self):
        """Test that HttpResponseError without status_code is not retryable."""
        error = _RealHttpResponseError("Generic HTTP error")
        assert is_retryable_error(error) is False

    def test_unknown_exception_is_retryable(self):
        """Test that unknown exceptions are retryable by default."""
        error = RuntimeError("Unknown error")
        assert is_retryable_error(error) is True


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_try(self):
        """Test that decorator returns result when function succeeds immediately."""
        with patch("asyncio.sleep", new_callable=AsyncMock):

            @retry_with_backoff()
            async def successful_func():
                return "success"

            result = await successful_func()
            assert result == "success"

    @pytest.mark.asyncio
    async def test_retries_then_succeeds(self):
        """Test that decorator retries on retryable error then succeeds."""
        call_count = 0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            @retry_with_backoff(RetryPolicy(max_retries=3))
            async def flaky_func():
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise TimeoutError("Temporary timeout")
                return "success after retries"

            result = await flaky_func()
            assert result == "success after retries"
            assert call_count == 3
            # Should have called sleep 2 times (for the 2 failures)
            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Test that decorator raises after exceeding max retries."""
        call_count = 0
        policy = RetryPolicy(max_retries=2)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            @retry_with_backoff(policy)
            async def always_fails():
                nonlocal call_count
                call_count += 1
                raise TimeoutError("Always fails")

            with pytest.raises(TimeoutError, match="Always fails"):
                await always_fails()

            # Should try: initial + 2 retries = 3 total attempts
            assert call_count == 3
            # Should sleep between each retry (2 times)
            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_immediately_for_non_retryable_error(self):
        """Test that decorator raises immediately for non-retryable errors."""
        call_count = 0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            @retry_with_backoff()
            async def auth_error_func():
                nonlocal call_count
                call_count += 1
                raise ValueError("Invalid input")

            with pytest.raises(ValueError, match="Invalid input"):
                await auth_error_func()

            # Should only try once, no retries
            assert call_count == 1
            # Should not sleep at all
            assert mock_sleep.call_count == 0

    @pytest.mark.asyncio
    async def test_backoff_calculation(self):
        """Test that backoff times increase exponentially."""
        call_count = 0
        policy = RetryPolicy(max_retries=3, backoff_factor=2.0, max_wait=60.0)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            @retry_with_backoff(policy)
            async def always_fails():
                nonlocal call_count
                call_count += 1
                raise TimeoutError("Always fails")

            with pytest.raises(TimeoutError):
                await always_fails()

            # Check that sleep was called with increasing values
            assert mock_sleep.call_count == 3
            sleep_times = [call.args[0] for call in mock_sleep.call_args_list]

            # Verify exponential increase (with jitter tolerance)
            assert 2.0 <= sleep_times[0] <= 3.0
            assert 4.0 <= sleep_times[1] <= 5.0
            assert 8.0 <= sleep_times[2] <= 9.0

    @pytest.mark.asyncio
    async def test_max_wait_caps_backoff(self):
        """Test that max_wait caps the backoff time."""
        call_count = 0
        policy = RetryPolicy(max_retries=5, backoff_factor=10.0, max_wait=5.0)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            @retry_with_backoff(policy)
            async def always_fails():
                nonlocal call_count
                call_count += 1
                raise TimeoutError("Always fails")

            with pytest.raises(TimeoutError):
                await always_fails()

            # All sleep times should be capped at max_wait
            sleep_times = [call.args[0] for call in mock_sleep.call_args_list]
            for sleep_time in sleep_times:
                assert sleep_time <= 5.0

    @pytest.mark.asyncio
    async def test_decorator_with_function_args(self):
        """Test that decorator works with functions that take arguments."""
        call_count = 0

        with patch("asyncio.sleep", new_callable=AsyncMock):

            @retry_with_backoff(RetryPolicy(max_retries=2))
            async def func_with_args(x: int, y: str) -> str:
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise TimeoutError("Temporary error")
                return f"{x}-{y}"

            result = await func_with_args(42, "test")
            assert result == "42-test"
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_default_policy(self):
        """Test that decorator uses default policy when none provided."""
        with patch("asyncio.sleep", new_callable=AsyncMock):

            @retry_with_backoff()  # No policy provided
            async def successful_func():
                return "default policy works"

            result = await successful_func()
            assert result == "default policy works"

    @pytest.mark.asyncio
    async def test_http_429_is_retried(self):
        """Test that HTTP 429 errors are retried."""
        call_count = 0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            @retry_with_backoff(RetryPolicy(max_retries=2))
            async def rate_limited_func():
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    error = _RealHttpResponseError("Rate limited")
                    error.status_code = 429
                    raise error
                return "success"

            result = await rate_limited_func()
            assert result == "success"
            assert call_count == 3
            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_http_400_not_retried(self):
        """Test that HTTP 400 errors are not retried."""
        call_count = 0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            @retry_with_backoff(RetryPolicy(max_retries=3))
            async def bad_request_func():
                nonlocal call_count
                call_count += 1
                error = _RealHttpResponseError("Bad request")
                error.status_code = 400
                raise error

            with pytest.raises(Exception, match="Bad request"):
                await bad_request_func()

            # Should only try once
            assert call_count == 1
            assert mock_sleep.call_count == 0
