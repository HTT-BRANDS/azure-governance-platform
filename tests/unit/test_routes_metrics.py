"""Unit tests for metrics API routes.

Tests metrics endpoints:
- GET /api/v1/metrics/health
- GET /api/v1/metrics/cache
- GET /api/v1/metrics/database
- Auth required on all endpoints
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


class TestHealthMetrics:
    """Tests for GET /api/v1/metrics/health."""

    def test_health_returns_status_and_version(self, authed_client):
        """Health endpoint returns timestamp, status, and version."""
        response = authed_client.get("/api/v1/metrics/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestCacheMetrics:
    """Tests for GET /api/v1/metrics/cache."""

    def test_cache_returns_metrics(self, authed_client):
        """Cache endpoint returns hit/miss stats from cache_manager."""
        mock_stats = {
            "backend": "memory",
            "hits": 150,
            "misses": 30,
            "hit_rate": 0.83,
            "size": 42,
        }

        with patch("app.api.routes.metrics.cache_manager") as mock_cm:
            mock_cm.get_metrics.return_value = mock_stats
            response = authed_client.get("/api/v1/metrics/cache")

        assert response.status_code == 200
        data = response.json()
        assert data["hits"] == 150
        assert data["misses"] == 30
        assert data["hit_rate"] == 0.83
        assert data["size"] == 42
        assert "timestamp" in data


class TestDatabaseMetrics:
    """Tests for GET /api/v1/metrics/database."""

    def test_database_returns_connected(self, authed_client):
        """Database endpoint returns connected status and timestamp."""
        response = authed_client.get("/api/v1/metrics/database")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert "timestamp" in data


class TestMetricsAuth:
    """All metrics endpoints require authentication."""

    def test_health_requires_auth(self, db_session):
        """GET /api/v1/metrics/health returns 401 without credentials."""

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/metrics/health")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_cache_requires_auth(self, db_session):
        """GET /api/v1/metrics/cache returns 401 without credentials."""

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/metrics/cache")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_database_requires_auth(self, db_session):
        """GET /api/v1/metrics/database returns 401 without credentials."""

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/metrics/database")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(get_db, None)
