"""Unit tests for TeamsWebhookClient.

Tests for Microsoft Teams webhook integration with adaptive card construction,
POST handling, retry logic, and rate limiting.

10 tests covering:
- TeamsWebhookClient initialization
- Adaptive card construction via module-level helpers
- Webhook POST (mocked httpx)
- Error handling
- Rate limit handling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.notifications import Notification, NotificationChannel, Severity
from app.services.teams_webhook import (
    AlertType,
    TeamsCard,
    TeamsWebhookClient,
    create_adaptive_card,
    create_deadline_alert_card,
    create_mfa_alert_card,
)


class TestTeamsWebhookClientInit:
    """Tests for TeamsWebhookClient initialization."""

    def test_init_with_webhook_url(self):
        """Test client initialization with webhook URL."""
        webhook_url = "https://outlook.office.com/webhook/test"
        client = TeamsWebhookClient(webhook_url=webhook_url)

        assert client.webhook_url == webhook_url
        assert client.timeout is not None

    def test_init_default_timeout(self):
        """Test client initialization has default timeout of 30s."""
        webhook_url = "https://outlook.office.com/webhook/test"
        client = TeamsWebhookClient(webhook_url=webhook_url)

        assert client.timeout == 30.0


class TestAdaptiveCardConstruction:
    """Tests for Teams adaptive card construction."""

    def test_create_mfa_alert_card(self):
        """Test creating MFA alert card structure."""
        card = create_mfa_alert_card(
            tenant_id="Test Tenant",
            user_mfa_pct=85.0,
            admin_mfa_pct=90.0,
            unprotected_admins=2,
            severity=Severity.WARNING,
        )

        assert isinstance(card, TeamsCard)
        assert card.alert_type == AlertType.MFA_GAP
        assert card.severity == Severity.WARNING
        assert "Test Tenant" in card.title

        # Verify adaptive card payload
        payload = create_adaptive_card(card)
        assert payload["type"] == "message"
        assert "attachments" in payload

    def test_create_deadline_alert_card(self):
        """Test creating deadline alert card structure."""
        card = create_deadline_alert_card(
            requirement_id="IAM-001",
            tenant_id="Test Tenant",
            title="MFA Enforcement",
            days_until=30,
            is_overdue=False,
            severity=Severity.WARNING,
        )

        assert isinstance(card, TeamsCard)
        assert card.alert_type == AlertType.DEADLINE
        assert "30 days" in card.message

    def test_create_generic_teams_card(self):
        """Test creating a generic TeamsCard directly."""
        card = TeamsCard(
            title="Test Alert",
            message="This is a test alert",
            severity=Severity.INFO,
            alert_type=AlertType.COMPLIANCE,
            facts=[{"title": "Tenant", "value": "test-tenant"}],
        )

        payload = create_adaptive_card(card)
        assert payload["type"] == "message"
        content = payload["attachments"][0]["content"]
        assert content["type"] == "AdaptiveCard"

    def test_card_includes_facts_when_provided(self):
        """Test that cards include facts when provided."""
        card = create_mfa_alert_card(
            tenant_id="Test Tenant",
            user_mfa_pct=85.0,
            admin_mfa_pct=90.0,
            unprotected_admins=2,
            severity=Severity.WARNING,
            dashboard_url="https://dashboard.example.com",
        )

        assert card.facts is not None
        assert len(card.facts) > 0
        assert card.actions is not None


class TestWebhookPOST:
    """Tests for webhook POST operations."""

    @pytest.mark.asyncio
    async def test_send_card_success(self):
        """Test successful webhook POST."""
        webhook_url = "https://outlook.office.com/webhook/test"
        client = TeamsWebhookClient(webhook_url=webhook_url)

        card = TeamsCard(
            title="Test",
            message="Test message",
            severity=Severity.INFO,
            alert_type=AlertType.COMPLIANCE,
        )

        with patch("app.services.teams_webhook.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            result = await client.send_card(card)

            assert result["success"] is True
            assert result["channel"] == NotificationChannel.TEAMS
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_card_http_error(self):
        """Test handling of HTTP errors."""
        webhook_url = "https://outlook.office.com/webhook/test"
        client = TeamsWebhookClient(webhook_url=webhook_url)

        card = TeamsCard(
            title="Test",
            message="Test message",
            severity=Severity.INFO,
            alert_type=AlertType.COMPLIANCE,
        )

        with patch("app.services.teams_webhook.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("Network error")

            result = await client.send_card(card)

            assert result["success"] is False
            assert "error" in result


class TestRetryAndRateLimit:
    """Tests for retry logic and rate limiting."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test notification sending via send_notification."""
        webhook_url = "https://outlook.office.com/webhook/test"
        client = TeamsWebhookClient(webhook_url=webhook_url)

        notification = Notification(
            channel=NotificationChannel.TEAMS,
            severity=Severity.ERROR,
            title="Test Alert",
            message="Test message",
            tenant_id="test-tenant",
        )

        with patch("app.services.teams_webhook.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response

            result = await client.send_notification(notification)

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test handling of rate limit responses (429)."""
        webhook_url = "https://outlook.office.com/webhook/test"
        client = TeamsWebhookClient(webhook_url=webhook_url)

        card = TeamsCard(
            title="Test",
            message="Test message",
            severity=Severity.INFO,
            alert_type=AlertType.COMPLIANCE,
        )

        with patch("app.services.teams_webhook.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Rate limited",
                request=MagicMock(),
                response=mock_response,
            )
            mock_client.post.return_value = mock_response

            result = await client.send_card(card)

            # Should handle rate limit gracefully
            assert result["success"] is False
            assert "429" in result.get("error", "")
