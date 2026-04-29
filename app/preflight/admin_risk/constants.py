"""Shared thresholds and severity values for admin risk checks."""

# Thresholds for risk detection
OVERPRIVILEGED_ROLE_THRESHOLD = 3  # More than this many roles is concerning
INACTIVE_ADMIN_DAYS = 90  # Days of inactivity to flag
SHARED_ACCOUNT_INDICATORS = ["admin", "service", "shared", "svc-"]
CRITICAL_ROLES = [
    "Global Administrator",
    "Privileged Role Administrator",
    "User Administrator",
    "Security Administrator",
]


class AdminRiskSeverity:
    """Severity levels for admin risk checks."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
