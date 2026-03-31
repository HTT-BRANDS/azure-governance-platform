# Chaos Engineering Tests

This directory contains chaos engineering tests that verify the resilience of the Azure Governance Platform under various failure conditions.

## Overview

Chaos engineering tests intentionally inject failures to verify that:
1. Circuit breakers open and close appropriately
2. The system degrades gracefully when dependencies fail
3. Retries and timeouts work as expected
4. No cascading failures occur

## Test Categories

### `test_database_failures.py`
Tests for database-related failures:
- Connection pool exhaustion
- Query timeouts
- Transaction failures
- Database unavailability
- Read replica failover
- Graceful degradation to read-only mode

### `test_azure_api_timeouts.py`
Tests for Azure API failures:
- API timeouts
- Rate limiting (429 responses)
- Service unavailable (503 responses)
- Authentication failures (401/403)
- Intermittent/flaky responses
- Recovery after extended outages

### `test_cache_failures.py`
Tests for cache service failures:
- Redis connection failures
- Cache cluster unavailability
- Stale data handling
- Cache stampede prevention
- Memory pressure handling
- Cache poisoning recovery

### `test_service_degradation.py`
Tests for overall service degradation:
- Cascading failure prevention
- Bulkhead pattern effectiveness
- Resource exhaustion handling
- Feature tier degradation
- Emergency read-only mode
- Static fallback content

## Running the Tests

```bash
# Run all chaos tests
uv run pytest tests/chaos/ -v

# Run specific chaos test file
uv run pytest tests/chaos/test_database_failures.py -v

# Run with coverage
uv run pytest tests/chaos/ --cov=app.core.resilience --cov=app.core.circuit_breaker

# Run chaos tests only (excludes other test types)
uv run pytest tests/chaos/ -m chaos
```

## Key Patterns Tested

### Circuit Breaker Integration
All tests verify that circuit breakers properly:
- Open after threshold failures
- Half-open after recovery timeout
- Close after successful health checks
- Prevent cascading failures

### Resilience Configurations
Tests use aggressive settings for fast feedback:
- Low retry counts (2-3)
- Short delays (0.1s base)
- Fast circuit breaker thresholds (3 failures)
- Short recovery timeouts (1s)

### Deterministic Behavior
Tests use seeded randomness where applicable to ensure:
- Reproducible results
- Stable CI/CD pipelines
- Debuggable failures

## Adding New Chaos Tests

When adding new chaos tests:

1. **Identify the failure mode**: What specific failure are you testing?
2. **Use existing fixtures**: Leverage `conftest.py` fixtures for common scenarios
3. **Test both failure and recovery**: Verify the system recovers when the failure clears
4. **Document expected behavior**: Comments should explain what the system *should* do
5. **Keep tests fast**: Use short timeouts and delays for quick feedback

Example pattern:

```python
@pytest.mark.asyncio
async def test_my_failure_scenario(fragile_circuit_breaker):
    breaker = fragile_circuit_breaker

    # Simulate failure condition
    for _ in range(3):
        try:
            with breaker:
                raise MyFailureException()
        except MyFailureException:
            pass

    # Verify expected behavior
    assert breaker.is_open
```

## Integration with Existing Patterns

These tests verify the resilience patterns already in the codebase:

- `app/core/circuit_breaker.py` - Circuit breaker implementation
- `app/core/resilience.py` - Retry and resilience utilities
- `app/core/cache.py` - Caching layer with fallback
- `app/core/database.py` - Database connection management

## Safety

Chaos tests are **100% mock-based** and do not:
- Connect to actual databases
- Make real Azure API calls
- Affect production services
- Modify persistent state

All failures are simulated using unittest.mock.
