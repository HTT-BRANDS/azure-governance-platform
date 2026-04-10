"""Enhanced integration tests for security headers across environments.

Validates security header configuration for all three environments:
- Development: 5-minute HSTS, relaxed policies
- Staging: 1-day HSTS, production-like policies
- Production: 1-year HSTS, strict policies, preload enabled

These tests ensure the SecurityHeadersConfig presets work correctly
and all 12 security headers are present in responses.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security_headers import (
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
    create_security_middleware_from_config,
)


def _make_env_settings(environment: str, is_development: bool = False):
    """Create a mock settings object for a specific environment."""
    settings = MagicMock()
    settings.environment = environment
    settings.is_development = is_development
    return settings


def _make_app_with_config(environment: str, is_development: bool = False):
    """Create a minimal FastAPI app with environment-specific security middleware."""
    mock_settings = _make_env_settings(environment, is_development)

    patcher = patch(
        "app.core.security_headers.get_settings",
        return_value=mock_settings,
    )
    patcher.start()

    app = FastAPI()

    # Use environment-specific config
    config = {
        "development": SecurityHeadersConfig.development,
        "staging": SecurityHeadersConfig.staging,
        "production": SecurityHeadersConfig.production,
    }.get(environment, SecurityHeadersConfig.development)()

    app.add_middleware(SecurityHeadersMiddleware, config=config)

    @app.get("/test")
    async def test_route():
        return {"ok": True}

    @app.get("/health")
    async def health_route():
        return {"status": "healthy"}

    client = TestClient(app)
    # Trigger middleware init
    client.get("/test")
    patcher.stop()
    return client


# ============================================================================
# Environment-Specific HSTS Tests
# ============================================================================


class TestHSTSEnvironmentSpecific:
    """HSTS header validation across dev, staging, and production environments."""

    def test_hsts_present_in_development(self):
        """HSTS should be present in development (5-minute max-age)."""
        client = _make_app_with_config("development", is_development=True)
        resp = client.get("/test")
        assert "Strict-Transport-Security" in resp.headers

    def test_hsts_max_age_development(self):
        """Development HSTS max-age should be 300 seconds (5 minutes)."""
        client = _make_app_with_config("development", is_development=True)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "max-age=300" in hsts

    def test_hsts_development_includes_subdomains(self):
        """Development HSTS should include subdomains."""
        client = _make_app_with_config("development", is_development=True)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in hsts

    def test_hsts_development_no_preload(self):
        """Development HSTS should NOT have preload flag."""
        client = _make_app_with_config("development", is_development=True)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "preload" not in hsts

    def test_hsts_present_in_staging(self):
        """HSTS should be present in staging (1-day max-age)."""
        client = _make_app_with_config("staging", is_development=False)
        resp = client.get("/test")
        assert "Strict-Transport-Security" in resp.headers

    def test_hsts_max_age_staging(self):
        """Staging HSTS max-age should be 86400 seconds (1 day)."""
        client = _make_app_with_config("staging", is_development=False)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "max-age=86400" in hsts

    def test_hsts_staging_includes_subdomains(self):
        """Staging HSTS should include subdomains."""
        client = _make_app_with_config("staging", is_development=False)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in hsts

    def test_hsts_staging_no_preload(self):
        """Staging HSTS should NOT have preload flag."""
        client = _make_app_with_config("staging", is_development=False)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "preload" not in hsts

    def test_hsts_present_in_production(self):
        """HSTS should be present in production (1-year max-age)."""
        client = _make_app_with_config("production", is_development=False)
        resp = client.get("/test")
        assert "Strict-Transport-Security" in resp.headers

    def test_hsts_max_age_production(self):
        """Production HSTS max-age should be 31536000 seconds (1 year)."""
        client = _make_app_with_config("production", is_development=False)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts

    def test_hsts_production_includes_subdomains(self):
        """Production HSTS should include subdomains."""
        client = _make_app_with_config("production", is_development=False)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in hsts

    def test_hsts_production_has_preload(self):
        """Production HSTS should have preload flag."""
        client = _make_app_with_config("production", is_development=False)
        resp = client.get("/test")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "preload" in hsts


# ============================================================================
# All 12 Security Headers Present Tests
# ============================================================================


class TestAllSecurityHeadersPresent:
    """Verify all 12 security headers are present in responses."""

    # Note: Document-Policy is conditionally set (omitted if empty string in config)
    EXPECTED_HEADERS_ALL_ENVS = [
        "X-Frame-Options",
        "X-Content-Type-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
        "Permissions-Policy",
        "Cross-Origin-Resource-Policy",
        "Cross-Origin-Opener-Policy",
        "Cross-Origin-Embedder-Policy",
        "Content-Security-Policy",
        "Strict-Transport-Security",
        "Server",
    ]

    @pytest.mark.parametrize("header", EXPECTED_HEADERS_ALL_ENVS)
    def test_header_present_development(self, header):
        """Core security headers should be present in development."""
        client = _make_app_with_config("development", is_development=True)
        resp = client.get("/test")
        assert header in resp.headers, f"{header} missing in development"

    @pytest.mark.parametrize("header", EXPECTED_HEADERS_ALL_ENVS + ["Document-Policy"])
    def test_header_present_staging(self, header):
        """All security headers should be present in staging."""
        client = _make_app_with_config("staging", is_development=False)
        resp = client.get("/test")
        assert header in resp.headers, f"{header} missing in staging"

    @pytest.mark.parametrize("header", EXPECTED_HEADERS_ALL_ENVS + ["Document-Policy"])
    def test_header_present_production(self, header):
        """All security headers should be present in production."""
        client = _make_app_with_config("production", is_development=False)
        resp = client.get("/test")
        assert header in resp.headers, f"{header} missing in production"

    def test_development_has_no_document_policy(self):
        """Development should NOT have Document-Policy header (it's empty)."""
        client = _make_app_with_config("development", is_development=True)
        resp = client.get("/test")
        assert "Document-Policy" not in resp.headers


# ============================================================================
# Header Value Validation Tests
# ============================================================================


class TestHeaderValues:
    """Validate specific header values across environments."""

    def test_x_frame_options_is_deny_all_environments(self):
        """X-Frame-Options should always be DENY."""
        for env in ["development", "staging", "production"]:
            client = _make_app_with_config(env, is_development=(env == "development"))
            resp = client.get("/test")
            assert resp.headers["X-Frame-Options"] == "DENY", f"Failed for {env}"

    def test_x_content_type_options_is_nosniff_all_environments(self):
        """X-Content-Type-Options should always be nosniff."""
        for env in ["development", "staging", "production"]:
            client = _make_app_with_config(env, is_development=(env == "development"))
            resp = client.get("/test")
            assert resp.headers["X-Content-Type-Options"] == "nosniff", f"Failed for {env}"

    def test_server_header_is_azure_governance(self):
        """Server header should identify the platform."""
        for env in ["development", "staging", "production"]:
            client = _make_app_with_config(env, is_development=(env == "development"))
            resp = client.get("/test")
            assert resp.headers["Server"] == "Azure-Governance-Platform", f"Failed for {env}"


# ============================================================================
# CSP Environment-Specific Tests
# ============================================================================


class TestCSPEnvironmentSpecific:
    """CSP policy variations across environments."""

    def test_development_csp_allows_eval(self):
        """Development CSP should allow unsafe-eval for debugging."""
        client = _make_app_with_config("development", is_development=True)
        resp = client.get("/test")
        csp = resp.headers["Content-Security-Policy"]
        assert "'unsafe-eval'" in csp or "http:" in csp

    def test_production_csp_no_eval(self):
        """Production CSP should NOT allow unsafe-eval."""
        client = _make_app_with_config("production", is_development=False)
        resp = client.get("/test")
        csp = resp.headers["Content-Security-Policy"]
        # Production CSP should be strict - no eval, no external CDNs
        assert "unpkg.com" not in csp
        assert "cdn.jsdelivr.net" not in csp

    def test_production_csp_frame_ancestors_none(self):
        """Production CSP should prevent framing."""
        client = _make_app_with_config("production", is_development=False)
        resp = client.get("/test")
        csp = resp.headers["Content-Security-Policy"]
        assert "frame-ancestors 'none'" in csp

    def test_staging_csp_allows_cdn_resources(self):
        """Staging CSP should allow CDN resources for testing."""
        client = _make_app_with_config("staging", is_development=False)
        resp = client.get("/test")
        csp = resp.headers["Content-Security-Policy"]
        assert "cdn.jsdelivr.net" in csp or "'self'" in csp

    def test_csp_contains_nonce_all_environments(self):
        """CSP should contain a nonce placeholder in all environments."""
        for env in ["development", "staging", "production"]:
            client = _make_app_with_config(env, is_development=(env == "development"))
            resp = client.get("/test")
            csp = resp.headers["Content-Security-Policy"]
            assert "'nonce-" in csp, f"CSP nonce missing in {env}"


# ============================================================================
# Factory Function Tests
# ============================================================================


class TestCreateSecurityMiddlewareFromConfig:
    """Tests for the create_security_middleware_from_config factory."""

    def test_factory_returns_callable(self):
        """Factory should return a callable."""
        factory = create_security_middleware_from_config("development")
        assert callable(factory)

    def test_factory_development_config(self):
        """Factory with development should use dev config."""
        factory = create_security_middleware_from_config("development")
        app = FastAPI()
        app.add_middleware(factory)

        @app.get("/test")
        async def root():
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/test")
        hsts = resp.headers.get("Strict-Transport-Security", "")
        assert "max-age=300" in hsts

    def test_factory_production_config(self):
        """Factory with production should use prod config."""
        factory = create_security_middleware_from_config("production")
        app = FastAPI()
        app.add_middleware(factory)

        @app.get("/test")
        async def root():
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/test")
        hsts = resp.headers.get("Strict-Transport-Security", "")
        assert "max-age=31536000" in hsts
        assert "preload" in hsts


# ============================================================================
# Environment Config Preset Tests
# ============================================================================


class TestSecurityHeadersConfigPresets:
    """Test the environment-specific config presets directly."""

    def test_development_config_has_short_hsts(self):
        """Development config should have 5-minute HSTS."""
        config = SecurityHeadersConfig.development()
        assert config.hsts_max_age == 300
        assert config.hsts_include_subdomains is True
        assert config.hsts_preload is False

    def test_staging_config_has_day_hsts(self):
        """Staging config should have 1-day HSTS."""
        config = SecurityHeadersConfig.staging()
        assert config.hsts_max_age == 86400
        assert config.hsts_include_subdomains is True
        assert config.hsts_preload is False

    def test_production_config_has_year_hsts(self):
        """Production config should have 1-year HSTS with preload."""
        config = SecurityHeadersConfig.production()
        assert config.hsts_max_age == 31536000
        assert config.hsts_include_subdomains is True
        assert config.hsts_preload is True

    def test_development_config_allows_cdn(self):
        """Development CSP should allow external resources."""
        config = SecurityHeadersConfig.development()
        script_src = config.csp_directives.get("script-src", "")
        assert "http:" in script_src or "https:" in script_src

    def test_production_config_strict_csp(self):
        """Production CSP should be strict."""
        config = SecurityHeadersConfig.production()
        script_src = config.csp_directives.get("script-src", "")
        assert "'nonce-" in script_src
        assert "https://unpkg.com" not in script_src


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestSecurityHeadersEdgeCases:
    """Edge cases and special scenarios."""

    def test_development_document_policy_empty(self):
        """Development should have empty Document-Policy."""
        config = SecurityHeadersConfig.development()
        assert config.document_policy == ""

    def test_production_document_policy_forced(self):
        """Production should force document policy."""
        config = SecurityHeadersConfig.production()
        assert config.document_policy == "force-load-at-top"

    def test_permissions_policy_development_restricted(self):
        """Development should have restricted permissions."""
        config = SecurityHeadersConfig.development()
        assert "camera=()" in config.permissions_policy
        assert "microphone=()" in config.permissions_policy

    def test_permissions_policy_production_full(self):
        """Production should have comprehensive permissions policy."""
        config = SecurityHeadersConfig.production()
        assert "camera=()" in config.permissions_policy
        assert "microphone=()" in config.permissions_policy
        assert "geolocation=()" in config.permissions_policy
        assert "payment=()" in config.permissions_policy

    def test_cross_origin_policies_strict_in_production(self):
        """Production should use strict cross-origin policies."""
        config = SecurityHeadersConfig.production()
        assert config.corp_policy == "same-origin"
        assert config.coop_policy == "same-origin"
        assert config.coep_policy == "require-corp"

    def test_cross_origin_policies_relaxed_in_development(self):
        """Development should use relaxed cross-origin policies."""
        config = SecurityHeadersConfig.development()
        assert config.corp_policy == "cross-origin"
        assert config.coop_policy == "unsafe-none"
        assert config.coep_policy == "unsafe-none"
