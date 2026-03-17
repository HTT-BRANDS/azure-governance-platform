"""Unit tests for resource health aggregation.

Tests the LighthouseAzureClient health methods and the
get_lighthouse_client / reset_lighthouse_client singletons in
app/services/lighthouse_client.py.

Traces: RM-006 — Resource health aggregation and Lighthouse client health.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.lighthouse_client import (
    LighthouseAzureClient,
    LighthouseDelegationError,
    get_lighthouse_client,
    reset_lighthouse_client,
)


# ---------------------------------------------------------------------------
# LighthouseDelegationError
# ---------------------------------------------------------------------------


class TestLighthouseDelegationError:
    """Tests for LighthouseDelegationError exception."""

    def test_creation(self):
        err = LighthouseDelegationError("sub-123", "Access denied")
        assert err.subscription_id == "sub-123"
        assert "sub-123" in str(err)
        assert "Access denied" in str(err)

    def test_is_exception(self):
        err = LighthouseDelegationError("sub-456", "timeout")
        assert isinstance(err, Exception)

    def test_message_format(self):
        err = LighthouseDelegationError("sub-001", "not delegated")
        assert str(err).startswith("Lighthouse delegation failed for sub-001")


# ---------------------------------------------------------------------------
# LighthouseAzureClient initialization
# ---------------------------------------------------------------------------


class TestLighthouseAzureClientInit:
    """Tests for LighthouseAzureClient initialization."""

    @patch("app.services.lighthouse_client.DefaultAzureCredential")
    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_default_credential(self, mock_resilient, mock_cred):
        """Should use DefaultAzureCredential when no credential provided."""
        client = LighthouseAzureClient()
        mock_cred.assert_called_once()
        assert client.credential is mock_cred.return_value

    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_custom_credential(self, mock_resilient):
        """Should use provided credential."""
        fake_cred = MagicMock()
        client = LighthouseAzureClient(credential=fake_cred)
        assert client.credential is fake_cred

    @patch("app.services.lighthouse_client.DefaultAzureCredential")
    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_resilience_clients_created(self, mock_resilient, mock_cred):
        """Should create per-API resilient clients."""
        client = LighthouseAzureClient()
        # 4 calls: general + arm + cost + security
        assert mock_resilient.call_count == 4


# ---------------------------------------------------------------------------
# get_health_status
# ---------------------------------------------------------------------------


class TestGetHealthStatus:
    """Tests for LighthouseAzureClient.get_health_status."""

    @patch("app.services.lighthouse_client.DefaultAzureCredential")
    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_returns_healthy_status(self, mock_resilient, mock_cred):
        """Health status should return 'healthy'."""
        mock_resilient_instance = MagicMock()
        mock_resilient_instance.get_state.return_value = {"state": "closed"}
        mock_resilient.return_value = mock_resilient_instance

        client = LighthouseAzureClient()
        status = client.get_health_status()

        assert status["status"] == "healthy"
        assert "resilience_state" in status
        assert "credential_type" in status

    @patch("app.services.lighthouse_client.DefaultAzureCredential")
    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_includes_resilience_state(self, mock_resilient, mock_cred):
        """Health status should include per-API resilience state."""
        mock_resilient_instance = MagicMock()
        mock_resilient_instance.get_state.return_value = {"state": "closed"}
        mock_resilient.return_value = mock_resilient_instance

        client = LighthouseAzureClient()
        status = client.get_health_status()

        assert "arm" in status["resilience_state"]
        assert "cost" in status["resilience_state"]
        assert "security" in status["resilience_state"]

    @patch("app.services.lighthouse_client.DefaultAzureCredential")
    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_credential_type_in_status(self, mock_resilient, mock_cred):
        """Health status should report credential type name."""
        client = LighthouseAzureClient()
        status = client.get_health_status()

        assert status["credential_type"] == type(client.credential).__name__


# ---------------------------------------------------------------------------
# get_lighthouse_client / reset_lighthouse_client
# ---------------------------------------------------------------------------


class TestLighthouseClientSingleton:
    """Tests for the global client singleton."""

    def setup_method(self):
        """Reset before each test."""
        reset_lighthouse_client()

    def teardown_method(self):
        """Reset after each test."""
        reset_lighthouse_client()

    @patch("app.services.lighthouse_client.DefaultAzureCredential")
    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_get_creates_instance(self, mock_resilient, mock_cred):
        """First call should create a new client."""
        client = get_lighthouse_client()
        assert isinstance(client, LighthouseAzureClient)

    @patch("app.services.lighthouse_client.DefaultAzureCredential")
    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_get_returns_same_instance(self, mock_resilient, mock_cred):
        """Subsequent calls should return the same instance."""
        c1 = get_lighthouse_client()
        c2 = get_lighthouse_client()
        assert c1 is c2

    @patch("app.services.lighthouse_client.DefaultAzureCredential")
    @patch("app.services.lighthouse_client.ResilientAzureClient")
    def test_reset_clears_instance(self, mock_resilient, mock_cred):
        """reset_lighthouse_client should clear the singleton."""
        c1 = get_lighthouse_client()
        reset_lighthouse_client()
        c2 = get_lighthouse_client()
        assert c1 is not c2
