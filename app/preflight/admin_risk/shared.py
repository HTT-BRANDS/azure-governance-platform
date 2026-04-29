"""Shared/service privileged administrator check."""

import time

from sqlalchemy.orm import Session

from app.models.identity import PrivilegedUser
from app.preflight.admin_risk.constants import (
    CRITICAL_ROLES,
    SHARED_ACCOUNT_INDICATORS,
    AdminRiskSeverity,
)
from app.preflight.admin_risk.session import create_admin_risk_session
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus


class SharedAdminCheck(BasePreflightCheck):
    """Check for shared administrative accounts.

    Identifies accounts that appear to be shared based on naming
    conventions or usage patterns, which is a security risk
    for privileged access.
    """

    def __init__(self):
        super().__init__(
            check_id="admin_shared_accounts",
            name="Shared Admin Account Detection",
            category=CheckCategory.AZURE_SECURITY,
            description="Identify shared or service admin accounts",
            timeout_seconds=15.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute shared admin account check."""
        start_time = time.perf_counter()
        db: Session | None = None

        try:
            db = create_admin_risk_session()

            # Get all privileged users
            query = db.query(PrivilegedUser)
            if tenant_id:
                query = query.filter(PrivilegedUser.tenant_id == tenant_id)

            users = query.all()

            # Identify potential shared accounts
            shared_accounts = []
            seen_users = set()

            for user in users:
                upn_lower = user.user_principal_name.lower()

                # Skip if we've already processed this user
                if user.user_principal_name in seen_users:
                    continue
                seen_users.add(user.user_principal_name)

                # Check for shared account indicators
                is_shared = any(indicator in upn_lower for indicator in SHARED_ACCOUNT_INDICATORS)

                # Check if it looks like a service account
                is_service = (
                    "svc" in upn_lower or "service" in upn_lower or upn_lower.startswith("sa-")
                )

                if is_shared or is_service:
                    # Get all roles for this user
                    user_query = db.query(PrivilegedUser).filter(
                        PrivilegedUser.user_principal_name == user.user_principal_name
                    )
                    if tenant_id:
                        user_query = user_query.filter(PrivilegedUser.tenant_id == tenant_id)

                    user_roles = user_query.all()
                    roles = [r.role_name for r in user_roles]
                    has_critical = any(r in CRITICAL_ROLES for r in roles)

                    shared_accounts.append(
                        {
                            "user_principal_name": user.user_principal_name,
                            "display_name": user.display_name,
                            "account_type": ("service" if is_service else "shared"),
                            "roles": roles,
                            "role_count": len(roles),
                            "has_critical_role": has_critical,
                            "mfa_enabled": bool(user.mfa_enabled),
                            "last_sign_in": (
                                user.last_sign_in.isoformat() if user.last_sign_in else None
                            ),
                            "match_reason": (
                                "contains_shared_indicator"
                                if is_shared
                                else "service_account_pattern"
                            ),
                        }
                    )

            duration_ms = (time.perf_counter() - start_time) * 1000

            if shared_accounts:
                critical_count = sum(1 for a in shared_accounts if a["has_critical_role"])
                without_mfa = sum(1 for a in shared_accounts if not a["mfa_enabled"])

                if critical_count > 0:
                    status = CheckStatus.FAIL
                    severity = AdminRiskSeverity.CRITICAL
                else:
                    status = CheckStatus.WARNING
                    severity = AdminRiskSeverity.HIGH

                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=status,
                    message=(f"{len(shared_accounts)} shared/service admin accounts detected"),
                    details={
                        "shared_account_count": len(shared_accounts),
                        "with_critical_roles": critical_count,
                        "without_mfa": without_mfa,
                        "severity": severity,
                        "shared_indicators": SHARED_ACCOUNT_INDICATORS,
                        "accounts": shared_accounts,
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Eliminate shared admin accounts - assign individual accounts",
                        "Use Azure AD PIM for shared responsibilities",
                        "Implement privileged access workstations (PAW) for admin tasks",
                        "Enable MFA on all shared accounts immediately",
                        "Document and audit all service account usage",
                        "Use managed identities instead of service accounts where possible",
                        "Implement regular credential rotation for service accounts",
                    ],
                    tenant_id=tenant_id,
                )

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.PASS,
                message="No shared admin accounts detected",
                details={
                    "accounts_checked": len(seen_users),
                    "shared_indicators_checked": SHARED_ACCOUNT_INDICATORS,
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
                message=f"Failed to check for shared accounts: {str(e)}",
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
