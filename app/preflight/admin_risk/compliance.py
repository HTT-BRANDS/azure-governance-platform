"""Privileged access compliance assessment check."""

import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.identity import PrivilegedUser
from app.preflight.admin_risk.constants import (
    INACTIVE_ADMIN_DAYS,
    OVERPRIVILEGED_ROLE_THRESHOLD,
    SHARED_ACCOUNT_INDICATORS,
    AdminRiskSeverity,
)
from app.preflight.admin_risk.session import create_admin_risk_session
from app.preflight.base import BasePreflightCheck
from app.preflight.models import CheckCategory, CheckResult, CheckStatus


class AdminComplianceGapCheck(BasePreflightCheck):
    """Check for compliance gaps in privileged access.

    Performs an overall compliance assessment of privileged
    access controls and reports gaps against security baselines.
    """

    def __init__(self):
        super().__init__(
            check_id="admin_compliance_gaps",
            name="Privileged Access Compliance Assessment",
            category=CheckCategory.AZURE_SECURITY,
            description="Overall compliance assessment for privileged access",
            timeout_seconds=20.0,
        )

    async def _execute_check(self, tenant_id: str | None = None) -> CheckResult:
        """Execute compliance gap assessment."""
        start_time = time.perf_counter()
        db: Session | None = None

        try:
            db = create_admin_risk_session()

            # Get all privileged users for the tenant
            query = db.query(PrivilegedUser)
            if tenant_id:
                query = query.filter(PrivilegedUser.tenant_id == tenant_id)

            users = query.all()

            if not users:
                duration_ms = (time.perf_counter() - start_time) * 1000
                return CheckResult(
                    check_id=self.check_id,
                    name=self.name,
                    category=self.category,
                    status=CheckStatus.SKIPPED,
                    message="No privileged users found to assess",
                    details={
                        "severity": AdminRiskSeverity.INFO,
                        "reason": "no_privileged_users",
                    },
                    duration_ms=duration_ms,
                    recommendations=[
                        "Verify identity sync is configured correctly",
                        "Check Azure AD role assignments",
                        "Ensure service principal has required permissions",
                    ],
                    tenant_id=tenant_id,
                )

            # Calculate compliance metrics
            total_unique_users = len({u.user_principal_name for u in users})

            # MFA compliance
            users_without_mfa = set()
            for user in users:
                if not user.mfa_enabled:
                    users_without_mfa.add(user.user_principal_name)

            mfa_compliance_rate = (
                ((total_unique_users - len(users_without_mfa)) / total_unique_users) * 100
                if total_unique_users > 0
                else 0
            )

            # Inactive accounts
            threshold_date = datetime.now(UTC) - timedelta(days=INACTIVE_ADMIN_DAYS)
            inactive_users = set()
            for user in users:
                last_sign_in = user.last_sign_in
                if last_sign_in and last_sign_in.tzinfo is None:
                    last_sign_in = last_sign_in.replace(tzinfo=UTC)
                if last_sign_in and last_sign_in < threshold_date:
                    inactive_users.add(user.user_principal_name)

            # Overprivileged accounts
            user_role_counts: dict[str, int] = defaultdict(int)
            for user in users:
                user_role_counts[user.user_principal_name] += 1

            overprivileged = [
                upn
                for upn, count in user_role_counts.items()
                if count > OVERPRIVILEGED_ROLE_THRESHOLD
            ]

            # Shared accounts
            shared_accounts = []
            for user in users:
                upn_lower = user.user_principal_name.lower()
                if any(ind in upn_lower for ind in SHARED_ACCOUNT_INDICATORS):
                    if user.user_principal_name not in shared_accounts:
                        shared_accounts.append(user.user_principal_name)

            # Calculate overall compliance score
            compliance_issues = len(users_without_mfa) + len(inactive_users) + len(overprivileged)
            compliance_score = max(
                0,
                100
                - (compliance_issues / total_unique_users * 100 if total_unique_users > 0 else 0),
            )

            # Determine status based on compliance score
            if compliance_score >= 90:
                status = CheckStatus.PASS
                severity = AdminRiskSeverity.LOW
            elif compliance_score >= 75:
                status = CheckStatus.WARNING
                severity = AdminRiskSeverity.MEDIUM
            elif compliance_score >= 50:
                status = CheckStatus.WARNING
                severity = AdminRiskSeverity.HIGH
            else:
                status = CheckStatus.FAIL
                severity = AdminRiskSeverity.CRITICAL

            duration_ms = (time.perf_counter() - start_time) * 1000

            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=status,
                message=(
                    f"Compliance score: {compliance_score:.1f}% ({compliance_issues} issues found)"
                ),
                details={
                    "compliance_score": round(compliance_score, 1),
                    "total_privileged_users": total_unique_users,
                    "mfa_compliance_rate": round(mfa_compliance_rate, 1),
                    "issues": {
                        "without_mfa": len(users_without_mfa),
                        "inactive_accounts": len(inactive_users),
                        "overprivileged": len(overprivileged),
                        "shared_accounts": len(shared_accounts),
                    },
                    "severity": severity,
                    "thresholds": {
                        "mfa_required": True,
                        "max_roles": OVERPRIVILEGED_ROLE_THRESHOLD,
                        "inactive_days": INACTIVE_ADMIN_DAYS,
                    },
                },
                duration_ms=duration_ms,
                recommendations=self._generate_recommendations(
                    compliance_score,
                    len(users_without_mfa),
                    len(inactive_users),
                    len(overprivileged),
                    len(shared_accounts),
                ),
                tenant_id=tenant_id,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return CheckResult(
                check_id=self.check_id,
                name=self.name,
                category=self.category,
                status=CheckStatus.FAIL,
                message=f"Failed to assess compliance: {str(e)}",
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

    def _generate_recommendations(
        self,
        compliance_score: float,
        without_mfa: int,
        inactive: int,
        overprivileged: int,
        shared: int,
    ) -> list[str]:
        """Generate recommendations based on compliance issues."""
        recommendations = []

        if compliance_score < 50:
            recommendations.append(
                "CRITICAL: Immediate action required - compliance score below 50%"
            )

        if without_mfa > 0:
            recommendations.append(f"Enable MFA for {without_mfa} privileged accounts immediately")

        if inactive > 0:
            recommendations.append(f"Review and disable {inactive} inactive admin accounts")

        if overprivileged > 0:
            recommendations.append(
                f"Review role assignments for {overprivileged} overprivileged accounts"
            )

        if shared > 0:
            recommendations.append(f"Eliminate {shared} shared admin accounts")

        # General recommendations
        recommendations.extend(
            [
                "Implement regular access reviews for privileged roles",
                "Use Azure AD PIM for just-in-time privileged access",
                "Enable Conditional Access policies for admin accounts",
                "Document and regularly audit all privileged access",
                "Consider implementing privileged access workstations (PAW)",
            ]
        )

        return recommendations
