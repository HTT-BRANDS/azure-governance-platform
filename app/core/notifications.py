"""Notification utilities for sync job alerts.

Provides multi-channel notification support including Teams webhooks,
email, and generic webhooks with adaptive card formatting and
deduplication logic.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Supported notification channels."""

    TEAMS = "teams"
    EMAIL = "email"
    WEBHOOK = "webhook"


class Severity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Notification:
    """Notification data structure."""

    title: str
    message: str
    severity: Severity = Severity.INFO
    channel: NotificationChannel = NotificationChannel.TEAMS
    metadata: dict[str, Any] = field(default_factory=dict)
    alert_id: int | None = None
    job_type: str | None = None
    tenant_id: str | None = None
    error_message: str | None = None
    dashboard_url: str | None = None
    retry_url: str | None = None


# In-memory tracking for notification deduplication
# Maps (alert_type, job_type) -> last_notification_time
_notification_history: dict[tuple[str, str | None], datetime] = {}


def should_notify(
    alert_type: str,
    job_type: str | None = None,
    cooldown_minutes: int | None = None,
) -> bool:
    """Check if notification should be sent based on deduplication rules.

    Prevents notification spam by tracking last notification time per
    alert type and job type combination.

    Args:
        alert_type: Type of alert (e.g., 'sync_failure', 'stale_sync')
        job_type: Optional job type for more granular tracking
        cooldown_minutes: Optional override for cooldown period

    Returns:
        True if notification should be sent, False if in cooldown
    """
    settings = get_settings()

    if not settings.notification_enabled:
        return False

    cooldown = timedelta(minutes=cooldown_minutes or settings.notification_cooldown_minutes)
    key = (alert_type, job_type)
    now = datetime.utcnow()

    last_sent = _notification_history.get(key)
    if last_sent and (now - last_sent) < cooldown:
        logger.debug(
            f"Skipping notification for {alert_type}/{job_type}: "
            f"in cooldown period (last sent {last_sent.isoformat()})"
        )
        return False

    return True


def record_notification_sent(
    alert_type: str,
    job_type: str | None = None,
) -> None:
    """Record that a notification was sent for deduplication tracking.

    Args:
        alert_type: Type of alert
        job_type: Optional job type
    """
    key = (alert_type, job_type)
    _notification_history[key] = datetime.utcnow()


def severity_meets_threshold(severity: Severity | str, threshold: Severity | str) -> bool:
    """Check if severity meets or exceeds the threshold.

    Severity order: info < warning < error < critical

    Args:
        severity: The severity to check
        threshold: The minimum severity threshold

    Returns:
        True if severity >= threshold
    """
    severity_order = {
        Severity.INFO: 0,
        Severity.WARNING: 1,
        Severity.ERROR: 2,
        Severity.CRITICAL: 3,
    }

    sev_val = severity_order.get(Severity(severity), 0)
    thresh_val = severity_order.get(Severity(threshold), 0)

    return sev_val >= thresh_val


def get_severity_color(severity: Severity | str) -> str:
    """Get Teams color code for severity level.

    Args:
        severity: The severity level

    Returns:
        Hex color code for the severity
    """
    colors = {
        Severity.INFO: "#0078D4",  # Blue
        Severity.WARNING: "#FFB900",  # Yellow/Gold
        Severity.ERROR: "#D83B01",  # Orange/Red
        Severity.CRITICAL: "#A80000",  # Dark Red
    }
    return colors.get(Severity(severity), "#0078D4")


def format_sync_alert(notification: Notification) -> dict[str, Any]:
    """Format a sync alert notification as a Teams Adaptive Card.

    Creates rich, actionable Adaptive Cards with:
    - Color-coded severity indicators
    - Sync job details
    - Quick action buttons
    - Links to dashboard and retry API

    Args:
        notification: The notification to format

    Returns:
        Adaptive Card JSON payload for Teams webhook
    """
    color = get_severity_color(notification.severity)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Build facts section with available details
    facts = []
    if notification.job_type:
        facts.append({"title": "Job Type", "value": notification.job_type.title()})
    if notification.tenant_id:
        facts.append({"title": "Tenant", "value": notification.tenant_id})
    if notification.alert_id:
        facts.append({"title": "Alert ID", "value": str(notification.alert_id)})

    # Action buttons
    actions = []
    if notification.dashboard_url:
        actions.append({
            "type": "Action.OpenUrl",
            "title": "📊 View Dashboard",
            "url": notification.dashboard_url,
        })
    if notification.retry_url:
        actions.append({
            "type": "Action.OpenUrl",
            "title": "🔄 Retry Sync",
            "url": notification.retry_url,
        })

    # Build the card
    card = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentVersion": "1.4",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "style": "emphasis",
                    "backgroundColor": color,
                    "body": [
                        {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                    "type": "Column",
                                    "width": "auto",
                                    "items": [
                                        {
                                            "type": "Image",
                                            "url": "https://cdn-icons-png.flaticon.com/512/564/564619.png",
                                            "altText": "Alert",
                                            "size": "Small",
                                        }
                                    ],
                                },
                                {
                                    "type": "Column",
                                    "width": "stretch",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": f"🔔 {notification.title}",
                                            "weight": "Bolder",
                                            "size": "Large",
                                            "color": notification.severity == Severity.CRITICAL and "Attention" or "Default",
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": f"Severity: **{notification.severity.upper()}** • {timestamp}",
                                            "size": "Small",
                                            "isSubtle": True,
                                        },
                                    ],
                                },
                            ],
                        },
                        {
                            "type": "TextBlock",
                            "text": notification.message,
                            "wrap": True,
                            "spacing": "Medium",
                        },
                    ],
                },
            }
        ],
    }

    # Add error details if present
    if notification.error_message:
        card["attachments"][0]["content"]["body"].append({
            "type": "Container",
            "style": "emphasis",
            "items": [
                {
                    "type": "TextBlock",
                    "text": "Error Details",
                    "weight": "Bolder",
                    "size": "Medium",
                },
                {
                    "type": "TextBlock",
                    "text": notification.error_message[:500],  # Truncate long errors
                    "fontType": "Monospace",
                    "wrap": True,
                    "size": "Small",
                },
            ],
        })

    # Add facts table
    if facts:
        card["attachments"][0]["content"]["body"].append({
            "type": "FactSet",
            "facts": facts,
        })

    # Add actions if available
    if actions:
        card["attachments"][0]["content"]["actions"] = actions

    return card


async def send_teams_notification(notification: Notification) -> dict[str, Any]:
    """Send notification to Microsoft Teams via webhook.

    Args:
        notification: The notification to send

    Returns:
        Dict with success status and response details
    """
    settings = get_settings()

    if not settings.teams_webhook_url:
        logger.warning("Teams webhook URL not configured")
        return {
            "success": False,
            "error": "Teams webhook URL not configured",
            "channel": NotificationChannel.TEAMS,
        }

    payload = format_sync_alert(notification)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.teams_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        logger.info(f"Teams notification sent: {notification.title}")
        return {
            "success": True,
            "status_code": response.status_code,
            "channel": NotificationChannel.TEAMS,
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"Teams webhook returned error: {e.response.status_code} - {e.response.text}")
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "channel": NotificationChannel.TEAMS,
        }
    except Exception as e:
        logger.error(f"Failed to send Teams notification: {e}")
        return {
            "success": False,
            "error": str(e),
            "channel": NotificationChannel.TEAMS,
        }


async def send_webhook_notification(
    notification: Notification,
    webhook_url: str,
) -> dict[str, Any]:
    """Send notification to a generic webhook endpoint.

    Args:
        notification: The notification to send
        webhook_url: The webhook URL

    Returns:
        Dict with success status and response details
    """
    payload = {
        "title": notification.title,
        "message": notification.message,
        "severity": notification.severity.value,
        "timestamp": datetime.utcnow().isoformat(),
        "alert_id": notification.alert_id,
        "job_type": notification.job_type,
        "tenant_id": notification.tenant_id,
        "metadata": notification.metadata,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        logger.info(f"Webhook notification sent: {notification.title}")
        return {
            "success": True,
            "status_code": response.status_code,
            "channel": NotificationChannel.WEBHOOK,
        }

    except Exception as e:
        logger.error(f"Failed to send webhook notification: {e}")
        return {
            "success": False,
            "error": str(e),
            "channel": NotificationChannel.WEBHOOK,
        }


async def send_notification(
    notification: Notification,
    webhook_url: str | None = None,
) -> dict[str, Any]:
    """Generic notification dispatcher.

    Routes notifications to appropriate channel based on configuration.

    Args:
        notification: The notification to send
        webhook_url: Optional custom webhook URL for webhook channel

    Returns:
        Dict with success status and response details
    """
    settings = get_settings()

    # Check if notifications are enabled
    if not settings.notification_enabled:
        logger.debug("Notifications disabled in settings")
        return {
            "success": False,
            "error": "Notifications disabled",
            "channel": notification.channel,
        }

    # Check severity threshold
    if not severity_meets_threshold(notification.severity, settings.notification_min_severity):
        logger.debug(
            f"Notification severity {notification.severity} below threshold "
            f"{settings.notification_min_severity}"
        )
        return {
            "success": False,
            "error": f"Severity {notification.severity} below threshold",
            "channel": notification.channel,
        }

    # Dispatch to appropriate channel
    if notification.channel == NotificationChannel.TEAMS:
        return await send_teams_notification(notification)
    elif notification.channel == NotificationChannel.WEBHOOK and webhook_url:
        return await send_webhook_notification(notification, webhook_url)
    elif notification.channel == NotificationChannel.EMAIL:
        # Email not yet implemented
        logger.warning("Email notifications not yet implemented")
        return {
            "success": False,
            "error": "Email channel not implemented",
            "channel": NotificationChannel.EMAIL,
        }
    else:
        return {
            "success": False,
            "error": f"Unknown channel: {notification.channel}",
            "channel": notification.channel,
        }


def create_dashboard_url(job_type: str | None = None) -> str | None:
    """Generate dashboard URL for notifications.

    Args:
        job_type: Optional job type for direct link

    Returns:
        Dashboard URL or None if not configured
    """
    settings = get_settings()
    base_url = f"http://{settings.host}:{settings.port}"

    if job_type:
        return f"{base_url}/sync-dashboard?type={job_type}"
    return f"{base_url}/sync-dashboard"


def create_retry_url(job_type: str, tenant_id: str | None = None) -> str | None:
    """Generate API retry URL for notifications.

    Args:
        job_type: The type of sync job to retry
        tenant_id: Optional specific tenant

    Returns:
        API URL for retrying the sync or None
    """
    settings = get_settings()
    base_url = f"http://{settings.host}:{settings.port}"

    if tenant_id:
        return f"{base_url}/api/sync/{job_type}?tenant_id={tenant_id}"
    return f"{base_url}/api/sync/{job_type}"
