"""Core module initialization."""

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db, get_db_context, init_db
from app.core.notifications import (
    Notification,
    NotificationChannel,
    Severity,
    create_dashboard_url,
    create_retry_url,
    format_sync_alert,
    record_notification_sent,
    send_notification,
    send_teams_notification,
    severity_meets_threshold,
    should_notify,
)
from app.core.scheduler import get_scheduler, init_scheduler, trigger_manual_sync

__all__ = [
    "Settings",
    "get_settings",
    "Base",
    "get_db",
    "get_db_context",
    "init_db",
    "get_scheduler",
    "init_scheduler",
    "trigger_manual_sync",
    # Notifications
    "Notification",
    "NotificationChannel",
    "Severity",
    "should_notify",
    "send_notification",
    "send_teams_notification",
    "format_sync_alert",
    "record_notification_sent",
    "severity_meets_threshold",
    "create_dashboard_url",
    "create_retry_url",
]
