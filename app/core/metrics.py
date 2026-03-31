"""Custom Prometheus metrics for Azure Governance Platform.

Provides application-specific metrics beyond the default FastAPI instrumentation:
- Sync operation duration and success rates
- Authentication latency and token operations
- Database query performance
- Cache hit/miss rates
- External API call latencies

Usage:
    from app.core.metrics import (
        sync_duration_histogram,
        auth_latency_histogram,
        record_sync_operation,
        record_auth_check,
    )

    # Record sync operation
    with record_sync_operation("costs"):
        result = perform_sync()

Traces: NF-P02 (API response time), NF-P03 (Concurrent users), NF-M04 (Observability)
"""

import time
from contextlib import contextmanager
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Info

# =============================================================================
# Application Info
# =============================================================================

app_info = Info(
    "governance_app_info",
    "Application version and build information",
    [
        "version",
        "environment",
    ],
)

# =============================================================================
# Sync Operation Metrics
# =============================================================================

sync_duration_histogram = Histogram(
    "governance_sync_duration_seconds",
    "Duration of sync operations by type",
    [
        "sync_type",  # costs, compliance, resources, identity, riverside
        "status",  # success, failure, timeout
    ],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
)

sync_records_counter = Counter(
    "governance_sync_records_total",
    "Number of records synced by type",
    [
        "sync_type",
        "record_type",  # azure_resources, cost_data, compliance_findings
    ],
)

sync_active_gauge = Gauge(
    "governance_sync_active_jobs",
    "Number of currently active sync jobs",
    [
        "sync_type",
    ],
)

sync_last_success_timestamp = Gauge(
    "governance_sync_last_success_timestamp",
    "Unix timestamp of last successful sync by type",
    [
        "sync_type",
    ],
)

# =============================================================================
# Authentication Metrics
# =============================================================================

auth_latency_histogram = Histogram(
    "governance_auth_latency_seconds",
    "Authentication and authorization operation latency",
    [
        "operation",  # login, token_refresh, validate, me
        "provider",  # azure_ad, staging_token, api_key
    ],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

auth_attempts_counter = Counter(
    "governance_auth_attempts_total",
    "Authentication attempts by result",
    [
        "operation",
        "result",  # success, invalid_credentials, expired_token, error
    ],
)

auth_active_sessions_gauge = Gauge(
    "governance_auth_active_sessions",
    "Number of currently active user sessions",
    [
        "tenant_id",
    ],
)

token_operations_counter = Counter(
    "governance_token_operations_total",
    "Token operations (issue, refresh, revoke, blacklist)",
    [
        "operation",  # issue, refresh, revoke, validate
        "token_type",  # access_token, refresh_token
    ],
)

# =============================================================================
# Database Metrics
# =============================================================================

db_query_duration_histogram = Histogram(
    "governance_db_query_duration_seconds",
    "Database query execution time",
    [
        "operation",  # select, insert, update, delete
        "table",  # costs, compliance, resources, sync_jobs, etc
    ],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

db_connections_gauge = Gauge(
    "governance_db_connections_active",
    "Active database connections",
    [
        "state",  # idle, active
    ],
)

db_pool_size_gauge = Gauge(
    "governance_db_pool_size",
    "Database connection pool size",
    [
        "pool_type",  # total, used, available
    ],
)

db_errors_counter = Counter(
    "governance_db_errors_total",
    "Database errors by type",
    [
        "error_type",  # connection_error, timeout, constraint_violation, deadlock
    ],
)

# =============================================================================
# Cache Metrics
# =============================================================================

cache_operations_counter = Counter(
    "governance_cache_operations_total",
    "Cache operations by result",
    [
        "backend",  # redis, memory
        "operation",  # get, set, delete, expire
        "result",  # hit, miss, success, error
    ],
)

cache_size_gauge = Gauge(
    "governance_cache_size_bytes",
    "Cache size in bytes",
    [
        "backend",
    ],
)

cache_ttl_histogram = Histogram(
    "governance_cache_ttl_seconds",
    "Time-to-live for cached items",
    [
        "cache_type",  # costs, compliance, resources, session, token
    ],
    buckets=[60, 300, 600, 1800, 3600, 7200, 86400],
)

# =============================================================================
# External API Metrics
# =============================================================================

external_api_latency_histogram = Histogram(
    "governance_external_api_latency_seconds",
    "External API call latency",
    [
        "service",  # azure_graph, azure_cost, azure_resource, teams_webhook
        "endpoint",  # simplified endpoint path
    ],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

external_api_errors_counter = Counter(
    "governance_external_api_errors_total",
    "External API errors",
    [
        "service",
        "error_type",  # timeout, rate_limit, auth_error, server_error, client_error
        "status_code",  # 401, 403, 429, 500, etc
    ],
)

external_api_rate_limit_gauge = Gauge(
    "governance_external_api_rate_limit_remaining",
    "Remaining rate limit for external APIs",
    [
        "service",
    ],
)

# =============================================================================
# Rate Limiting Metrics
# =============================================================================

rate_limit_hits_counter = Counter(
    "governance_rate_limit_hits_total",
    "Rate limit hits by client",
    [
        "endpoint",
        "limit_type",  # per_minute, per_hour, burst
    ],
)

rate_limit_current_gauge = Gauge(
    "governance_rate_limit_current_requests",
    "Current request count in rate limit window",
    [
        "client_id",
        "endpoint",
    ],
)

# =============================================================================
# Business Logic Metrics
# =============================================================================

compliance_score_gauge = Gauge(
    "governance_compliance_score",
    "Compliance score by framework",
    [
        "tenant_id",
        "framework",  # SOC2, ISO27001, NIST, CIS
    ],
)

cost_anomaly_counter = Counter(
    "governance_cost_anomalies_total",
    "Detected cost anomalies",
    [
        "severity",  # info, warning, critical
        "resource_type",
    ],
)

recommendation_generated_counter = Counter(
    "governance_recommendations_generated_total",
    "Cost optimization recommendations generated",
    [
        "category",  # compute, storage, network, license
        "priority",  # high, medium, low
    ],
)

# =============================================================================
# Context Managers for Recording
# =============================================================================


@contextmanager
def record_sync_operation(
    sync_type: str,
    record_count: int = 0,
) -> "SyncOperationContext":
    """Context manager to record sync operation metrics.

    Args:
        sync_type: Type of sync (costs, compliance, resources, etc.)
        record_count: Number of records synced (0 to skip counting)

    Example:
        with record_sync_operation("costs", record_count=100) as ctx:
            result = perform_cost_sync()
            ctx.set_record_count(len(result))
    """
    ctx = SyncOperationContext(sync_type)
    sync_active_gauge.labels(sync_type=sync_type).inc()

    start_time = time.perf_counter()
    try:
        yield ctx
        status = "success"
        sync_last_success_timestamp.labels(sync_type=sync_type).set(time.time())
    except TimeoutError:
        status = "timeout"
        raise
    except Exception:
        status = "failure"
        raise
    finally:
        duration = time.perf_counter() - start_time
        sync_duration_histogram.labels(
            sync_type=sync_type,
            status=status,
        ).observe(duration)
        sync_active_gauge.labels(sync_type=sync_type).dec()

        if ctx.record_count > 0 or record_count > 0:
            count = ctx.record_count or record_count
            sync_records_counter.labels(
                sync_type=sync_type,
                record_type="records",
            ).inc(count)


class SyncOperationContext:
    """Context for sync operation metric recording."""

    def __init__(self, sync_type: str) -> None:
        self.sync_type = sync_type
        self.record_count = 0

    def set_record_count(self, count: int) -> None:
        """Update the record count for this sync operation."""
        self.record_count = count


@contextmanager
def record_auth_check(
    operation: str,
    provider: str = "azure_ad",
) -> "AuthContext":
    """Context manager to record authentication metrics.

    Args:
        operation: Auth operation (login, token_refresh, validate, me)
        provider: Auth provider (azure_ad, staging_token, api_key)

    Example:
        with record_auth_check("login", "azure_ad"):
            user = authenticate_user(credentials)
    """
    ctx = AuthContext()
    start_time = time.perf_counter()

    try:
        yield ctx
        result = "success"
    except Exception as e:
        result = _classify_auth_error(e)
        raise
    finally:
        duration = time.perf_counter() - start_time
        auth_latency_histogram.labels(
            operation=operation,
            provider=provider,
        ).observe(duration)
        auth_attempts_counter.labels(
            operation=operation,
            result=result,
        ).inc()


class AuthContext:
    """Context for auth operation metric recording."""

    pass


def _classify_auth_error(error: Exception) -> str:
    """Classify an auth error into a result type."""
    error_str = str(error).lower()

    if "expired" in error_str or "expir" in error_str:
        return "expired_token"
    elif "invalid" in error_str or "credential" in error_str:
        return "invalid_credentials"
    else:
        return "error"


@contextmanager
def record_db_query(
    operation: str,
    table: str,
) -> None:
    """Context manager to record database query metrics.

    Args:
        operation: Query type (select, insert, update, delete)
        table: Database table name

    Example:
        with record_db_query("select", "costs"):
            results = db.query(CostModel).all()
    """
    start_time = time.perf_counter()

    try:
        yield
    except Exception as e:
        error_type = _classify_db_error(e)
        db_errors_counter.labels(
            error_type=error_type,
        ).inc()
        raise
    finally:
        duration = time.perf_counter() - start_time
        db_query_duration_histogram.labels(
            operation=operation,
            table=table,
        ).observe(duration)


def _classify_db_error(error: Exception) -> str:
    """Classify a DB error into an error type."""
    error_str = str(error).lower()

    if "connection" in error_str or "connect" in error_str:
        return "connection_error"
    elif "timeout" in error_str or "time out" in error_str:
        return "timeout"
    elif "constraint" in error_str or "unique" in error_str or "foreign key" in error_str:
        return "constraint_violation"
    elif "deadlock" in error_str:
        return "deadlock"
    else:
        return "other"


@contextmanager
def record_external_api_call(
    service: str,
    endpoint: str,
) -> "ExternalApiContext":
    """Context manager to record external API call metrics.

    Args:
        service: External service name (azure_graph, azure_cost, etc.)
        endpoint: API endpoint path (simplified)

    Example:
        with record_external_api_call("azure_graph", "/users") as ctx:
            response = requests.get(url)
            ctx.set_status_code(response.status_code)
    """
    ctx = ExternalApiContext(service, endpoint)
    start_time = time.perf_counter()

    try:
        yield ctx
    except Exception as e:
        error_type = "timeout" if "timeout" in str(e).lower() else "server_error"
        external_api_errors_counter.labels(
            service=service,
            error_type=error_type,
            status_code="0",
        ).inc()
        raise
    finally:
        duration = time.perf_counter() - start_time
        external_api_latency_histogram.labels(
            service=service,
            endpoint=endpoint,
        ).observe(duration)


class ExternalApiContext:
    """Context for external API call metric recording."""

    def __init__(self, service: str, endpoint: str) -> None:
        self.service = service
        self.endpoint = endpoint
        self._status_code: int | None = None

    def set_status_code(self, code: int) -> None:
        """Record the HTTP status code and classify any errors."""
        self._status_code = code

        if code >= 400:
            error_type = _classify_http_error(code)
            external_api_errors_counter.labels(
                service=self.service,
                error_type=error_type,
                status_code=str(code),
            ).inc()

        if code == 429:  # Rate limited
            rate_limit_hits_counter.labels(
                endpoint=self.endpoint,
                limit_type="unknown",
            ).inc()


def _classify_http_error(status_code: int) -> str:
    """Classify HTTP error code into error type."""
    if status_code == 401:
        return "auth_error"
    elif status_code == 403:
        return "auth_error"
    elif status_code == 429:
        return "rate_limit"
    elif status_code >= 500:
        return "server_error"
    else:
        return "client_error"


# =============================================================================
# Utility Functions
# =============================================================================


def record_cache_operation(
    backend: str,
    operation: str,
    result: str,
    count: int = 1,
) -> None:
    """Record a cache operation.

    Args:
        backend: Cache backend (redis, memory)
        operation: Operation type (get, set, delete)
        result: Operation result (hit, miss, success, error)
        count: Number of operations (default 1)
    """
    cache_operations_counter.labels(
        backend=backend,
        operation=operation,
        result=result,
    ).inc(count)


def record_compliance_score(
    tenant_id: str,
    framework: str,
    score: float,
) -> None:
    """Record compliance score metric.

    Args:
        tenant_id: Tenant identifier
        framework: Compliance framework (SOC2, ISO27001, etc.)
        score: Compliance score (0-100)
    """
    compliance_score_gauge.labels(
        tenant_id=tenant_id,
        framework=framework,
    ).set(score)


def record_token_operation(
    operation: str,
    token_type: str = "access_token",
) -> None:
    """Record a token operation.

    Args:
        operation: Token operation (issue, refresh, revoke, validate)
        token_type: Type of token (access_token, refresh_token)
    """
    token_operations_counter.labels(
        operation=operation,
        token_type=token_type,
    ).inc()


def update_app_info(version: str, environment: str) -> None:
    """Update application info metric.

    Args:
        version: Application version
        environment: Deployment environment (dev, staging, production)
    """
    app_info.info(
        {
            "version": version,
            "environment": environment,
        }
    )


def get_all_metrics() -> dict[str, Any]:
    """Get all metric definitions for documentation.

    Returns:
        Dictionary of all metrics with their descriptions
    """
    return {
        "sync": {
            "duration": "governance_sync_duration_seconds",
            "records": "governance_sync_records_total",
            "active": "governance_sync_active_jobs",
            "last_success": "governance_sync_last_success_timestamp",
        },
        "auth": {
            "latency": "governance_auth_latency_seconds",
            "attempts": "governance_auth_attempts_total",
            "sessions": "governance_auth_active_sessions",
            "tokens": "governance_token_operations_total",
        },
        "database": {
            "query_duration": "governance_db_query_duration_seconds",
            "connections": "governance_db_connections_active",
            "pool_size": "governance_db_pool_size",
            "errors": "governance_db_errors_total",
        },
        "cache": {
            "operations": "governance_cache_operations_total",
            "size": "governance_cache_size_bytes",
            "ttl": "governance_cache_ttl_seconds",
        },
        "external_api": {
            "latency": "governance_external_api_latency_seconds",
            "errors": "governance_external_api_errors_total",
            "rate_limit": "governance_external_api_rate_limit_remaining",
        },
        "business": {
            "compliance": "governance_compliance_score",
            "cost_anomalies": "governance_cost_anomalies_total",
            "recommendations": "governance_recommendations_generated_total",
        },
    }
