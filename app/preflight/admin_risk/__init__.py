"""Admin risk check strategies split by identity risk domain."""

from app.preflight.admin_risk.compliance import AdminComplianceGapCheck
from app.preflight.admin_risk.constants import (
    CRITICAL_ROLES,
    INACTIVE_ADMIN_DAYS,
    OVERPRIVILEGED_ROLE_THRESHOLD,
    SHARED_ACCOUNT_INDICATORS,
    AdminRiskSeverity,
)
from app.preflight.admin_risk.inactive import InactiveAdminCheck
from app.preflight.admin_risk.mfa import AdminMfaCheck
from app.preflight.admin_risk.overprivileged import OverprivilegedAccountCheck
from app.preflight.admin_risk.registry import (
    ADMIN_RISK_CHECK_STRATEGIES,
    build_admin_risk_checks,
    get_admin_risk_checks,
    run_all_admin_risk_checks,
)
from app.preflight.admin_risk.shared import SharedAdminCheck

__all__ = [
    "ADMIN_RISK_CHECK_STRATEGIES",
    "CRITICAL_ROLES",
    "INACTIVE_ADMIN_DAYS",
    "OVERPRIVILEGED_ROLE_THRESHOLD",
    "SHARED_ACCOUNT_INDICATORS",
    "AdminComplianceGapCheck",
    "AdminMfaCheck",
    "AdminRiskSeverity",
    "InactiveAdminCheck",
    "OverprivilegedAccountCheck",
    "SharedAdminCheck",
    "build_admin_risk_checks",
    "get_admin_risk_checks",
    "run_all_admin_risk_checks",
]
