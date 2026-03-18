"""Shared pytest fixtures for unit tests."""

import pytest

from app.core.circuit_breaker import circuit_breaker_registry
from app.core.rate_limit import rate_limiter

# Import fixtures from parent conftest to make authed_client available
from tests.conftest import (  # noqa: F401
    authed_client,
    mock_authz,
    mock_user,
)


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset all circuit breakers before each test."""
    # Run before test
    circuit_breaker_registry.reset_all()
    rate_limiter._memory_cache.clear()  # prevent cross-test rate-limit bleed
    yield
    # Reset after test as well
    circuit_breaker_registry.reset_all()
    rate_limiter._memory_cache.clear()


@pytest.fixture(autouse=True)
def isolate_dependency_overrides():
    """Restore app.dependency_overrides to pre-test state after every test.

    Prevents tests that mutate dependency_overrides inside the test body
    (rather than inside a fixture) from leaking state into subsequent tests.
    """
    from app.main import app

    snapshot = dict(app.dependency_overrides)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(snapshot)
