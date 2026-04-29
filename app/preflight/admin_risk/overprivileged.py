"""Overprivileged privileged-account check."""

import time
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.models.identity import PrivilegedUser
from app.preflight.admin_risk.constants import (
    CRITICAL_ROLES,
    OVERPRIVILEGED_ROLE_THRESHOLD,
    AdminRiskSeverity,
)
from app.preflight.admin_risk.session import create_admin_risk_session
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus


class OverprivilegedAccountCheck(BasePreflightCheck):
    """Check for accounts with too many privileged roles.

    Identifies users who have been assigned multiple administrative
    roles, which violates the principle of least privilege.
    """

    def __init__(self):
        super().__init__(
            check_id="admin_overprivileged",
            name="Overprivileged Account Detection",
            category=CheckCategory.AZURE_SECURITY,
            description="Identify accounts with excessive role assignments",
            timeout_seconds=15.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute overprivileged account check."""
        start_time = time.perf_counter()
        db: Session | None = None

        try:
            db = create_admin_risk_session()

            # Get all privileged users
            query = db.query(PrivilegedUser)
            if tenant_id:
                query = query.filter(PrivilegedUser.tenant_id == tenant_id)

            users = query.all()

            # Count roles per user
            user_roles: dict[str, dict[str, Any]] = defaultdict(
                lambda: {"roles": [], "display_name": "", "tenant_id": ""}
            )
            for user in users:
                user_roles[user.user_principal_name]["roles"].append(
                    {
                        "name": user.role_name,
                        "scope": user.role_scope,
                        "is_permanent": bool(user.is_permanent),
                    }
                )
                user_roles[user.user_principal_name]["display_name"] = user.display_name
                user_roles[user.user_principal_name]["tenant_id"] = user.tenant_id

            # Find overprivileged users
            overprivileged = []
            for upn, data in user_roles.items():
                role_count = len(data["roles"])
                if role_count > OVERPRIVILEGED_ROLE_THRESHOLD:
                    has_critical = any(r["name"] in CRITICAL_ROLES for r in data["roles"])
                    overprivileged.append(
                        {
                            "user_principal_name": upn,
                            "display_name": data["display_name"],
                            "tenant_id": data["tenant_id"],
                            "role_count": role_count,
                            "roles": [r["name"] for r in data["roles"]],
                            "has_critical_role": has_critical,
                        }
                    )

            duration_ms = (time.perf_counter() - start_time) * 1000

            if overprivileged:
                critical_count = sum(1 for u in overprivileged if u["has_critical_role"])

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
                        f"{len(overprivileged)} accounts with excessive "
                        f"privileges (> {OVERPRIVILEGED_ROLE_THRESHOLD} roles)"
                    ),
                    details={
                        "overprivileged_count": len(overprivileged),
                        "critical_role_violations": critical_count,
                        "role_threshold": OVERPRIVILEGED_ROLE_THRESHOLD,
                        "severity": severity,
                        "accounts": overprivileged,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Review role assignments and remove unnecessary privileges",
                        "Apply principle of least privilege - one role per user where possible",
                        "Use PIM for temporary access instead of permanent assignments",
                        "Consider role consolidation - create custom roles for specific needs",
                        "Audit role assignments quarterly",
                        "Document business justification for multiple role assignments",
                    ],
                    tenant_id=tenant_id,
                )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.PASS,
                message="No overprivileged accounts detected",
                details={
                    "accounts_checked": len(user_roles),
                    "role_threshold": OVERPRIVILEGED_ROLE_THRESHOLD,
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
                message=f"Failed to check for overprivileged accounts: {str(e)}",
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
