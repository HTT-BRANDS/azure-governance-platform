"""Integration tests for API health endpoints.

These tests verify the health and documentation endpoints
respond correctly using FastAPI's TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create a TestClient for integration testing."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_health_endpoint(client: TestClient) -> None:
    """GET /health returns 200 with 'healthy' status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_detailed(client: TestClient) -> None:
    """GET /health/detailed returns 200 with components dict."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert isinstance(data["components"], dict)


def test_api_docs(client: TestClient) -> None:
    """GET /docs returns 200 (Swagger UI)."""
    response = client.get("/docs")
    assert response.status_code == 200
