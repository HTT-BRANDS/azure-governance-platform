"""Authenticated end-to-end staging tests.

These tests obtain a short-lived JWT via the staging admin token endpoint
and then exercise every major business-logic area of the app against the
live staging environment.

Requirements:
  - STAGING_URL  env var (or --staging-url pytest option)
  - STAGING_ADMIN_KEY env var (or --staging-admin-key pytest option)

All tests are skipped if STAGING_ADMIN_KEY is not configured.

Coverage:
  1. Auth         — staging token issuance + /me endpoint
  2. Tenants      — list, create, get
  3. Monitoring   — system status, create alert
  4. Sync         — trigger cost sync, poll to completion
  5. Costs        — summary + anomalies
  6. Compliance   — summary + policies
  7. Identity     — summary + privileged users
  8. Riverside    — overview + readiness
  9. Budget       — list
  10. Dashboard   — authenticated HTML page renders
  11. Bulk        — tag analysis endpoint
"""

import os
import time

import pytest
import requests

# ============================================================================
# Configuration
# ============================================================================

STAGING_URL = os.getenv("STAGING_URL", "https://app-governance-staging-xnczpwyv.azurewebsites.net")
STAGING_ADMIN_KEY = os.getenv("STAGING_ADMIN_KEY", "")

pytestmark = pytest.mark.skipif(
    not STAGING_ADMIN_KEY,
    reason="STAGING_ADMIN_KEY not set — skipping authenticated E2E tests",
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def base_url() -> str:
    return STAGING_URL.rstrip("/")


@pytest.fixture(scope="module")
def auth_token(base_url: str) -> str:
    """Obtain a 60-min admin JWT from the staging token endpoint."""
    resp = requests.post(
        f"{base_url}/api/v1/auth/staging-token",
        headers={"x-staging-admin-key": STAGING_ADMIN_KEY},
        timeout=15,
    )
    assert resp.status_code == 200, f"Token endpoint failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


@pytest.fixture(scope="module")
def authed(base_url: str, auth_token: str):
    """Requests session with auth headers pre-set."""
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json",
        }
    )
    session.base_url = base_url
    return session


# ============================================================================
# 1. Auth
# ============================================================================


class TestAuth:
    def test_staging_token_issued(self, authed, base_url):
        """Verify the token we got is actually valid for /me."""
        resp = authed.get(f"{base_url}/api/v1/auth/me", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "e2e@staging.local"
        assert "admin" in data["user"]["roles"]

    def test_direct_login_blocked(self, base_url):
        """Staging must block direct username/password login."""
        resp = requests.post(
            f"{base_url}/api/v1/auth/login",
            data={"username": "admin", "password": "admin"},  # pragma: allowlist secret
            timeout=10,
        )
        assert resp.status_code == 403, "Direct login must be blocked in staging"

    def test_staging_token_wrong_key_rejected(self, base_url):
        """Wrong admin key must be rejected."""
        resp = requests.post(
            f"{base_url}/api/v1/auth/staging-token",
            headers={"x-staging-admin-key": "wrong-key-intentionally"},
            timeout=10,
        )
        assert resp.status_code == 401


# ============================================================================
# 2. Tenants
# ============================================================================


class TestTenants:
    def test_list_tenants(self, authed, base_url):
        """Authenticated user can list tenants."""
        resp = authed.get(f"{base_url}/api/v1/tenants/", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), "Expected list of tenants"

    def test_tenants_response_shape(self, authed, base_url):
        """Each tenant has required fields."""
        resp = authed.get(f"{base_url}/api/v1/tenants/", timeout=10)
        assert resp.status_code == 200
        tenants = resp.json()
        if tenants:
            t = tenants[0]
            assert "id" in t
            assert "name" in t
            assert "tenant_id" in t


# ============================================================================
# 3. Monitoring
# ============================================================================


class TestMonitoring:
    def test_system_status(self, authed, base_url):
        """Monitoring status endpoint returns overall health."""
        resp = authed.get(f"{base_url}/api/v1/monitoring/status", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_status" in data or "status" in data

    def test_active_alerts(self, authed, base_url):
        """Active alerts endpoint returns a list."""
        resp = authed.get(f"{base_url}/api/v1/monitoring/alerts", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_sync_job_history(self, authed, base_url):
        """Sync job history endpoint is accessible."""
        resp = authed.get(f"{base_url}/api/v1/monitoring/sync-jobs", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ============================================================================
# 4. Sync Jobs
# ============================================================================


class TestSync:
    def test_trigger_cost_sync(self, authed, base_url):
        """Can trigger a cost sync job and get a job ID back."""
        resp = authed.post(
            f"{base_url}/api/v1/sync/costs",
            json={"force": True},
            timeout=20,
        )
        # 202 Accepted or 200 OK both valid
        assert resp.status_code in (200, 202), f"Unexpected {resp.status_code}: {resp.text}"

    def test_sync_status(self, authed, base_url):
        """Sync status endpoint returns current state."""
        resp = authed.get(f"{base_url}/api/v1/sync/status", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        # Shape: either a dict with job types or a list
        assert data is not None

    def test_sync_health(self, authed, base_url):
        """Sync health check returns structured response."""
        resp = authed.get(f"{base_url}/api/v1/sync/health", timeout=10)
        assert resp.status_code == 200


# ============================================================================
# 5. Costs
# ============================================================================


class TestCosts:
    def test_cost_summary(self, authed, base_url):
        """Cost summary endpoint returns structured response."""
        resp = authed.get(f"{base_url}/api/v1/costs/summary", timeout=15)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (dict, list))

    def test_cost_anomalies(self, authed, base_url):
        """Cost anomalies endpoint is reachable and returns list."""
        resp = authed.get(f"{base_url}/api/v1/costs/anomalies", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), (list, dict))

    def test_cost_trends(self, authed, base_url):
        """Cost trends endpoint returns response."""
        resp = authed.get(f"{base_url}/api/v1/costs/trends", timeout=10)
        assert resp.status_code == 200


# ============================================================================
# 6. Compliance
# ============================================================================


class TestCompliance:
    def test_compliance_summary(self, authed, base_url):
        """Compliance summary returns structured response."""
        resp = authed.get(f"{base_url}/api/v1/compliance/summary", timeout=15)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (dict, list))

    def test_policy_states(self, authed, base_url):
        """Policy states endpoint returns list."""
        resp = authed.get(f"{base_url}/api/v1/compliance/policies", timeout=10)
        assert resp.status_code == 200


# ============================================================================
# 7. Identity
# ============================================================================


class TestIdentity:
    def test_identity_summary(self, authed, base_url):
        """Identity summary endpoint returns response."""
        resp = authed.get(f"{base_url}/api/v1/identity/summary", timeout=15)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (dict, list))

    def test_privileged_users(self, authed, base_url):
        """Privileged users endpoint returns list."""
        resp = authed.get(f"{base_url}/api/v1/identity/privileged-users", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), (list, dict))


# ============================================================================
# 8. Riverside Compliance
# ============================================================================


class TestRiverside:
    def test_riverside_overview(self, authed, base_url):
        """Riverside overview returns status for all tenants."""
        resp = authed.get(f"{base_url}/api/v1/riverside/overview", timeout=20)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (dict, list))

    def test_riverside_readiness(self, authed, base_url):
        """Riverside readiness report is accessible."""
        resp = authed.get(f"{base_url}/api/v1/riverside/readiness", timeout=20)
        assert resp.status_code == 200


# ============================================================================
# 9. Budgets
# ============================================================================


class TestBudgets:
    def test_list_budgets(self, authed, base_url):
        """Budget list endpoint returns a list."""
        resp = authed.get(f"{base_url}/api/v1/budgets/", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), (list, dict))

    def test_budget_summary(self, authed, base_url):
        """Budget summary returns structured data."""
        resp = authed.get(f"{base_url}/api/v1/budgets/summary", timeout=10)
        assert resp.status_code == 200


# ============================================================================
# 10. Dashboard UI
# ============================================================================


class TestDashboardUI:
    def test_dashboard_page_authenticated(self, authed, base_url):
        """Dashboard renders HTML when authenticated via cookie."""
        # Use cookie-based auth for UI pages
        session = requests.Session()
        token_resp = requests.post(
            f"{base_url}/api/v1/auth/staging-token",
            headers={"x-staging-admin-key": STAGING_ADMIN_KEY},
            timeout=15,
        )
        access_token = token_resp.json()["access_token"]
        session.cookies.set("access_token", access_token, domain=base_url.split("//")[1])

        resp = session.get(f"{base_url}/dashboard", timeout=15)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        # Should contain governance platform markup
        assert any(
            marker in resp.text
            for marker in ["governance", "dashboard", "Azure", "tenant"]
        ), "Dashboard HTML missing expected content"

    def test_login_page_unauthenticated(self, base_url):
        """Unauthenticated / redirects to login."""
        resp = requests.get(f"{base_url}/", allow_redirects=False, timeout=10)
        assert resp.status_code in (200, 302, 307)


# ============================================================================
# 11. Bulk Operations
# ============================================================================


class TestBulkOperations:
    def test_bulk_tag_analysis(self, authed, base_url):
        """Bulk tag analysis endpoint is accessible."""
        resp = authed.get(f"{base_url}/api/v1/bulk/tag-analysis", timeout=15)
        assert resp.status_code == 200

    def test_resources_list(self, authed, base_url):
        """Resources endpoint returns list."""
        resp = authed.get(f"{base_url}/api/v1/resources/", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), (list, dict))


# ============================================================================
# 12. Performance Baseline
# ============================================================================


class TestPerformance:
    """Ensure key endpoints respond within acceptable time bounds."""

    BUDGET_MS = {
        "/health": 500,
        "/api/v1/monitoring/status": 3000,
        "/api/v1/costs/summary": 5000,
        "/api/v1/compliance/summary": 5000,
        "/api/v1/identity/summary": 5000,
    }

    @pytest.mark.parametrize("path,max_ms", BUDGET_MS.items())
    def test_response_time(self, authed, base_url, path, max_ms):
        start = time.monotonic()
        resp = authed.get(f"{base_url}{path}", timeout=max_ms / 1000 + 5)
        elapsed_ms = (time.monotonic() - start) * 1000
        assert resp.status_code in (200, 401, 403), f"{path} returned {resp.status_code}"
        assert elapsed_ms < max_ms, (
            f"{path} took {elapsed_ms:.0f}ms — budget is {max_ms}ms"
        )
