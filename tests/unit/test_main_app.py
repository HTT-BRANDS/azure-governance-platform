"""Unit tests for the main FastAPI application.

Tests app creation, middleware registration, route inclusion,
and health check endpoints in app/main.py.

Traces: SYS-001, SYS-002 — Application bootstrap, middleware chain,
router registration, and health endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked lifespan (no real DB/scheduler)."""
    from contextlib import asynccontextmanager

    from app.main import app

    # Override lifespan to skip real init
    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.router.lifespan_context = original_lifespan


# ---------------------------------------------------------------------------
# App Metadata
# ---------------------------------------------------------------------------


class TestAppMetadata:
    """Tests for FastAPI app metadata."""

    def test_app_title(self):
        from app.main import app

        assert app.title is not None
        assert len(app.title) > 0

    def test_app_version(self):
        from app.main import app

        assert app.version is not None

    def test_app_description(self):
        from app.main import app

        assert app.description is not None
        assert "governance" in app.description.lower()

    def test_app_description_has_no_commonmark_code_block_indent(self):
        """Regression guard for ncxl: Swagger UI markdown rendering.

        CommonMark treats lines with 4+ leading spaces as indented code blocks,
        which caused the entire description to render as monospaced preformatted
        text in Swagger UI (visible at docs/api/swagger/). The fix was to wrap
        the triple-quoted description with textwrap.dedent() to strip the common
        Python indent before FastAPI exports it into the OpenAPI spec.

        This test catches any future regression where someone re-adds indent.
        """
        from app.main import app

        assert app.description is not None
        offending = [
            (i, line)
            for i, line in enumerate(app.description.splitlines(), start=1)
            if line.startswith("    ")  # 4 spaces = CommonMark code block
        ]
        assert not offending, (
            f"Found {len(offending)} line(s) in app.description with 4+ leading "
            f"spaces. These will render as code blocks in Swagger UI. Wrap the "
            f"description in textwrap.dedent(...) before passing to FastAPI().\n"
            f"First offender: line {offending[0][0]}: {offending[0][1]!r}"
        )


# ---------------------------------------------------------------------------
# Health Endpoints
# ---------------------------------------------------------------------------


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_basic_health_check(self, client):
        """GET /health should return healthy status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_detailed_health_returns_200(self, client):
        """GET /health/detailed should return 200."""
        # SessionLocal is imported lazily inside the endpoint
        resp = client.get("/health/detailed")
        # Even if components are degraded, endpoint itself should respond
        assert resp.status_code == 200
        data = resp.json()
        assert "components" in data


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    def test_x_frame_options(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_options(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_xss_protection(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy(self, client):
        resp = client.get("/health")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client):
        resp = client.get("/health")
        pp = resp.headers.get("Permissions-Policy")
        assert pp is not None
        assert "camera=()" in pp

    def test_content_security_policy(self, client):
        resp = client.get("/health")
        csp = resp.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "nonce-" in csp


# ---------------------------------------------------------------------------
# Route Registration
# ---------------------------------------------------------------------------


class TestRouteRegistration:
    """Tests that routers are included in the app."""

    def test_has_health_route(self):
        from app.main import app

        paths = [r.path for r in app.routes]
        assert "/health" in paths

    def test_has_metrics_route(self):
        from app.main import app

        paths = [r.path for r in app.routes]
        assert "/metrics" in paths


# ---------------------------------------------------------------------------
# Root Redirect
# ---------------------------------------------------------------------------


class TestRootRedirect:
    """Tests for the root endpoint redirect."""

    def test_root_without_token_returns_redirect_or_401(self, client):
        """Root without auth token should redirect to /login or return 401.

        The auth exception handler converts 401 to a login redirect for
        browser requests, but in test client context (Accept: */*)
        it may return 401 JSON response or 302 depending on middleware order.
        """
        resp = client.get("/", follow_redirects=False)
        # Both behaviors are acceptable depending on middleware ordering
        assert resp.status_code in (302, 307, 401)
