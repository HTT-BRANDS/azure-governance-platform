"""Tests for app/core/metrics.py — Prometheus metrics module.

Covers:
- Classification helpers (_classify_auth_error, _classify_db_error, _classify_http_error)
- Context managers (record_sync_operation, record_auth_check, record_db_query, record_external_api_call)
- SyncOperationContext / AuthContext / ExternalApiContext classes
- Utility functions (record_cache_operation, record_compliance_score, etc.)
- get_all_metrics structure

Phase B.1 of the test coverage sprint.
"""

from unittest.mock import patch

import pytest

from app.core.metrics import (
    AuthContext,
    ExternalApiContext,
    SyncOperationContext,
    _classify_auth_error,
    _classify_db_error,
    _classify_http_error,
    get_all_metrics,
    record_auth_check,
    record_cache_operation,
    record_compliance_score,
    record_db_query,
    record_external_api_call,
    record_sync_operation,
    record_token_operation,
    update_app_info,
)

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


class TestClassifyAuthError:
    """_classify_auth_error maps exception messages to result types."""

    def test_expired_token(self):
        assert _classify_auth_error(Exception("Token expired")) == "expired_token"

    def test_expiry_variant(self):
        assert _classify_auth_error(Exception("JWT expir at noon")) == "expired_token"

    def test_invalid_credentials(self):
        assert _classify_auth_error(Exception("Invalid token")) == "invalid_credentials"

    def test_credential_keyword(self):
        assert _classify_auth_error(Exception("Bad credential")) == "invalid_credentials"

    def test_generic_error(self):
        assert _classify_auth_error(Exception("something broke")) == "error"

    def test_empty_message(self):
        assert _classify_auth_error(Exception("")) == "error"


class TestClassifyDbError:
    """_classify_db_error maps exception messages to DB error types."""

    def test_connection_error(self):
        assert _classify_db_error(Exception("Connection refused")) == "connection_error"

    def test_connect_variant(self):
        assert _classify_db_error(Exception("can't connect to host")) == "connection_error"

    def test_timeout(self):
        assert _classify_db_error(Exception("query timeout")) == "timeout"

    def test_time_out_variant(self):
        assert _classify_db_error(Exception("time out waiting")) == "timeout"

    def test_constraint_violation(self):
        assert _classify_db_error(Exception("UNIQUE constraint failed")) == "constraint_violation"

    def test_foreign_key(self):
        assert _classify_db_error(Exception("FOREIGN KEY violation")) == "constraint_violation"

    def test_deadlock(self):
        assert _classify_db_error(Exception("deadlock detected")) == "deadlock"

    def test_other(self):
        assert _classify_db_error(Exception("something else")) == "other"


class TestClassifyHttpError:
    """_classify_http_error maps HTTP status codes to error types."""

    def test_401(self):
        assert _classify_http_error(401) == "auth_error"

    def test_403(self):
        assert _classify_http_error(403) == "auth_error"

    def test_429(self):
        assert _classify_http_error(429) == "rate_limit"

    def test_500(self):
        assert _classify_http_error(500) == "server_error"

    def test_502(self):
        assert _classify_http_error(502) == "server_error"

    def test_400(self):
        assert _classify_http_error(400) == "client_error"

    def test_404(self):
        assert _classify_http_error(404) == "client_error"


# ---------------------------------------------------------------------------
# SyncOperationContext
# ---------------------------------------------------------------------------


class TestSyncOperationContext:
    """SyncOperationContext tracks record counts for sync operations."""

    def test_initial_record_count_is_zero(self):
        ctx = SyncOperationContext("costs")
        assert ctx.record_count == 0
        assert ctx.sync_type == "costs"

    def test_set_record_count(self):
        ctx = SyncOperationContext("resources")
        ctx.set_record_count(42)
        assert ctx.record_count == 42


# ---------------------------------------------------------------------------
# AuthContext
# ---------------------------------------------------------------------------


class TestAuthContext:
    """AuthContext is a simple marker class."""

    def test_instantiation(self):
        ctx = AuthContext()
        assert ctx is not None


# ---------------------------------------------------------------------------
# ExternalApiContext
# ---------------------------------------------------------------------------


class TestExternalApiContext:
    """ExternalApiContext records status codes and classifies errors."""

    def test_init(self):
        ctx = ExternalApiContext("azure_graph", "/users")
        assert ctx.service == "azure_graph"
        assert ctx.endpoint == "/users"
        assert ctx._status_code is None

    @patch("app.core.metrics.external_api_errors_counter")
    def test_set_status_code_success(self, mock_counter):
        ctx = ExternalApiContext("azure_graph", "/users")
        ctx.set_status_code(200)
        assert ctx._status_code == 200
        mock_counter.labels.assert_not_called()

    @patch("app.core.metrics.rate_limit_hits_counter")
    @patch("app.core.metrics.external_api_errors_counter")
    def test_set_status_code_429_records_rate_limit(self, mock_errors, mock_rl):
        ctx = ExternalApiContext("azure_graph", "/users")
        ctx.set_status_code(429)
        mock_errors.labels.assert_called_once()
        mock_rl.labels.assert_called_once()

    @patch("app.core.metrics.external_api_errors_counter")
    def test_set_status_code_500(self, mock_counter):
        ctx = ExternalApiContext("azure_cost", "/query")
        ctx.set_status_code(500)
        mock_counter.labels.assert_called_once_with(
            service="azure_cost",
            error_type="server_error",
            status_code="500",
        )


# ---------------------------------------------------------------------------
# Context managers — record_sync_operation
# ---------------------------------------------------------------------------


class TestRecordSyncOperation:
    """record_sync_operation tracks duration, active gauge, and record counts."""

    @patch("app.core.metrics.sync_records_counter")
    @patch("app.core.metrics.sync_last_success_timestamp")
    @patch("app.core.metrics.sync_duration_histogram")
    @patch("app.core.metrics.sync_active_gauge")
    def test_success_path(self, mock_gauge, mock_hist, mock_ts, mock_counter):
        with record_sync_operation("costs", record_count=10) as ctx:
            assert ctx.sync_type == "costs"

        mock_gauge.labels.return_value.inc.assert_called_once()
        mock_gauge.labels.return_value.dec.assert_called_once()
        mock_hist.labels.assert_called_once_with(sync_type="costs", status="success")
        mock_ts.labels.assert_called_once_with(sync_type="costs")

    @patch("app.core.metrics.sync_records_counter")
    @patch("app.core.metrics.sync_last_success_timestamp")
    @patch("app.core.metrics.sync_duration_histogram")
    @patch("app.core.metrics.sync_active_gauge")
    def test_failure_path(self, mock_gauge, mock_hist, mock_ts, mock_counter):
        with pytest.raises(ValueError, match="boom"):
            with record_sync_operation("compliance"):
                raise ValueError("boom")

        mock_hist.labels.assert_called_once_with(sync_type="compliance", status="failure")
        mock_gauge.labels.return_value.dec.assert_called_once()

    @patch("app.core.metrics.sync_records_counter")
    @patch("app.core.metrics.sync_last_success_timestamp")
    @patch("app.core.metrics.sync_duration_histogram")
    @patch("app.core.metrics.sync_active_gauge")
    def test_timeout_path(self, mock_gauge, mock_hist, mock_ts, mock_counter):
        with pytest.raises(TimeoutError):
            with record_sync_operation("resources"):
                raise TimeoutError("timed out")

        mock_hist.labels.assert_called_once_with(sync_type="resources", status="timeout")

    @patch("app.core.metrics.sync_records_counter")
    @patch("app.core.metrics.sync_last_success_timestamp")
    @patch("app.core.metrics.sync_duration_histogram")
    @patch("app.core.metrics.sync_active_gauge")
    def test_ctx_record_count_used_when_set(self, mock_gauge, mock_hist, mock_ts, mock_counter):
        with record_sync_operation("costs") as ctx:
            ctx.set_record_count(77)

        mock_counter.labels.assert_called_once_with(sync_type="costs", record_type="records")
        mock_counter.labels.return_value.inc.assert_called_once_with(77)


# ---------------------------------------------------------------------------
# Context managers — record_auth_check
# ---------------------------------------------------------------------------


class TestRecordAuthCheck:
    """record_auth_check tracks latency and attempt results."""

    @patch("app.core.metrics.auth_attempts_counter")
    @patch("app.core.metrics.auth_latency_histogram")
    def test_success(self, mock_hist, mock_counter):
        with record_auth_check("login", "azure_ad"):
            pass

        mock_hist.labels.assert_called_once_with(operation="login", provider="azure_ad")
        mock_counter.labels.assert_called_once_with(operation="login", result="success")

    @patch("app.core.metrics.auth_attempts_counter")
    @patch("app.core.metrics.auth_latency_histogram")
    def test_expired_error(self, mock_hist, mock_counter):
        with pytest.raises(Exception):  # noqa: B017
            with record_auth_check("validate"):
                raise Exception("Token expired at noon")

        mock_counter.labels.assert_called_once_with(operation="validate", result="expired_token")


# ---------------------------------------------------------------------------
# Context managers — record_db_query
# ---------------------------------------------------------------------------


class TestRecordDbQuery:
    """record_db_query tracks duration and classifies errors."""

    @patch("app.core.metrics.db_query_duration_histogram")
    def test_success(self, mock_hist):
        with record_db_query("select", "costs"):
            pass

        mock_hist.labels.assert_called_once_with(operation="select", table="costs")
        mock_hist.labels.return_value.observe.assert_called_once()

    @patch("app.core.metrics.db_errors_counter")
    @patch("app.core.metrics.db_query_duration_histogram")
    def test_error_classified(self, mock_hist, mock_err):
        with pytest.raises(Exception):  # noqa: B017
            with record_db_query("insert", "tenants"):
                raise Exception("Connection refused by server")

        mock_err.labels.assert_called_once_with(error_type="connection_error")


# ---------------------------------------------------------------------------
# Context managers — record_external_api_call
# ---------------------------------------------------------------------------


class TestRecordExternalApiCall:
    """record_external_api_call tracks latency and errors."""

    @patch("app.core.metrics.external_api_latency_histogram")
    def test_success(self, mock_hist):
        with record_external_api_call("azure_graph", "/users") as ctx:
            assert isinstance(ctx, ExternalApiContext)

        mock_hist.labels.assert_called_once_with(service="azure_graph", endpoint="/users")
        mock_hist.labels.return_value.observe.assert_called_once()

    @patch("app.core.metrics.external_api_errors_counter")
    @patch("app.core.metrics.external_api_latency_histogram")
    def test_timeout_error(self, mock_hist, mock_err):
        with pytest.raises(Exception):  # noqa: B017
            with record_external_api_call("azure_cost", "/query"):
                raise Exception("Read timeout occurred")

        mock_err.labels.assert_called_once_with(
            service="azure_cost", error_type="timeout", status_code="0"
        )


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


class TestUtilityFunctions:
    """Standalone metric recording helpers."""

    @patch("app.core.metrics.cache_operations_counter")
    def test_record_cache_operation(self, mock_counter):
        record_cache_operation("redis", "get", "hit", count=5)
        mock_counter.labels.assert_called_once_with(backend="redis", operation="get", result="hit")
        mock_counter.labels.return_value.inc.assert_called_once_with(5)

    @patch("app.core.metrics.compliance_score_gauge")
    def test_record_compliance_score(self, mock_gauge):
        record_compliance_score("t-1", "SOC2", 92.5)
        mock_gauge.labels.assert_called_once_with(tenant_id="t-1", framework="SOC2")
        mock_gauge.labels.return_value.set.assert_called_once_with(92.5)

    @patch("app.core.metrics.token_operations_counter")
    def test_record_token_operation(self, mock_counter):
        record_token_operation("issue", "refresh_token")
        mock_counter.labels.assert_called_once_with(operation="issue", token_type="refresh_token")

    @patch("app.core.metrics.app_info")
    def test_update_app_info(self, mock_info):
        update_app_info("2.0.0", "production")
        mock_info.info.assert_called_once_with({"version": "2.0.0", "environment": "production"})


# ---------------------------------------------------------------------------
# get_all_metrics
# ---------------------------------------------------------------------------


class TestGetAllMetrics:
    """get_all_metrics returns a well-structured dictionary."""

    def test_returns_dict(self):
        result = get_all_metrics()
        assert isinstance(result, dict)

    def test_top_level_keys(self):
        result = get_all_metrics()
        expected_keys = {"sync", "auth", "database", "cache", "external_api", "business"}
        assert set(result.keys()) == expected_keys

    def test_sync_section(self):
        result = get_all_metrics()
        assert "duration" in result["sync"]
        assert "records" in result["sync"]
        assert "active" in result["sync"]
        assert "last_success" in result["sync"]

    def test_metric_names_are_strings(self):
        result = get_all_metrics()
        for section in result.values():
            for value in section.values():
                assert isinstance(value, str)
                assert value.startswith("governance_")
