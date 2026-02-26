"""Identity governance service."""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.identity import IdentitySnapshot, PrivilegedUser
from app.models.tenant import Tenant
from app.schemas.identity import (
    GuestAccount,
    IdentitySummary,
    PrivilegedAccount,
    StaleAccount,
    TenantIdentitySummary,
)

logger = logging.getLogger(__name__)


class IdentityService:
    """Service for identity governance operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_identity_summary(self) -> IdentitySummary:
        """Get aggregated identity summary across all tenants."""
        tenants = self.db.query(Tenant).filter(Tenant.is_active == True).all()

        total_users = 0
        active_users = 0
        guest_users = 0
        mfa_enabled = 0
        mfa_disabled = 0
        privileged_users = 0
        stale_accounts = 0
        service_principals = 0

        tenant_summaries = []

        for tenant in tenants:
            # Get latest identity snapshot
            latest = (
                self.db.query(IdentitySnapshot)
                .filter(IdentitySnapshot.tenant_id == tenant.id)
                .order_by(IdentitySnapshot.snapshot_date.desc())
                .first()
            )

            if latest:
                total_users += latest.total_users
                active_users += latest.active_users
                guest_users += latest.guest_users
                mfa_enabled += latest.mfa_enabled_users
                mfa_disabled += latest.mfa_disabled_users
                privileged_users += latest.privileged_users
                stale_accounts += latest.stale_accounts_30d
                service_principals += latest.service_principals

                # Calculate MFA percent for tenant
                tenant_mfa_percent = 0.0
                if latest.total_users > 0:
                    tenant_mfa_percent = (
                        latest.mfa_enabled_users / latest.total_users * 100
                    )

                tenant_summaries.append(
                    TenantIdentitySummary(
                        tenant_id=tenant.id,
                        tenant_name=tenant.name,
                        total_users=latest.total_users,
                        guest_users=latest.guest_users,
                        mfa_enabled_percent=tenant_mfa_percent,
                        privileged_users=latest.privileged_users,
                        stale_accounts_30d=latest.stale_accounts_30d,
                        stale_accounts_90d=latest.stale_accounts_90d,
                    )
                )

        # Calculate overall MFA percent
        overall_mfa_percent = 0.0
        if total_users > 0:
            overall_mfa_percent = mfa_enabled / total_users * 100

        return IdentitySummary(
            total_users=total_users,
            active_users=active_users,
            guest_users=guest_users,
            mfa_enabled_percent=overall_mfa_percent,
            privileged_users=privileged_users,
            stale_accounts=stale_accounts,
            service_principals=service_principals,
            by_tenant=tenant_summaries,
        )

    def get_privileged_accounts(
        self, tenant_id: Optional[str] = None
    ) -> List[PrivilegedAccount]:
        """Get privileged account details."""
        query = self.db.query(PrivilegedUser)

        if tenant_id:
            query = query.filter(PrivilegedUser.tenant_id == tenant_id)

        users = query.order_by(PrivilegedUser.role_name).all()

        tenants = {t.id: t.name for t in self.db.query(Tenant).all()}

        return [
            PrivilegedAccount(
                tenant_id=u.tenant_id,
                tenant_name=tenants.get(u.tenant_id, "Unknown"),
                user_principal_name=u.user_principal_name,
                display_name=u.display_name or "",
                user_type=u.user_type or "Member",
                role_name=u.role_name,
                role_scope=u.role_scope or "",
                is_permanent=bool(u.is_permanent),
                mfa_enabled=bool(u.mfa_enabled),
                last_sign_in=u.last_sign_in,
                risk_level=self._calculate_risk_level(u),
            )
            for u in users
        ]

    def _calculate_risk_level(self, user: PrivilegedUser) -> str:
        """Calculate risk level for a privileged user."""
        risk_score = 0

        # Guest with privileged access = high risk
        if user.user_type == "Guest":
            risk_score += 3

        # No MFA = higher risk
        if not user.mfa_enabled:
            risk_score += 2

        # Permanent assignment = higher risk than PIM
        if user.is_permanent:
            risk_score += 1

        # No recent sign-in = potential stale account
        if user.last_sign_in:
            days_since_signin = (datetime.utcnow() - user.last_sign_in).days
            if days_since_signin > 30:
                risk_score += 1
            if days_since_signin > 90:
                risk_score += 1

        # Map score to level
        if risk_score >= 5:
            return "High"
        elif risk_score >= 3:
            return "Medium"
        return "Low"

    def get_guest_accounts(
        self, tenant_id: Optional[str] = None, stale_only: bool = False
    ) -> List[GuestAccount]:
        """Get guest account details."""
        # For MVP, we'd query from a cached table of guest users
        # This is a placeholder that would be populated by the sync job
        return []

    def get_stale_accounts(
        self, days_inactive: int = 30, tenant_id: Optional[str] = None
    ) -> List[StaleAccount]:
        """Get stale account details."""
        # For MVP, this would be populated by the sync job
        # comparing last sign-in dates
        return []
