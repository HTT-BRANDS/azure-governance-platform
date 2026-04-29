"""Inactive privileged administrator check."""

import time
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.identity import PrivilegedUser
from app.preflight.admin_risk.constants import (
    CRITICAL_ROLES,
    INACTIVE_ADMIN_DAYS,
    AdminRiskSeverity,
)
from app.preflight.admin_risk.session import create_admin_risk_session
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus


class InactiveAdminCheck(BasePreflightCheck):
    """Check for inactive administrative accounts.

    Identifies privileged accounts that haven't signed in for
    90+ days, which may indicate stale credentials or
    unnecessary access.
    """

    def __init__(self):
        super().__init__(
            check_id="admin_inactive",
            name="Inactive Administrator Detection",
            category=CheckCategory.AZURE_SECURITY,
            description="Identify admin accounts inactive for 90+ days",
            timeout_seconds=15.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute inactive admin check."""
        start_time = time.perf_counter()
        db: Session | None = None

        try:
            db = create_admin_risk_session()

            # Calculate the threshold date
            threshold_date = datetime.now(UTC) - timedelta(days=INACTIVE_ADMIN_DAYS)

            # Find inactive admins
            query = db.query(PrivilegedUser).filter(PrivilegedUser.last_sign_in < threshold_date)

            if tenant_id:
                query = query.filter(PrivilegedUser.tenant_id == tenant_id)

            inactive_users = query.all()

            # Group by user and calculate days inactive
            unique_users: dict[str, dict[str, Any]] = {}
            for user in inactive_users:
                if user.user_principal_name not in unique_users:
                    last_sign_in = user.last_sign_in
                    if last_sign_in and last_sign_in.tzinfo is None:
                        last_sign_in = last_sign_in.replace(tzinfo=UTC)
                    days_inactive = (
                        (datetime.now(UTC) - last_sign_in).days if last_sign_in else None
                    )

                    unique_users[user.user_principal_name] = {
                        "display_name": user.display_name,
                        "last_sign_in": (
                            user.last_sign_in.isoformat() if user.last_sign_in else None
                        ),
                        "days_inactive": days_inactive,
                        "roles": [],
                        "has_critical_role": False,
                        "mfa_enabled": bool(user.mfa_enabled),
                    }

                unique_users[user.user_principal_name]["roles"].append(user.role_name)
                if user.role_name in CRITICAL_ROLES:
                    unique_users[user.user_principal_name]["has_critical_role"] = True

            duration_ms = (time.perf_counter() - start_time) * 1000

            if unique_users:
                critical_count = sum(1 for u in unique_users.values() if u["has_critical_role"])
                without_mfa = sum(1 for u in unique_users.values() if not u["mfa_enabled"])

                # Determine severity based on critical roles
                if critical_count > 0:
                    status = CheckStatus.FAIL
                    severity = AdminRiskSeverity.CRITICAL
                else:
                    status = CheckStatus.WARNING
                    severity = AdminRiskSeverity.MEDIUM

                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=status,
                    message=(
                        f"{len(unique_users)} inactive admin accounts (>{INACTIVE_ADMIN_DAYS} days)"
                    ),
                    details={
                        "inactive_count": len(unique_users),
                        "inactive_days_threshold": INACTIVE_ADMIN_DAYS,
                        "critical_role_inactive": critical_count,
                        "without_mfa": without_mfa,
                        "severity": severity,
                        "accounts": [
                            {
                                "user_principal_name": upn,
                                "display_name": info["display_name"],
                                "last_sign_in": info["last_sign_in"],
                                "days_inactive": info["days_inactive"],
                                "roles": info["roles"],
                                "has_critical_role": info["has_critical_role"],
                                "mfa_enabled": info["mfa_enabled"],
                            }
                            for upn, info in unique_users.items()
                        ],
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Review and disable/remove inactive admin accounts",
                        "Require re-authentication for dormant accounts before reactivation",
                        "Implement automated access reviews for privileged roles",
                        "Set up alerts for accounts inactive > 30 days",
                        "Document and justify any exceptions for inactive accounts",
                        "Consider breaking glass accounts with documented procedures",
                    ],
                    tenant_id=tenant_id,
                )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.PASS,
                message="No inactive admin accounts detected",
                details={
                    "inactive_days_threshold": INACTIVE_ADMIN_DAYS,
                    "severity": AdminRiskSeverity.INFO,
                },
                duration_ms=duration_ms,
                tenant_id=tenant_id,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.FAIL,
                message=f"Failed to check for inactive admins: {str(e)}",
                details={
                    "error_type": type(e).__name__,
                    "severity": AdminRiskSeverity.CRITICAL,
                },
                duration_ms=duration_ms,
                recommendations=[
                    "Verify database connectivity",
                    "Check identity sync job is running correctly",
                    "Review application logs for errors",
                ],
                tenant_id=tenant_id,
            )
        finally:
            if db:
                db.close()
