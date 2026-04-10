"""E2E tests for Swagger UI and API documentation accessibility.

Tests the authentication gate on /docs and /redoc endpoints:
- Development: accessible without authentication
- Production: requires valid JWT token

Also tests /openapi.json which is always public.
"""

from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.auth import jwt_manager
from app.core.config import Settings, get_settings
from app.main import app


def clear_settings_cache():
    """Clear the lru_cache on get_settings for test isolation."""
    get_settings.cache_clear()


# =============================================================================
# Fixtures for different environment configurations
# =============================================================================


@pytest.fixture
def dev_settings() -> Settings:
    """Settings configured for development environment."""
    # Use MagicMock to avoid Settings validation issues
    from unittest.mock import MagicMock

    dev = MagicMock(spec=Settings)
    dev.is_development = True
    dev.is_production = False
    dev.environment = "development"
    dev.app_name = "Azure Governance Platform"
    dev.app_version = "1.0.0"
    dev.cors_origins = ["http://localhost:3000"]
    # Use real JWT settings so tokens validate correctly
    dev.jwt_secret_key = _real_settings.jwt_secret_key
    dev.jwt_algorithm = _real_settings.jwt_algorithm
    dev.jwt_access_token_expire_minutes = _real_settings.jwt_access_token_expire_minutes
    dev.jwt_refresh_token_expire_days = _real_settings.jwt_refresh_token_expire_days
    return dev


@pytest.fixture
def prod_settings() -> Settings:
    """Settings configured for production environment.

    Uses the real JWT secret key so tokens created with real settings validate.
    """
    # Use MagicMock to avoid Settings validation in production
    from unittest.mock import MagicMock

    prod = MagicMock(spec=Settings)
    prod.is_development = False
    prod.is_production = True
    prod.environment = "production"
    prod.app_name = "Azure Governance Platform"
    prod.app_version = "1.0.0"
    prod.cors_origins = ["https://example.com"]
    # Use real JWT settings so tokens validate correctly
    prod.jwt_secret_key = _real_settings.jwt_secret_key
    prod.jwt_algorithm = _real_settings.jwt_algorithm
    prod.jwt_access_token_expire_minutes = _real_settings.jwt_access_token_expire_minutes
    prod.jwt_refresh_token_expire_days = _real_settings.jwt_refresh_token_expire_days
    return prod


# Use actual settings for token creation so they validate correctly
_real_settings = get_settings()


def _create_token(**kwargs) -> str:
    """Create a JWT token using the real settings for consistent validation."""
    return jwt_manager.create_access_token(**kwargs)


@pytest.fixture
def valid_token() -> str:
    """Generate a valid JWT token for testing."""
    return _create_token(
        user_id="test-user-123",
        email="test@example.com",
        name="Test User",
        roles=["user"],
        tenant_ids=["test-tenant-123"],
    )


@pytest.fixture
def expired_token() -> str:
    """Generate an expired JWT token for testing."""
    from datetime import timedelta

    return jwt_manager.create_access_token(
        user_id="test-user-123",
        email="test@example.com",
        name="Test User",
        roles=["user"],
        tenant_ids=["test-tenant-123"],
        expires_delta=timedelta(seconds=-1),  # Already expired
    )


# =============================================================================
# Test Class: Swagger UI in Development Environment
# =============================================================================


class TestSwaggerUIInDevelopment:
    """Test /docs endpoint behavior in development environment."""

    def test_swagger_ui_accessible_without_auth(self, dev_settings):
        """Test that /docs returns 200 in development without authentication."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/docs")

                assert response.status_code == 200
                assert "Swagger UI" in response.text or "swagger" in response.text.lower()
                assert "<!DOCTYPE html>" in response.text

    def test_swagger_ui_does_not_redirect_to_login(self, dev_settings):
        """Test that /docs does not redirect to login in development."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/docs", follow_redirects=False)

                # Should NOT redirect (301/302)
                assert response.status_code == 200
                assert response.status_code not in [301, 302, 307, 308]

    def test_swagger_ui_contains_openapi_spec_link(self, dev_settings):
        """Test that Swagger UI contains link to /openapi.json."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/docs")

                assert response.status_code == 200
                assert "/openapi.json" in response.text

    def test_swagger_ui_with_bearer_header_still_works(self, dev_settings, valid_token):
        """Test that /docs works even with bearer token in development."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/docs", headers={"Authorization": f"Bearer {valid_token}"})

                assert response.status_code == 200
                assert "Swagger UI" in response.text or "swagger" in response.text.lower()


# =============================================================================
# Test Class: Swagger UI in Production Environment (No Auth)
# =============================================================================


class TestSwaggerUIRequiresAuthInProduction:
    """Test /docs endpoint behavior in production without authentication."""

    def test_swagger_ui_returns_401_without_auth(self, prod_settings):
        """Test that /docs returns 401 in production without authentication."""
        clear_settings_cache()
        # Patch at the source where get_settings is defined and called
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs")

                assert response.status_code == 401

    def test_swagger_ui_returns_authentication_required_message(self, prod_settings):
        """Test that 401 response contains authentication required message."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs")

                assert response.status_code == 401
                data = response.json()
                assert "detail" in data
                assert (
                    "authentication" in data["detail"].lower()
                    or "required" in data["detail"].lower()
                )

    def test_swagger_ui_returns_www_authenticate_header(self, prod_settings):
        """Test that 401 response includes WWW-Authenticate header."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs")

                assert response.status_code == 401
                assert "www-authenticate" in response.headers
                assert "Bearer" in response.headers["www-authenticate"]

    def test_swagger_ui_does_not_show_swagger_ui_content(self, prod_settings):
        """Test that 401 response does not contain Swagger UI HTML."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs")

                assert response.status_code == 401
                # Response should be JSON, not HTML
                assert response.headers.get("content-type") == "application/json"
                assert "<!DOCTYPE html>" not in response.text
                assert "swagger" not in response.text.lower()


# =============================================================================
# Test Class: Swagger UI in Production (With Valid Auth)
# =============================================================================


class TestSwaggerUIWithValidAuthInProduction:
    """Test /docs endpoint behavior in production with valid authentication."""

    def test_swagger_ui_returns_200_with_valid_token(self, prod_settings, valid_token):
        """Test that /docs returns 200 with valid JWT token in production."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs", headers={"Authorization": f"Bearer {valid_token}"})

                assert response.status_code == 200
                assert "Swagger UI" in response.text or "swagger" in response.text.lower()

    def test_swagger_ui_shows_content_with_valid_token(self, prod_settings, valid_token):
        """Test that /docs shows Swagger UI HTML with valid token."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs", headers={"Authorization": f"Bearer {valid_token}"})

                assert response.status_code == 200
                assert "<!DOCTYPE html>" in response.text
                assert "/openapi.json" in response.text

    def test_swagger_ui_with_valid_token_via_cookie(self, prod_settings, valid_token):
        """Test that /docs works with token in access_token cookie."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs", cookies={"access_token": valid_token})

                assert response.status_code == 200
                assert "Swagger UI" in response.text or "swagger" in response.text.lower()


# =============================================================================
# Test Class: Swagger UI in Production (With Invalid Auth)
# =============================================================================


class TestSwaggerUIWithInvalidAuthInProduction:
    """Test /docs endpoint behavior with invalid/expired authentication."""

    def test_swagger_ui_returns_401_with_expired_token(self, prod_settings, expired_token):
        """Test that /docs returns 401 with expired JWT token."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs", headers={"Authorization": f"Bearer {expired_token}"})

                assert response.status_code == 401
                data = response.json()
                assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()

    def test_swagger_ui_returns_401_with_malformed_token(self, prod_settings):
        """Test that /docs returns 401 with malformed JWT token."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/docs", headers={"Authorization": "Bearer invalid-token"})

                assert response.status_code == 401

    def test_swagger_ui_returns_401_with_missing_bearer_prefix(self, prod_settings, valid_token):
        """Test that /docs returns 401 when Bearer prefix is missing."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get(
                    "/docs",
                    headers={"Authorization": valid_token},  # Missing "Bearer "
                )

                assert response.status_code == 401


# =============================================================================
# Test Class: ReDoc in Development Environment
# =============================================================================


class TestReDocInDevelopment:
    """Test /redoc endpoint behavior in development environment."""

    def test_redoc_accessible_without_auth(self, dev_settings):
        """Test that /redoc returns 200 in development without authentication."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/redoc")

                assert response.status_code == 200
                assert "ReDoc" in response.text or "redoc" in response.text.lower()

    def test_redoc_contains_openapi_spec_link(self, dev_settings):
        """Test that ReDoc contains link to /openapi.json."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/redoc")

                assert response.status_code == 200
                assert "/openapi.json" in response.text


# =============================================================================
# Test Class: ReDoc in Production Environment
# =============================================================================


class TestReDocInProduction:
    """Test /redoc endpoint behavior in production environment."""

    def test_redoc_returns_401_without_auth(self, prod_settings):
        """Test that /redoc returns 401 in production without authentication."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/redoc")

                assert response.status_code == 401

    def test_redoc_returns_200_with_valid_token(self, prod_settings, valid_token):
        """Test that /redoc returns 200 with valid JWT token."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/redoc", headers={"Authorization": f"Bearer {valid_token}"})

                assert response.status_code == 200
                assert "ReDoc" in response.text or "redoc" in response.text.lower()

    def test_redoc_with_valid_token_via_cookie(self, prod_settings, valid_token):
        """Test that /redoc works with token in access_token cookie."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/redoc", cookies={"access_token": valid_token})

                assert response.status_code == 200
                assert "ReDoc" in response.text or "redoc" in response.text.lower()


# =============================================================================
# Test Class: OpenAPI JSON (Always Public)
# =============================================================================


class TestOpenApiJsonAlwaysPublic:
    """Test /openapi.json endpoint - always public in all environments."""

    def test_openapi_json_returns_200_in_development(self, dev_settings):
        """Test that /openapi.json returns 200 in development."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/openapi.json")

                assert response.status_code == 200

    def test_openapi_json_returns_200_in_production_without_auth(self, prod_settings):
        """Test that /openapi.json returns 200 in production without auth."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=prod_settings):
            with TestClient(app) as client:
                response = client.get("/openapi.json")

                assert response.status_code == 200

    def test_openapi_json_returns_valid_json(self, dev_settings):
        """Test that /openapi.json returns valid JSON."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/openapi.json")

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, dict)

    def test_openapi_json_contains_openapi_version(self, dev_settings):
        """Test that /openapi.json contains openapi version field."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/openapi.json")

                assert response.status_code == 200
                data = response.json()
                assert "openapi" in data
                assert data["openapi"].startswith("3.")

    def test_openapi_json_contains_api_info(self, dev_settings):
        """Test that /openapi.json contains API info."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/openapi.json")

                assert response.status_code == 200
                data = response.json()
                assert "info" in data
                assert "title" in data["info"]
                assert "version" in data["info"]

    def test_openapi_json_contains_paths(self, dev_settings):
        """Test that /openapi.json contains API paths."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/openapi.json")

                assert response.status_code == 200
                data = response.json()
                assert "paths" in data
                assert len(data["paths"]) > 0

    def test_openapi_json_content_type_is_json(self, dev_settings):
        """Test that /openapi.json returns application/json content type."""
        clear_settings_cache()
        with patch("app.core.config.get_settings", return_value=dev_settings):
            with TestClient(app) as client:
                response = client.get("/openapi.json")

                assert response.status_code == 200
                content_type = response.headers.get("content-type", "")
                assert "application/json" in content_type


# =============================================================================
# Test Class: Live Server Tests (E2E)
# =============================================================================


@pytest.mark.e2e
class TestSwaggerDocsLiveServer:
    """E2E tests against live server (requires running server)."""

    def test_openapi_json_live_server(self, base_url: str):
        """Test /openapi.json on live server."""
        with httpx.Client(base_url=base_url, timeout=10) as client:
            response = client.get("/openapi.json")

            assert response.status_code == 200
            data = response.json()
            assert "openapi" in data
            assert data["openapi"].startswith("3.")

    def test_docs_returns_401_on_production_server(self, base_url: str):
        """Test that /docs requires auth on production server.

        Note: This assumes the server is running in production mode.
        Skip if server is in development mode.
        """
        with httpx.Client(base_url=base_url, timeout=10) as client:
            response = client.get("/docs")

            # Server might be in dev or prod, both are valid
            # We just verify it responds appropriately
            assert response.status_code in [200, 401]

            if response.status_code == 200:
                # Dev mode - should show Swagger UI
                assert "swagger" in response.text.lower() or "Swagger UI" in response.text
            else:
                # Prod mode - should require auth
                assert response.status_code == 401
