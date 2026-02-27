"""Riverside Service - Main service class and exports.

This module provides the main RiversideService class that coordinates
sync operations and queries for Riverside compliance tracking.
"""

from typing import TYPE_CHECKING

from app.api.services.riverside_service.constants import (
    ALL_TENANTS,
    CURRENT_MATURITY_SCORE,
    FINANCIAL_RISK,
    MFA_THRESHOLD_PERCENTAGES,
    RIVERSIDE_DEADLINE,
    RIVERSIDE_SYNC_INTERVAL_HOURS,
    RIVERSIDE_TENANTS,
    TARGET_MATURITY_SCORE,
    DeadlinePhase,
    MFAStatus,
    RequirementLevel,
    RequirementStatus,
    RiversideRequirementCategory,
)
from app.api.services.riverside_service.models import (
    AggregateMFAStatus,
    MFAMaturityScore,
    RiversideComplianceSummary,
    RiversideExecutiveSummary,
    RiversideRequirement,
    RiversideThreatMetrics,
    TenantRequirementTracker,
    TenantRiversideSummary,
)
from app.api.services.riverside_service.queries import (
    get_gaps,
    get_maturity_scores,
    get_mfa_status,
    get_requirements,
    get_riverside_summary,
)
from app.api.services.riverside_service.sync import (
    sync_riverside_device_compliance,
    sync_riverside_maturity_scores,
    sync_riverside_mfa,
    sync_riverside_requirements,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

__all__ = [
    # Main service
    "RiversideService",
    # Constants
    "ALL_TENANTS",
    "CURRENT_MATURITY_SCORE",
    "FINANCIAL_RISK",
    "MFA_THRESHOLD_PERCENTAGES",
    "RIVERSIDE_DEADLINE",
    "RIVERSIDE_SYNC_INTERVAL_HOURS",
    "RIVERSIDE_TENANTS",
    "TARGET_MATURITY_SCORE",
    # Enums
    "DeadlinePhase",
    "MFAStatus",
    "RequirementLevel",
    "RequirementStatus",
    "RiversideRequirementCategory",
    # Models
    "AggregateMFAStatus",
    "MFAMaturityScore",
    "RiversideComplianceSummary",
    "RiversideExecutiveSummary",
    "RiversideRequirement",
    "RiversideThreatMetrics",
    "TenantRequirementTracker",
    "TenantRiversideSummary",
]


class RiversideService:
    """Service for managing Riverside compliance governance across Microsoft 365 tenants.

    This service provides executive-level visibility into compliance requirements
    with the July 8, 2026 deadline and $4M financial risk.
    """

    def __init__(self, db: "Session") -> None:
        """Initialize RiversideService with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # ========================================================================
    # SYNC METHODS
    # ========================================================================

    async def sync_riverside_mfa(self) -> dict:
        """Sync MFA data from Microsoft Graph API for all tenants.

        Returns:
            Dict with sync results by tenant.
        """
        return await sync_riverside_mfa(self.db)

    async def sync_riverside_device_compliance(self) -> dict:
        """Sync device compliance data from Intune/Graph API for all tenants.

        Returns:
            Dict with sync results by tenant.
        """
        return await sync_riverside_device_compliance(self.db)

    async def sync_riverside_requirements(self) -> dict:
        """Sync requirement status from database and Graph API indicators.

        Returns:
            Dict with sync results.
        """
        return await sync_riverside_requirements(self.db)

    async def sync_riverside_maturity_scores(self) -> dict:
        """Calculate and sync maturity scores based on current compliance data.

        Returns:
            Dict with maturity scores by tenant.
        """
        return await sync_riverside_maturity_scores(self.db)

    async def sync_all(self) -> dict:
        """Run all Riverside sync operations.

        Returns:
            Dict with all sync results.
        """
        results = {
            "mfa": await self.sync_riverside_mfa(),
            "device_compliance": await self.sync_riverside_device_compliance(),
            "requirements": await self.sync_riverside_requirements(),
            "maturity_scores": await self.sync_riverside_maturity_scores(),
        }
        return results

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_riverside_summary(self) -> dict:
        """Get executive summary for Riverside compliance dashboard.

        Returns:
            Dict with comprehensive executive summary including:
            - Days to deadline
            - Financial risk
            - Overall maturity
            - MFA coverage
            - Device compliance
            - Critical gaps
        """
        return get_riverside_summary(self.db)

    def get_mfa_status(self) -> dict:
        """Get detailed MFA status for all tenants.

        Returns:
            Dict with MFA metrics including per-tenant breakdown.
        """
        return get_mfa_status(self.db)

    def get_maturity_scores(self) -> dict:
        """Get maturity scores for all domains and tenants.

        Returns:
            Dict with maturity scores including domain breakdowns.
        """
        return get_maturity_scores(self.db)

    def get_requirements(
        self,
        category: str | None = None,
        priority: str | None = None,
        status: str | None = None
    ) -> dict:
        """Get requirements list with optional filtering.

        Args:
            category: Filter by category (IAM, GS, DS)
            priority: Filter by priority (P0, P1, P2)
            status: Filter by status (not_started, in_progress, completed, blocked)

        Returns:
            Dict with filtered requirements and statistics.
        """
        return get_requirements(self.db, category, priority, status)

    def get_gaps(self) -> dict:
        """Get critical gaps analysis.

        Returns:
            Dict with critical gaps categorized by priority.
        """
        return get_gaps(self.db)
