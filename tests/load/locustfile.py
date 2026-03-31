"""Load tests for Azure Governance Platform (NF-P03).

Validates that the platform can handle 50+ concurrent users
with API response times under 500ms (cached).

Usage:
    # Interactive mode (opens web UI at http://localhost:8089)
    uv run locust -f tests/load/locustfile.py --host http://localhost:8000

    # Headless mode (CI-friendly)
    uv run locust -f tests/load/locustfile.py \\
        --host http://localhost:8000 \\
        --headless \\
        --users 60 \\
        --spawn-rate 10 \\
        --run-time 60s \\
        --csv tests/load/results

    # Quick smoke (30 seconds, 50 users)
    uv run locust -f tests/load/locustfile.py \\
        --host http://localhost:8000 \\
        --headless \\
        --users 50 \\
        --spawn-rate 10 \\
        --run-time 30s

    # Auth-focused load test
    uv run locust -f tests/load/locustfile.py \\
        --host http://localhost:8000 \\
        --headless \\
        --class-picker AuthLoadUser \\
        --users 30 \\
        --run-time 60s

    # Sync-focused load test
    uv run locust -f tests/load/locustfile.py \\
        --host http://localhost:8000 \\
        --headless \\
        --class-picker SyncLoadUser \\
        --users 20 \\
        --run-time 60s

Traces: NF-P03 (Support 50+ concurrent users)
"""

import os
import time
from datetime import UTC, datetime
from typing import Any

from locust import HttpUser, between, events, task


class GovernanceAPIUser(HttpUser):
    """Simulates a typical governance platform user.

    Mixes read-heavy API calls that reflect real usage patterns:
    - Health check (lightweight, frequent)
    - Cost endpoints (dashboard-heavy)
    - Compliance endpoints (regular checks)
    - Resource endpoints (inventory browsing)
    - Identity endpoints (occasional lookups)
    """

    # Wait between 1-3 seconds between tasks (realistic user behavior)
    wait_time = between(1, 3)

    def on_start(self):
        """Authenticate and store token for subsequent requests."""
        self._authenticate()

    def _authenticate(self):
        """Get authentication token from staging endpoint or env var."""
        staging_token_url = "/api/v1/auth/staging-token"
        try:
            resp = self.client.post(
                staging_token_url,
                json={"purpose": "load-test"},
                timeout=10,
            )
            if resp.status_code == 200:
                token = resp.json().get("access_token", "")
                self.client.headers.update({"Authorization": f"Bearer {token}"})
                return
        except Exception:
            pass

        # Fallback: use env var token
        token = os.environ.get("LOAD_TEST_TOKEN", "")
        if token:
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    # ---- Health (10% of traffic) ----

    @task(2)
    def health_check(self):
        """GET /health — lightweight liveness probe."""
        self.client.get("/health", name="/health")

    @task(1)
    def metrics(self):
        """GET /metrics — Prometheus metrics endpoint."""
        self.client.get("/metrics", name="/metrics")

    # ---- Cost Management (30% of traffic) ----

    @task(4)
    def cost_summary(self):
        """GET /api/v1/costs/summary — main dashboard widget."""
        self.client.get("/api/v1/costs/summary", name="/api/v1/costs/summary")

    @task(3)
    def cost_trends(self):
        """GET /api/v1/costs/trends — cost trending chart."""
        self.client.get("/api/v1/costs/trends", name="/api/v1/costs/trends")

    @task(2)
    def cost_anomalies(self):
        """GET /api/v1/costs/anomalies — anomaly detection."""
        self.client.get("/api/v1/costs/anomalies", name="/api/v1/costs/anomalies")

    # ---- Compliance (25% of traffic) ----

    @task(3)
    def compliance_summary(self):
        """GET /api/v1/compliance/summary — compliance dashboard."""
        self.client.get("/api/v1/compliance/summary", name="/api/v1/compliance/summary")

    @task(2)
    def compliance_frameworks(self):
        """GET /api/v1/compliance/frameworks — framework listing."""
        self.client.get("/api/v1/compliance/frameworks", name="/api/v1/compliance/frameworks")

    # ---- Resources (20% of traffic) ----

    @task(3)
    def resource_inventory(self):
        """GET /api/v1/resources/inventory — resource listing."""
        self.client.get("/api/v1/resources/inventory", name="/api/v1/resources/inventory")

    @task(1)
    def resource_quotas(self):
        """GET /api/v1/resources/quotas/summary — quota monitoring."""
        self.client.get(
            "/api/v1/resources/quotas/summary",
            name="/api/v1/resources/quotas/summary",
        )

    # ---- Identity (10% of traffic) ----

    @task(2)
    def identity_summary(self):
        """GET /api/v1/identity/summary — identity dashboard."""
        self.client.get("/api/v1/identity/summary", name="/api/v1/identity/summary")

    # ---- Recommendations (5% of traffic) ----

    @task(1)
    def recommendations(self):
        """GET /api/v1/recommendations — optimization suggestions."""
        self.client.get("/api/v1/recommendations", name="/api/v1/recommendations")


class AuthLoadUser(HttpUser):
    """Simulates authentication-heavy usage patterns.

    Tests auth endpoints including:
    - Login flows
    - Token refresh
    - Token validation
    - Logout
    """

    wait_time = between(2, 5)

    def on_start(self):
        """Initialize auth state tracking."""
        self.auth_token = None
        self.refresh_token = None
        self.token_expiry = None

    @task(5)
    def staging_token_login(self):
        """POST /api/v1/auth/staging-token — development login."""
        with self.client.post(
            "/api/v1/auth/staging-token",
            json={"purpose": "load-test"},
            name="/api/v1/auth/staging-token",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.auth_token = data.get("access_token")
                self.token_expiry = data.get("expires_at")
                if self.auth_token:
                    self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    resp.success()
                else:
                    resp.failure("No access_token in response")
            else:
                resp.failure(f"Auth failed: {resp.status_code}")

    @task(3)
    def validate_token(self):
        """GET /api/v1/auth/validate — verify token validity."""
        if not self.auth_token:
            return  # Skip if not authenticated
        self.client.get(
            "/api/v1/auth/validate",
            name="/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {self.auth_token}"},
        )

    @task(2)
    def get_user_info(self):
        """GET /api/v1/auth/me — get current user info."""
        if not self.auth_token:
            return
        self.client.get(
            "/api/v1/auth/me",
            name="/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.auth_token}"},
        )

    @task(1)
    def logout(self):
        """POST /api/v1/auth/logout — end session."""
        if not self.auth_token:
            return
        self.client.post(
            "/api/v1/auth/logout",
            name="/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {self.auth_token}"},
        )
        self.auth_token = None
        self.client.headers.pop("Authorization", None)


class SyncLoadUser(HttpUser):
    """Simulates sync operation load patterns.

    Tests sync endpoints for:
    - Job status monitoring
    - Sync triggering
    - Status polling
    """

    wait_time = between(3, 8)

    def on_start(self):
        """Authenticate for sync operations."""
        token = os.environ.get("LOAD_TEST_TOKEN", "")
        staging_token_url = "/api/v1/auth/staging-token"
        try:
            resp = self.client.post(
                staging_token_url,
                json={"purpose": "load-test-sync"},
                timeout=10,
            )
            if resp.status_code == 200:
                token = resp.json().get("access_token", "")
        except Exception:
            pass
        if token:
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(4)
    def sync_status(self):
        """GET /api/v1/sync/status — check sync job status."""
        self.client.get("/api/v1/sync/status", name="/api/v1/sync/status")

    @task(3)
    def sync_history(self):
        """GET /api/v1/sync/history — list recent sync jobs."""
        self.client.get(
            "/api/v1/sync/history",
            name="/api/v1/sync/history",
            params={"limit": 10},
        )

    @task(2)
    def sync_metrics(self):
        """GET /api/v1/sync/metrics — sync performance metrics."""
        self.client.get("/api/v1/sync/metrics", name="/api/v1/sync/metrics")

    @task(1)
    def trigger_sync(self):
        """POST /api/v1/sync/trigger — start a sync job."""
        with self.client.post(
            "/api/v1/sync/trigger",
            name="/api/v1/sync/trigger",
            json={
                "resource_types": ["costs", "compliance", "resources"],
                "force_refresh": False,
            },
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 202, 409):  # 409 = sync already running
                resp.success()

    @task(1)
    def sync_health(self):
        """GET /api/v1/sync/health — sync system health."""
        self.client.get("/api/v1/sync/health", name="/api/v1/sync/health")


class MixedLoadUser(GovernanceAPIUser, AuthLoadUser, SyncLoadUser):
    """Combined load user that exercises all endpoint types.

    Weighted to reflect production traffic patterns:
    - 70% standard API calls (GovernanceAPIUser)
    - 20% auth operations (AuthLoadUser)
    - 10% sync operations (SyncLoadUser)
    """

    wait_time = between(1, 4)

    # Task weights from parent classes will be combined
    # Higher weight = more frequent execution


# ---- Event Hooks for CI Assertions ----

# SLA Configuration
SLA_P95_MAX_MS = int(os.environ.get("LOAD_TEST_P95_MAX_MS", "500"))  # Default: 500ms for p95
SLA_P99_MAX_MS = int(os.environ.get("LOAD_TEST_P99_MAX_MS", "1000"))  # Default: 1s for p99
SLA_ERROR_RATE_MAX_PCT = float(os.environ.get("LOAD_TEST_ERROR_RATE_MAX", "1.0"))  # Default: 1%
SLA_MIN_REQUESTS = int(os.environ.get("LOAD_TEST_MIN_REQUESTS", "100"))


def log_sla_violation(
    metric: str,
    actual: float,
    threshold: float,
    is_error: bool = True,
) -> str:
    """Format an SLA violation message.

    Args:
        metric: Name of the metric that violated SLA
        actual: Actual value observed
        threshold: Maximum allowed value
        is_error: True if this is an error condition

    Returns:
        Formatted violation message
    """
    status = "❌ FAILED" if is_error else "⚠️  WARNING"
    return f"{status}: SLA violation - {metric}: {actual:.2f} > {threshold:.2f}"


@events.request.add_listener
def on_request(
    request_type: str,
    name: str,
    response_time: float,
    response_length: int,
    context: dict[str, Any] | None,
    exception: Exception | None,
    **kwargs: Any,
) -> None:
    """Track request metrics for per-endpoint SLA checking.

    Logs slow requests for debugging.
    """
    # Log slow requests (over 1 second)
    if response_time > 1000 and exception is None:
        timestamp = datetime.now(UTC).isoformat()
        print(f"[SLOW REQUEST] {timestamp} - {name}: {response_time:.0f}ms")


@events.quitting.add_listener
def assert_response_times(environment, **_kwargs):
    """Fail the load test if response times exceed SLA thresholds.

    NF-P02: API response time < 500ms (cached)
    NF-P03: Support 50+ concurrent users
    NF-R05: Error rate < 1%

    Environment variables for SLA configuration:
        LOAD_TEST_P95_MAX_MS: Maximum p95 response time (default: 500)
        LOAD_TEST_P99_MAX_MS: Maximum p99 response time (default: 1000)
        LOAD_TEST_ERROR_RATE_MAX: Maximum error rate % (default: 1.0)
        LOAD_TEST_MIN_REQUESTS: Minimum requests required (default: 100)
    """
    stats = environment.stats
    total = stats.total
    start_time = time.time()

    print("\n" + "=" * 70)
    print("LOAD TEST SLA REPORT")
    print("=" * 70)

    # Check minimum requests
    if total.num_requests < SLA_MIN_REQUESTS:
        environment.process_exit_code = 1
        print(f"❌ LOAD TEST FAILED: Only {total.num_requests} requests made")
        print(f"   Minimum required: {SLA_MIN_REQUESTS}")
        return

    # Calculate percentiles
    p50 = total.get_response_time_percentile(0.5) or 0
    p75 = total.get_response_time_percentile(0.75) or 0
    p95 = total.get_response_time_percentile(0.95) or 0
    p99 = total.get_response_time_percentile(0.99) or 0
    error_rate = (total.num_failures / total.num_requests) * 100 if total.num_requests > 0 else 0

    # Print detailed report
    print("\n📊 REQUEST STATISTICS")
    print(f"   Total requests:  {total.num_requests:,}")
    print(f"   Failed requests: {total.num_failures:,}")
    print(f"   Error rate:      {error_rate:.2f}%")
    print("\n⏱️  RESPONSE TIMES")
    print(f"   p50 (median):    {p50:.0f}ms")
    print(f"   p75:             {p75:.0f}ms")
    print(f"   p95:             {p95:.0f}ms")
    print(f"   p99:             {p99:.0f}ms")
    print(f"   Max:             {total.max_response_time:.0f}ms")
    print(f"   Min:             {total.min_response_time:.0f}ms")
    print(f"   Avg:             {total.avg_response_time:.0f}ms")
    print("\n📋 SLA THRESHOLDS")
    print(f"   p95 max:         {SLA_P95_MAX_MS}ms")
    print(f"   p99 max:         {SLA_P99_MAX_MS}ms")
    print(f"   Error rate max:  {SLA_ERROR_RATE_MAX_PCT}%")

    # Per-endpoint statistics for slow endpoints
    print(f"\n🔍 PER-ENDPOINT P95 (> {SLA_P95_MAX_MS}ms threshold):")
    slow_endpoints = []
    for name, stats_entry in environment.stats.entries.items():
        if stats_entry.num_requests > 0:
            endpoint_p95 = stats_entry.get_response_time_percentile(0.95) or 0
            endpoint_error_rate = (
                (stats_entry.num_failures / stats_entry.num_requests) * 100
                if stats_entry.num_requests > 0
                else 0
            )
            if endpoint_p95 > SLA_P95_MAX_MS or endpoint_error_rate > SLA_ERROR_RATE_MAX_PCT:
                slow_endpoints.append(
                    (
                        name,
                        endpoint_p95,
                        stats_entry.num_requests,
                        endpoint_error_rate,
                    )
                )

    if slow_endpoints:
        for name, endpoint_p95, count, err_rate in sorted(
            slow_endpoints, key=lambda x: x[1], reverse=True
        )[:10]:  # Show top 10
            print(f"   {name}: p95={endpoint_p95:.0f}ms, errors={err_rate:.1f}%, n={count}")
    else:
        print("   All endpoints within SLA ✓")

    # SLA Checks
    print("\n✅ SLA CHECKS")
    all_passed = True

    # Check p95
    if p95 > SLA_P95_MAX_MS:
        print(log_sla_violation("p95 response time", p95, SLA_P95_MAX_MS))
        all_passed = False
    else:
        print(f"   ✓ p95: {p95:.0f}ms <= {SLA_P95_MAX_MS}ms")

    # Check p99 (warning only, not failure)
    if p99 > SLA_P99_MAX_MS:
        print(log_sla_violation("p99 response time", p99, SLA_P99_MAX_MS, is_error=False))
    else:
        print(f"   ✓ p99: {p99:.0f}ms <= {SLA_P99_MAX_MS}ms")

    # Check error rate
    if error_rate > SLA_ERROR_RATE_MAX_PCT:
        print(log_sla_violation("Error rate", error_rate, SLA_ERROR_RATE_MAX_PCT))
        all_passed = False
    else:
        print(f"   ✓ Error rate: {error_rate:.2f}% <= {SLA_ERROR_RATE_MAX_PCT}%")

    print("=" * 70)

    if all_passed:
        duration = time.time() - start_time
        print(f"✅ LOAD TEST PASSED in {duration:.1f}s")
        environment.process_exit_code = 0
    else:
        print("❌ LOAD TEST FAILED")
        environment.process_exit_code = 1


@events.test_start.add_listener
def on_test_start(environment, **_kwargs):
    """Log test start information."""
    print("\n" + "=" * 70)
    print("LOAD TEST STARTED")
    print("=" * 70)
    print(f"Host: {environment.host}")
    print(f"Target: {environment.target_weight or 'all users'}")
    print(f"SLA - p95 max: {SLA_P95_MAX_MS}ms")
    print(f"SLA - p99 max: {SLA_P99_MAX_MS}ms")
    print(f"SLA - Error rate max: {SLA_ERROR_RATE_MAX_PCT}%")
    print(f"SLA - Min requests: {SLA_MIN_REQUESTS}")
    print("=" * 70 + "\n")
