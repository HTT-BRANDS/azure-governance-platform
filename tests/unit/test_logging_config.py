"""Unit tests for app/core/logging_config.py.

Tests correlation ID management, request timing, log_api_request
at various status-code levels, JSONFormatter output, and
configure_logging handler setup.
"""

import json
import logging
import time
from unittest.mock import patch

import pytest

from app.core.logging_config import (
    JSONFormatter,
    configure_logging,
    correlation_id,
    get_correlation_id,
    get_request_duration_ms,
    log_api_request,
    request_start_time,
    set_correlation_id,
    set_request_start_time,
)


@pytest.fixture(autouse=True)
def _reset_context_vars():
    """Reset ContextVars before and after each test to prevent leakage."""
    tok_cid = correlation_id.set(None)
    tok_rst = request_start_time.set(None)
    yield
    correlation_id.reset(tok_cid)
    request_start_time.reset(tok_rst)


# ============================================================================
# Correlation ID Tests
# ============================================================================


def test_get_correlation_id_creates_new_id_when_none_set():
    """get_correlation_id generates a new 8-char UUID prefix when unset."""
    cid = get_correlation_id()

    assert isinstance(cid, str)
    assert len(cid) == 8
    # Should be a valid hex substring (uuid4 first 8 chars)
    int(cid.replace("-", ""), 16)


def test_get_correlation_id_returns_same_id_on_repeated_calls():
    """get_correlation_id returns the same value once created."""
    first = get_correlation_id()
    second = get_correlation_id()

    assert first == second


def test_set_correlation_id_stores_and_retrieves_correctly():
    """set_correlation_id stores a custom ID that get_correlation_id returns."""
    set_correlation_id("my-custom-id")

    assert get_correlation_id() == "my-custom-id"


def test_set_correlation_id_overrides_auto_generated():
    """set_correlation_id overrides a previously auto-generated ID."""
    auto_id = get_correlation_id()
    assert len(auto_id) == 8

    set_correlation_id("override-id")

    assert get_correlation_id() == "override-id"


# ============================================================================
# Request Duration Tests
# ============================================================================


def test_get_request_duration_ms_returns_none_without_start_time():
    """get_request_duration_ms returns None when no start time is set."""
    assert get_request_duration_ms() is None


def test_get_request_duration_ms_returns_positive_duration():
    """get_request_duration_ms returns a positive float after start time is set."""
    set_request_start_time()
    # Small sleep to ensure measurable duration
    time.sleep(0.01)

    duration = get_request_duration_ms()

    assert duration is not None
    assert isinstance(duration, float)
    assert duration > 0


def test_get_request_duration_ms_increases_over_time():
    """get_request_duration_ms returns increasing values over time."""
    set_request_start_time()
    time.sleep(0.005)
    first = get_request_duration_ms()
    time.sleep(0.005)
    second = get_request_duration_ms()

    assert first is not None
    assert second is not None
    assert second > first


# ============================================================================
# log_api_request Tests — Status Code Levels
# ============================================================================


def test_log_api_request_logs_error_for_500_status():
    """log_api_request uses logger.error for status_code >= 500."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request("GET", "/api/test", 500, 123.45)

        mock_logger.error.assert_called_once()
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_not_called()

        # Verify the logged data is valid JSON with correct fields
        logged_json = mock_logger.error.call_args[0][0]
        data = json.loads(logged_json)
        assert data["method"] == "GET"
        assert data["path"] == "/api/test"
        assert data["status_code"] == 500
        assert data["duration_ms"] == 123.45


def test_log_api_request_logs_error_for_503_status():
    """log_api_request uses logger.error for 503 (service unavailable)."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request("POST", "/api/data", 503, 50.0)

        mock_logger.error.assert_called_once()
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_not_called()


def test_log_api_request_logs_warning_for_400_status():
    """log_api_request uses logger.warning for 400-499 status codes."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request("POST", "/api/login", 401, 55.0)

        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_not_called()
        mock_logger.info.assert_not_called()

        logged_json = mock_logger.warning.call_args[0][0]
        data = json.loads(logged_json)
        assert data["status_code"] == 401


def test_log_api_request_logs_warning_for_404_status():
    """log_api_request uses logger.warning for 404 (not found)."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request("GET", "/api/missing", 404, 10.0)

        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_not_called()
        mock_logger.info.assert_not_called()


def test_log_api_request_logs_info_for_200_status():
    """log_api_request uses logger.info for 200-299 status codes."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request("GET", "/api/health", 200, 5.0)

        mock_logger.info.assert_called_once()
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()

        logged_json = mock_logger.info.call_args[0][0]
        data = json.loads(logged_json)
        assert data["status_code"] == 200
        assert data["event"] == "api_request"


def test_log_api_request_logs_info_for_201_status():
    """log_api_request uses logger.info for 201 (created)."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request("POST", "/api/resources", 201, 80.0)

        mock_logger.info.assert_called_once()


def test_log_api_request_includes_user_and_tenant():
    """log_api_request includes user_id and tenant_id in log data."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request(
            "GET", "/api/data", 200, 10.0,
            user_id="user-123",
            tenant_id="tenant-456",
        )

        logged_json = mock_logger.info.call_args[0][0]
        data = json.loads(logged_json)
        assert data["user_id"] == "user-123"
        assert data["tenant_id"] == "tenant-456"


def test_log_api_request_includes_extra_fields():
    """log_api_request merges extra dict into log data."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request(
            "GET", "/api/data", 200, 10.0,
            extra={"request_id": "req-789", "region": "eastus"},
        )

        logged_json = mock_logger.info.call_args[0][0]
        data = json.loads(logged_json)
        assert data["request_id"] == "req-789"
        assert data["region"] == "eastus"


def test_log_api_request_includes_correlation_id():
    """log_api_request embeds the current correlation_id."""
    set_correlation_id("test-corr-id")

    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request("GET", "/api/test", 200, 1.0)

        logged_json = mock_logger.info.call_args[0][0]
        data = json.loads(logged_json)
        assert data["correlation_id"] == "test-corr-id"


def test_log_api_request_rounds_duration():
    """log_api_request rounds duration_ms to 2 decimal places."""
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value
        log_api_request("GET", "/api/test", 200, 123.456789)

        logged_json = mock_logger.info.call_args[0][0]
        data = json.loads(logged_json)
        assert data["duration_ms"] == 123.46


# ============================================================================
# JSONFormatter Tests
# ============================================================================


def test_json_formatter_produces_valid_json():
    """JSONFormatter.format returns a valid JSON string."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Hello world",
        args=None,
        exc_info=None,
    )

    output = formatter.format(record)

    data = json.loads(output)
    assert data["level"] == "INFO"
    assert data["logger"] == "test.logger"
    assert data["message"] == "Hello world"
    assert "timestamp" in data
    assert "correlation_id" in data
    assert data["path"] == "test_file.py:42"


def test_json_formatter_includes_correlation_id():
    """JSONFormatter embeds the current context correlation_id."""
    set_correlation_id("fmt-corr-id")
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="f.py",
        lineno=1, msg="msg", args=None, exc_info=None,
    )

    output = formatter.format(record)
    data = json.loads(output)

    assert data["correlation_id"] == "fmt-corr-id"


def test_json_formatter_includes_duration_when_available():
    """JSONFormatter includes duration_ms when request timing is active."""
    set_request_start_time()
    time.sleep(0.005)

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="f.py",
        lineno=1, msg="msg", args=None, exc_info=None,
    )

    output = formatter.format(record)
    data = json.loads(output)

    assert "duration_ms" in data
    assert isinstance(data["duration_ms"], float)
    assert data["duration_ms"] > 0


def test_json_formatter_omits_duration_when_no_start_time():
    """JSONFormatter omits duration_ms when no request timing is set."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="f.py",
        lineno=1, msg="msg", args=None, exc_info=None,
    )

    output = formatter.format(record)
    data = json.loads(output)

    assert "duration_ms" not in data


def test_json_formatter_includes_exception_info():
    """JSONFormatter includes exception details when exc_info is present."""
    formatter = JSONFormatter()
    try:
        raise ValueError("test error")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test", level=logging.ERROR, pathname="f.py",
        lineno=1, msg="something broke", args=None, exc_info=exc_info,
    )

    output = formatter.format(record)
    data = json.loads(output)

    assert "exception" in data
    assert "ValueError" in data["exception"]
    assert "test error" in data["exception"]


# ============================================================================
# configure_logging Tests
# ============================================================================


def test_configure_logging_sets_up_root_handler():
    """configure_logging attaches a StreamHandler to the root logger."""
    # Save original state
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level

    try:
        configure_logging()

        assert len(root.handlers) == 1
        handler = root.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, JSONFormatter)
        assert root.level == logging.INFO
    finally:
        # Restore original state
        root.handlers = original_handlers
        root.level = original_level


def test_configure_logging_sets_api_logger_level():
    """configure_logging sets api.requests logger to INFO."""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level

    try:
        configure_logging()

        api_logger = logging.getLogger("api.requests")
        assert api_logger.level == logging.INFO
    finally:
        root.handlers = original_handlers
        root.level = original_level


def test_configure_logging_reduces_third_party_noise():
    """configure_logging sets uvicorn/sqlalchemy loggers to WARNING."""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level

    try:
        configure_logging()

        assert logging.getLogger("uvicorn.access").level == logging.WARNING
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING
    finally:
        root.handlers = original_handlers
        root.level = original_level
