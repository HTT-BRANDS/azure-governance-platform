"""Unit tests for EmailService.

Tests for SMTP-based email notifications with HTML templates for
MFA compliance, deadline tracking, maturity regressions, and threat escalations.

8 tests covering:
- EmailService initialization
- Email composition (subject, body, recipients)
- SMTP connection handling (mocked)
- Error handling for send failures
- Template rendering for alert emails
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.notifications import Notification, NotificationChannel, Severity
from app.services.email_service import EmailMessage, EmailService, EmailTemplate


class TestEmailServiceInit:
    """Tests for EmailService initialization."""

    def test_init_with_defaults(self):
        """Test EmailService uses settings defaults."""
        service = EmailService()

        assert service.smtp_host is not None
        assert service.smtp_port is not None
        assert service.from_address is not None

    def test_init_with_custom_config(self):
        """Test EmailService accepts custom configuration."""
        service = EmailService(
            smtp_host="smtp.test.com",
            smtp_port=465,
            smtp_user="testuser",
            smtp_password="testpass",
            from_address="test@example.com",
            use_tls=False,
        )

        assert service.smtp_host == "smtp.test.com"
        assert service.smtp_port == 465
        assert service.smtp_user == "testuser"
        assert service.smtp_password == "testpass"
        assert service.from_address == "test@example.com"
        assert service.use_tls is False


class TestEmailComposition:
    """Tests for email message composition."""

    @pytest.mark.asyncio
    async def test_compose_mfa_alert_email(self):
        """Test MFA alert email sending."""
        service = EmailService(
            smtp_host="smtp.test.com",
            smtp_port=587,
        )

        # Mock the SMTP client
        with patch("app.services.email_service.aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.connect = AsyncMock()
            mock_smtp.starttls = AsyncMock()
            mock_smtp.login = AsyncMock()
            mock_smtp.sendmail = AsyncMock()
            mock_smtp.quit = AsyncMock()

            result = await service.send_mfa_alert(
                to_addresses=["admin@example.com"],
                tenant_id="test-tenant",
                user_mfa_pct=85.0,
                admin_mfa_pct=90.0,
                unprotected_admins=3,
            )

            assert result["success"] is True
            assert result["channel"] == NotificationChannel.EMAIL

    @pytest.mark.asyncio
    async def test_compose_deadline_alert_email(self):
        """Test deadline alert email sending."""
        service = EmailService(
            smtp_host="smtp.test.com",
            smtp_port=587,
        )

        # Mock the SMTP client
        with patch("app.services.email_service.aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.connect = AsyncMock()
            mock_smtp.starttls = AsyncMock()
            mock_smtp.login = AsyncMock()
            mock_smtp.sendmail = AsyncMock()
            mock_smtp.quit = AsyncMock()

            result = await service.send_deadline_alert(
                to_addresses=["admin@example.com"],
                requirement_id="REQ-001",
                tenant_id="test-tenant",
                title="Security Compliance",
                days_until=60,
                is_overdue=False,
            )

            assert result["success"] is True
            assert result["channel"] == NotificationChannel.EMAIL

    def test_email_message_has_required_fields(self):
        """Test EmailMessage dataclass has all required fields."""
        msg = EmailMessage(
            subject="Test Subject",
            body_text="Plain text body",
            body_html="<html><body>HTML body</body></html>",
            to_addresses=["test@example.com"],
            from_address="sender@example.com",
            template=EmailTemplate.GENERIC,
        )

        assert msg.subject == "Test Subject"
        assert msg.body_text == "Plain text body"
        assert msg.body_html == "<html><body>HTML body</body></html>"
        assert msg.to_addresses == ["test@example.com"]
        assert msg.from_address == "sender@example.com"
        assert msg.template == EmailTemplate.GENERIC


class TestSMTPConnection:
    """Tests for SMTP connection handling."""

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email send via SMTP."""
        service = EmailService(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="testuser",
            smtp_password="testpass",
        )

        # Mock the SMTP client
        with patch("app.services.email_service.aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.connect = AsyncMock()
            mock_smtp.starttls = AsyncMock()
            mock_smtp.login = AsyncMock()
            mock_smtp.sendmail = AsyncMock()
            mock_smtp.quit = AsyncMock()

            result = await service.send_email(
                to_addresses=["recipient@example.com"],
                subject="Test Email",
                body_text="Test body",
                body_html="<p>Test body</p>",
            )

            assert result["success"] is True
            assert result["channel"] == NotificationChannel.EMAIL
            mock_smtp.connect.assert_called_once()
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("testuser", "testpass")

    @pytest.mark.asyncio
    async def test_send_email_no_smtp_host(self):
        """Test error when SMTP host is not configured."""
        service = EmailService(smtp_host=None)

        result = await service.send_email(
            to_addresses=["recipient@example.com"],
            subject="Test Email",
            body_text="Test body",
            body_html="<p>Test body</p>",
        )

        assert result["success"] is False
        assert "error" in result


class TestErrorHandling:
    """Tests for error handling during email sending."""

    @pytest.mark.asyncio
    async def test_send_email_connection_error(self):
        """Test handling of SMTP connection errors."""
        service = EmailService(
            smtp_host="smtp.test.com",
            smtp_port=587,
        )

        # Mock SMTP to raise connection error
        with patch("app.services.email_service.aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.connect.side_effect = Exception("Connection refused")

            result = await service.send_email(
                to_addresses=["recipient@example.com"],
                subject="Test Email",
                body_text="Test body",
                body_html="<p>Test body</p>",
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_send_notification_integration(self):
        """Test sending notification via email channel."""
        notification = Notification(
            channel=NotificationChannel.EMAIL,
            severity=Severity.INFO,
            title="Test Notification",
            message="Test message",
            tenant_id="test-tenant",
        )

        service = EmailService(
            smtp_host="smtp.test.com",
            smtp_port=587,
        )

        # Mock the SMTP client
        with patch("app.services.email_service.aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.connect = AsyncMock()
            mock_smtp.starttls = AsyncMock()
            mock_smtp.login = AsyncMock()
            mock_smtp.sendmail = AsyncMock()
            mock_smtp.quit = AsyncMock()

            result = await service.send_notification(
                notification, to_addresses=["admin@example.com"]
            )

            assert result["success"] is True
            assert result["channel"] == NotificationChannel.EMAIL
