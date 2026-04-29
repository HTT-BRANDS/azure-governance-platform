"""MFA enforcement check for privileged administrators."""

import time
from typing import Any

from sqlalchemy.orm import Session

from app.models.identity import PrivilegedUser
from app.preflight.admin_risk.constants import CRITICAL_ROLES, AdminRiskSeverity
from app.preflight.admin_risk.session import create_admin_risk_session
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus


class AdminMfaCheck(BasePreflightCheck):
    """Check that privileged accounts have MFA enabled.

    Verifies that all privileged users (admins) have MFA enabled
    as a basic security requirement for privileged access.
    """

    def __init__(self):
        super().__init__(
            check_id="admin_mfa_enabled",
            name="Privileged Account MFA Status",
            category=CheckCategory.AZURE_SECURITY,
            description="Verify all privileged accounts have MFA enabled",
            timeout_seconds=15.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute MFA check for privileged accounts."""
        start_time = time.perf_counter()
        db: Session | None = None

        try:
            db = create_admin_risk_session()

            # Query privileged users without MFA
            query = db.query(PrivilegedUser).filter(PrivilegedUser.mfa_enabled == 0)

            if tenant_id:
                query = query.filter(PrivilegedUser.tenant_id == tenant_id)

            users_without_mfa = query.all()

            # Group by user to avoid duplicates (same user, multiple roles)
            unique_users: dict[str, dict[str, Any]] = {}
            for user in users_without_mfa:
                if user.user_principal_name not in unique_users:
                    unique_users[user.user_principal_name] = {
                        "display_name": user.display_name,
                        "roles": [],
                        "is_critical": False,
                    }
                unique_users[user.user_principal_name]["roles"].append(user.role_name)
                if user.role_name in CRITICAL_ROLES:
                    unique_users[user.user_principal_name]["is_critical"] = True

            duration_ms = (time.perf_counter() - start_time) * 1000

            if unique_users:
                critical_count = sum(1 for u in unique_users.values() if u["is_critical"])

                if critical_count > 0:
                    status = CheckStatus.FAIL
                    severity = AdminRiskSeverity.CRITICAL
                    message = (
                        f"{len(unique_users)} privileged accounts without MFA "
                        f"({critical_count} with critical roles)"
                    )
                else:
                    status = CheckStatus.WARNING
                    severity = AdminRiskSeverity.HIGH
                    message = f"{len(unique_users)} privileged accounts without MFA"

                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=status,
                    message=message,
                    details={
                        "accounts_without_mfa": len(unique_users),
                        "critical_role_count": critical_count,
                        "severity": severity,
                        "accounts": [
                            {
                                "user_principal_name": upn,
                                "display_name": info["display_name"],
                                "roles": info["roles"],
                                "has_critical_role": info["is_critical"],
                            }
                            for upn, info in unique_users.items()
                        ],
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Enable MFA for all privileged accounts immediately",
                        "Require MFA for administrative role assignments",
                        "Use Conditional Access policies to enforce MFA for admins",
                        "Review and update PIM settings to require MFA activation",
                        "Consider emergency access accounts with secure MFA",
                    ],
                    tenant_id=tenant_id,
                )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.PASS,
                message="All privileged accounts have MFA enabled",
                details={
                    "accounts_checked": db.query(PrivilegedUser)
                    .filter(PrivilegedUser.tenant_id == tenant_id if tenant_id else True)
                    .distinct(PrivilegedUser.user_principal_name)
                    .count(),
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
                message=f"Failed to check MFA status: {str(e)}",
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
