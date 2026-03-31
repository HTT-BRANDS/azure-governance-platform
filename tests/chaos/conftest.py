"""Shared fixtures for chaos engineering tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.core.database import Base
from app.core.resilience import ResilienceConfig


@pytest.fixture
def chaos_config() -> ResilienceConfig:
    """Return aggressive chaos test config with short timeouts."""
    return ResilienceConfig(
        max_retries=2,
        base_delay=0.1,
        max_delay=1.0,
        jitter=False,  # Deterministic for tests
        rate_limit_timeout=5.0,
    )


@pytest.fixture
def fragile_circuit_breaker() -> CircuitBreaker:
    """Return circuit breaker with low thresholds for fast failure testing."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1.0,
        success_threshold=1,
    )
    return CircuitBreaker(name="chaos_test_breaker", config=config)


@pytest.fixture
def mock_failing_db() -> Generator[MagicMock, None, None]:
    """Mock database that simulates connection failures."""
    with patch("app.core.database._get_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("Simulated database connection failure")
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        yield mock_engine


@pytest.fixture
def flaky_azure_response() -> Generator[MagicMock, None, None]:
    """Mock Azure API responses that fail intermittently."""
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count % 3 != 0:  # Fail 2 out of 3 calls
            raise Exception(f"Azure API timeout (call #{call_count})")
        return MagicMock(status_code=200, json=lambda: {"value": []})

    with patch("httpx.AsyncClient.request") as mock_request:
        mock_request.side_effect = side_effect
        yield mock_request


@pytest.fixture
def degraded_cache() -> Generator[MagicMock, None, None]:
    """Mock cache that fails or returns stale data."""
    with patch("app.core.cache.redis_client") as mock_cache:
        # Simulate cache that accepts writes but fails reads
        mock_cache.get.side_effect = Exception("Cache cluster unreachable")
        mock_cache.set.return_value = True  # Writes succeed but don't persist
        mock_cache.ping.return_value = False
        yield mock_cache


@pytest.fixture
def timeout_engine() -> Generator[MagicMock, None, None]:
    """Mock SQLAlchemy engine that times out on connections."""
    with patch("app.core.database.create_engine") as mock_create:
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = TimeoutError("Database connection timeout")
        mock_create.return_value = mock_engine
        yield mock_create


@pytest.fixture
def memory_db_session() -> Generator[sessionmaker, None, None]:
    """Create an in-memory SQLite database for isolated chaos tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
