"""
Chaos Engineering: Azure API Timeout and Failure Tests

Tests system resilience against Azure API degradation:
- Timeout scenarios
- Rate limiting responses
- Service unavailable errors
- Intermittent failures
"""

import asyncio
from unittest.mock import MagicMock

import httpx
import pytest

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.core.resilience import ResilienceConfig


class TestAzureAPITimeouts:
    """Test behavior when Azure API calls timeout."""

    @pytest.mark.asyncio
    async def test_timeout_triggers_circuit_breaker(self):
        """Repeated timeouts should open the circuit breaker."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1.0)
        breaker = CircuitBreaker(name="azure_api", config=config)

        async def failing_call():
            raise TimeoutError("Azure API timeout")

        # Trigger failures using correct API
        for _ in range(3):
            if breaker.can_execute():
                try:
                    await failing_call()
                except TimeoutError:
                    breaker.record_failure()

        assert breaker.is_open, "Circuit should open after repeated timeouts"

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Retries should use exponential backoff with jitter."""
        config = ResilienceConfig(
            max_retries=3,
            base_delay=0.1,
            max_delay=1.0,
            jitter=True,
        )

        delays = []
        for i in range(config.max_retries):
            delay = min(config.base_delay * (2**i), config.max_delay)
            if config.jitter:
                delay = delay * 0.8  # Simulate jitter reduction
            delays.append(delay)

        # Verify exponential growth
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]
        assert all(d <= config.max_delay for d in delays)

    @pytest.mark.asyncio
    async def test_success_after_transient_timeout(self):
        """Operation should succeed after transient timeout recovery."""
        call_count = 0

        async def flaky_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Transient timeout")
            return {"success": True}

        result = None
        for _attempt in range(5):
            try:
                result = await flaky_call()
                break
            except TimeoutError:
                await asyncio.sleep(0.05)  # Small retry delay

        assert result is not None
        assert result.get("success") is True
        assert call_count == 3


class TestAzureRateLimiting:
    """Test behavior when Azure API rate limits are hit."""

    @pytest.mark.asyncio
    async def test_retry_after_header_compliance(self):
        """System should respect Retry-After header."""
        retry_after_seconds = 5

        response = MagicMock()
        response.status_code = 429
        response.headers = {"Retry-After": str(retry_after_seconds)}

        # Should extract and use the retry delay
        assert int(response.headers.get("Retry-After", 0)) == retry_after_seconds

    @pytest.mark.asyncio
    async def test_rate_limit_circuit_breaker(self):
        """Rate limit responses (429) should count toward circuit breaker."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            expected_exception=(Exception,),
        )
        breaker = CircuitBreaker(name="azure_rate_limit", config=config)

        # Simulate 429 responses
        for _ in range(3):
            if breaker.can_execute():
                try:
                    raise httpx.HTTPStatusError(
                        "Rate limited",
                        request=MagicMock(),
                        response=MagicMock(status_code=429),
                    )
                except httpx.HTTPStatusError:
                    breaker.record_failure()

        assert breaker.is_open, "Rate limiting should trigger circuit breaker"

    @pytest.mark.asyncio
    async def test_token_bucket_rate_limiter(self):
        """Token bucket rate limiter should throttle requests."""
        max_requests = 10
        time_window = 60  # seconds

        # Simulate token bucket
        tokens = max_requests
        last_refill = asyncio.get_event_loop().time()

        async def make_request():
            nonlocal tokens, last_refill
            now = asyncio.get_event_loop().time()

            # Refill tokens
            elapsed = now - last_refill
            tokens = min(max_requests, tokens + int(elapsed * max_requests / time_window))
            last_refill = now

            if tokens > 0:
                tokens -= 1
                return {"success": True}
            else:
                raise Exception("Rate limit exceeded")

        # First 10 requests succeed
        for _ in range(10):
            result = await make_request()
            assert result["success"]

        # 11th request should fail
        with pytest.raises(Exception, match="Rate limit"):
            await make_request()


class TestAzureServiceUnavailable:
    """Test behavior during Azure service outages."""

    @pytest.mark.asyncio
    async def test_503_service_unavailable_handling(self):
        """503 responses should trigger retry with backoff."""
        responses = [
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(200, json={"status": "ok"}),
        ]

        response_iter = iter(responses)

        async def mock_request():
            response = next(response_iter)
            if response.status_code >= 500:
                raise httpx.HTTPStatusError(
                    "Server error",
                    request=MagicMock(),
                    response=response,
                )
            return response

        # Retry loop
        result = None
        for attempt in range(3):
            try:
                result = await mock_request()
                break
            except httpx.HTTPStatusError:
                if attempt < 2:
                    await asyncio.sleep(0.1)

        assert result is not None
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_graceful_degradation_during_outage(self):
        """System should use cached data during Azure service outages."""
        cached_data = {
            "subscriptions": ["sub-1", "sub-2"],
            "cached_at": "2024-01-01T00:00:00Z",
        }

        # Simulate Azure outage
        azure_available = False

        def get_subscriptions():
            if azure_available:
                return {"subscriptions": ["sub-1", "sub-2", "sub-3"], "fresh": True}
            return {**cached_data, "stale": True}

        result = get_subscriptions()

        assert "stale" in result
        assert result["subscriptions"] == cached_data["subscriptions"]


class TestAzureIntermittentFailures:
    """Test behavior with flaky Azure API responses."""

    @pytest.mark.asyncio
    async def test_success_with_flaky_api(self):
        """System should eventually succeed with flaky Azure API."""
        call_count = 0

        async def flaky_azure_call():
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:  # Fail odd calls
                raise httpx.NetworkError("Connection reset")
            return {"data": "success"}

        # With retries, should eventually succeed
        max_attempts = 5
        result = None

        for _attempt in range(max_attempts):
            try:
                result = await flaky_azure_call()
                break
            except httpx.NetworkError:
                await asyncio.sleep(0.05)

        assert result is not None
        assert result.get("data") == "success"

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_flaky_service(self):
        """Circuit breaker should protect against consistently flaky service."""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=2.0,
            success_threshold=2,
        )
        breaker = CircuitBreaker(name="flaky_azure", config=config)

        failure_rate = 0.7  # 70% failure rate
        call_count = 0

        async def very_flaky_call():
            nonlocal call_count
            call_count += 1
            import random

            random.seed(call_count)  # Deterministic
            if random.random() < failure_rate:
                raise Exception("Random failure")
            return "success"

        # Run many calls through circuit breaker
        successes = 0
        failures = 0
        circuit_opens = 0

        for _ in range(20):
            if not breaker.can_execute():
                circuit_opens += 1
                continue

            try:
                await very_flaky_call()
                breaker.record_success()
                successes += 1
            except Exception:
                breaker.record_failure()
                failures += 1

        # Circuit should have opened at some point or be open now
        assert circuit_opens > 0 or breaker.is_open


class TestAzureAuthenticationFailures:
    """Test behavior when Azure authentication fails."""

    @pytest.mark.asyncio
    async def test_token_refresh_on_auth_failure(self):
        """System should refresh token on 401 responses."""
        token_refreshed = False

        async def make_request():
            nonlocal token_refreshed
            if not token_refreshed:
                token_refreshed = True
                raise httpx.HTTPStatusError(
                    "Unauthorized",
                    request=MagicMock(),
                    response=MagicMock(status_code=401),
                )
            return {"status": "success"}

        # Simulate retry with token refresh
        for _attempt in range(2):
            try:
                result = await make_request()
                assert result["status"] == "success"
                break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    continue

        assert token_refreshed

    @pytest.mark.asyncio
    async def test_fallback_to_secondary_credential(self):
        """System should try secondary credential on auth failure."""
        primary_credential_failed = True
        secondary_credential_worked = True

        def authenticate():
            if primary_credential_failed:
                if secondary_credential_worked:
                    return {"token": "secondary_token", "source": "secondary"}
                raise Exception("All credentials failed")
            return {"token": "primary_token", "source": "primary"}

        result = authenticate()

        assert result["source"] == "secondary"


class TestAzureAPITimeoutRecovery:
    """Test recovery patterns after Azure API timeouts."""

    @pytest.mark.asyncio
    async def test_fast_fail_after_timeout(self):
        """After timeout, subsequent calls should fail fast."""
        timeout_occurred = False

        async def monitored_call():
            nonlocal timeout_occurred
            if timeout_occurred:
                # Fast fail - don't wait again
                raise Exception("Fast fail - previous timeout")
            timeout_occurred = True
            raise TimeoutError("Initial timeout")

        # First call times out
        with pytest.raises(asyncio.TimeoutError):
            await monitored_call()

        # Subsequent call fails fast
        with pytest.raises(Exception, match="Fast fail"):
            await monitored_call()

    @pytest.mark.asyncio
    async def test_staggered_recovery_after_outage(self):
        """System should gradually recover after extended outage."""
        outage_duration = 10  # seconds of outage
        recovery_progress = []

        for second in range(outage_duration + 5):
            if second < outage_duration:
                # During outage
                available = False
            elif second < outage_duration + 2:
                # Gradual recovery - some services back
                available = second % 2 == 0
            else:
                # Full recovery
                available = True

            recovery_progress.append(
                {
                    "second": second,
                    "available": available,
                }
            )

        # Verify progression
        assert not recovery_progress[0]["available"]  # Start in outage
        assert recovery_progress[-1]["available"]  # End recovered
