"""Riverside Company compliance tracking service.

Business logic service for Riverside operations including compliance calculations,
MFA enrollment tracking, requirement management, and dashboard data aggregation.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.riverside import (
    RequirementCategory,
    RequirementPriority,
    RequirementStatus,
    RiversideCompliance,
    RiversideDeviceCompliance,
    RiversideMFA,
    RiversideRequirement,
    RiversideThreatData,
)
from app.models.tenant import Tenant
from app.schemas.riverside import (
    BulkUpdateItem,
    BulkUpdateResponse,
    RiversideComplianceResponse,
    RiversideDashboardSummary,
    RiversideMFAResponse,
    RiversideRequirementResponse,
    RiversideTenantSummary,
)

logger = logging.getLogger(__name__)

# Constants
RIVERSIDE_DEADLINE = date(2026, 7, 8)
TARGET_MATURITY_SCORE = 3.0


class RiversideService:
    """Service for Riverside compliance tracking operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_compliance_summary(
        self, tenant_id: str | None = None
    ) -> list[RiversideComplianceResponse]:
        """Get compliance summary, optionally filtered by tenant.

        Args:
            tenant_id: Optional tenant ID to filter by

        Returns:
            List of compliance summary records
        """
        query = self.db.query(RiversideCompliance)

        if tenant_id:
            query = query.filter(RiversideCompliance.tenant_id == tenant_id)

        records = query.order_by(RiversideCompliance.tenant_id).all()
        return [RiversideComplianceResponse.model_validate(r) for r in records]

    def get_mfa_stats(
        self, tenant_id: str | None = None
    ) -> list[RiversideMFAResponse]:
        """Get MFA enrollment statistics, optionally filtered by tenant.

        Calculates MFA coverage percentages per tenant including admin MFA stats.

        Args:
            tenant_id: Optional tenant ID to filter by

        Returns:
            List of MFA statistics records
        """
        query = self.db.query(RiversideMFA)

        if tenant_id:
            query = query.filter(RiversideMFA.tenant_id == tenant_id)

        # Get the latest snapshot per tenant
        subquery = (
            self.db.query(
                RiversideMFA.tenant_id,
                func.max(RiversideMFA.snapshot_date).label("max_snapshot"),
            )
            .group_by(RiversideMFA.tenant_id)
            .subquery()
        )

        query = (
            self.db.query(RiversideMFA)
            .join(
                subquery,
                (RiversideMFA.tenant_id == subquery.c.tenant_id)
                & (RiversideMFA.snapshot_date == subquery.c.max_snapshot),
            )
            .order_by(RiversideMFA.tenant_id)
        )

        if tenant_id:
            query = query.filter(RiversideMFA.tenant_id == tenant_id)

        records = query.all()
        return [RiversideMFAResponse.model_validate(r) for r in records]

    def get_requirements_by_status(
        self,
        status: RequirementStatus | None = None,
        tenant_id: str | None = None,
        category: RequirementCategory | None = None,
        priority: RequirementPriority | None = None,
    ) -> list[RiversideRequirementResponse]:
        """Get requirements filtered by status and other criteria.

        Args:
            status: Filter by requirement status
            tenant_id: Optional tenant ID to filter by
            category: Optional category filter
            priority: Optional priority filter

        Returns:
            List of requirement records matching criteria
        """
        query = self.db.query(RiversideRequirement)

        if status:
            query = query.filter(RiversideRequirement.status == status)
        if tenant_id:
            query = query.filter(RiversideRequirement.tenant_id == tenant_id)
        if category:
            query = query.filter(RiversideRequirement.category == category)
        if priority:
            query = query.filter(RiversideRequirement.priority == priority)

        records = query.order_by(
            RiversideRequirement.priority,
            RiversideRequirement.due_date,
            RiversideRequirement.requirement_id,
        ).all()

        return [RiversideRequirementResponse.model_validate(r) for r in records]

    def update_requirement_status(
        self,
        requirement_id: int,
        status: RequirementStatus,
        notes: str | None = None,
        evidence_url: str | None = None,
    ) -> RiversideRequirementResponse:
        """Update the status of a requirement.

        Args:
            requirement_id: ID of the requirement to update
            status: New status value
            notes: Optional notes about the update
            evidence_url: Optional evidence URL

        Returns:
            Updated requirement record

        Raises:
            ValueError: If requirement not found
        """
        requirement = (
            self.db.query(RiversideRequirement)
            .filter(RiversideRequirement.id == requirement_id)
            .first()
        )

        if not requirement:
            raise ValueError(f"Requirement with ID {requirement_id} not found")

        requirement.status = status
        requirement.updated_at = datetime.utcnow()

        if status == RequirementStatus.COMPLETED and not requirement.completed_date:
            requirement.completed_date = date.today()

        if notes:
            if requirement.evidence_notes:
                requirement.evidence_notes = f"{requirement.evidence_notes}\n\n{notes}"
            else:
                requirement.evidence_notes = notes

        if evidence_url:
            requirement.evidence_url = evidence_url

        self.db.commit()
        self.db.refresh(requirement)

        return RiversideRequirementResponse.model_validate(requirement)

    def get_dashboard_data(self) -> RiversideDashboardSummary:
        """Get aggregated dashboard data for all Riverside tenants.

        Calculates:
        - Overall maturity averages
        - Requirements completion statistics
        - MFA coverage averages
        - Device compliance averages
        - Requirements grouped by category, priority, and status
        - Days until deadline

        Returns:
            Dashboard summary with aggregated data
        """
        # Get all Riverside tenants
        tenants = self.db.query(Tenant).filter(Tenant.is_active.is_(True)).all()

        # Get latest compliance data per tenant
        compliance_subquery = (
            self.db.query(
                RiversideCompliance.tenant_id,
                func.max(RiversideCompliance.created_at).label("max_created"),
            )
            .group_by(RiversideCompliance.tenant_id)
            .subquery()
        )

        compliance_records = {
            c.tenant_id: c
            for c in self.db.query(RiversideCompliance)
            .join(
                compliance_subquery,
                (RiversideCompliance.tenant_id == compliance_subquery.c.tenant_id)
                & (RiversideCompliance.created_at == compliance_subquery.c.max_created),
            )
            .all()
        }

        # Get latest MFA data per tenant
        mfa_subquery = (
            self.db.query(
                RiversideMFA.tenant_id,
                func.max(RiversideMFA.snapshot_date).label("max_snapshot"),
            )
            .group_by(RiversideMFA.tenant_id)
            .subquery()
        )

        mfa_records = {
            m.tenant_id: m
            for m in self.db.query(RiversideMFA)
            .join(
                mfa_subquery,
                (RiversideMFA.tenant_id == mfa_subquery.c.tenant_id)
                & (RiversideMFA.snapshot_date == mfa_subquery.c.max_snapshot),
            )
            .all()
        }

        # Get latest device compliance per tenant
        device_subquery = (
            self.db.query(
                RiversideDeviceCompliance.tenant_id,
                func.max(RiversideDeviceCompliance.snapshot_date).label("max_snapshot"),
            )
            .group_by(RiversideDeviceCompliance.tenant_id)
            .subquery()
        )

        device_records = {
            d.tenant_id: d
            for d in self.db.query(RiversideDeviceCompliance)
            .join(
                device_subquery,
                (RiversideDeviceCompliance.tenant_id == device_subquery.c.tenant_id)
                & (
                    RiversideDeviceCompliance.snapshot_date
                    == device_subquery.c.max_snapshot
                ),
            )
            .all()
        }

        # Get requirements counts per tenant
        requirements_stats = (
            self.db.query(
                RiversideRequirement.tenant_id,
                func.count(RiversideRequirement.id).label("total"),
                func.sum(
                    func.case(
                        (RiversideRequirement.status == RequirementStatus.COMPLETED, 1),
                        else_=0,
                    )
                ).label("completed"),
            )
            .group_by(RiversideRequirement.tenant_id)
            .all()
        )

        req_stats_by_tenant = {
            r.tenant_id: {"total": r.total, "completed": r.completed or 0}
            for r in requirements_stats
        }

        # Calculate days until deadline
        today = date.today()
        days_until = (RIVERSIDE_DEADLINE - today).days

        # Build tenant summaries
        tenant_summaries: list[RiversideTenantSummary] = []
        total_maturity = 0.0
        total_requirements = 0
        total_completed = 0
        total_mfa_coverage = 0.0
        total_device_compliance = 0.0
        total_critical_gaps = 0

        for tenant in tenants:
            comp = compliance_records.get(tenant.id)
            mfa = mfa_records.get(tenant.id)
            device = device_records.get(tenant.id)
            req_stats = req_stats_by_tenant.get(tenant.id, {"total": 0, "completed": 0})

            maturity_score = (
                comp.overall_maturity_score if comp else 0.0
            )
            mfa_coverage = mfa.mfa_coverage_percentage if mfa else 0.0
            admin_mfa = mfa.admin_mfa_percentage if mfa else 0.0
            device_compliance = device.compliance_percentage if device else 0.0
            critical_gaps = comp.critical_gaps_count if comp else 0

            req_total = req_stats["total"]
            req_completed = req_stats["completed"]
            completion_pct = (
                (req_completed / req_total * 100) if req_total > 0 else 0.0
            )

            tenant_summaries.append(
                RiversideTenantSummary(
                    tenant_id=tenant.id,
                    tenant_name=tenant.name,
                    overall_maturity_score=maturity_score,
                    requirements_completed=req_completed,
                    requirements_total=req_total,
                    completion_percentage=round(completion_pct, 1),
                    mfa_coverage_percentage=round(mfa_coverage, 1),
                    admin_mfa_percentage=round(admin_mfa, 1),
                    device_compliance_percentage=round(device_compliance, 1),
                    critical_gaps_count=critical_gaps,
                    days_until_deadline=days_until,
                )
            )

            total_maturity += maturity_score
            total_requirements += req_total
            total_completed += req_completed
            total_mfa_coverage += mfa_coverage
            total_device_compliance += device_compliance
            total_critical_gaps += critical_gaps

        # Calculate aggregates
        tenant_count = len(tenant_summaries)
        avg_maturity = (
            round(total_maturity / tenant_count, 1) if tenant_count > 0 else 0.0
        )
        avg_mfa = (
            round(total_mfa_coverage / tenant_count, 1) if tenant_count > 0 else 0.0
        )
        avg_device = (
            round(total_device_compliance / tenant_count, 1)
            if tenant_count > 0
            else 0.0
        )
        overall_completion = (
            round(total_completed / total_requirements * 100, 1)
            if total_requirements > 0
            else 0.0
        )

        # Get requirements grouped by category
        category_stats = (
            self.db.query(
                RiversideRequirement.category,
                func.count(RiversideRequirement.id).label("total"),
                func.sum(
                    func.case(
                        (RiversideRequirement.status == RequirementStatus.COMPLETED, 1),
                        else_=0,
                    )
                ).label("completed"),
            )
            .group_by(RiversideRequirement.category)
            .all()
        )

        requirements_by_category: dict[str, dict[str, int]] = {
            c.category.value: {"completed": c.completed or 0, "total": c.total}
            for c in category_stats
        }

        # Get requirements grouped by priority
        priority_stats = (
            self.db.query(
                RiversideRequirement.priority,
                func.count(RiversideRequirement.id).label("total"),
                func.sum(
                    func.case(
                        (RiversideRequirement.status == RequirementStatus.COMPLETED, 1),
                        else_=0,
                    )
                ).label("completed"),
            )
            .group_by(RiversideRequirement.priority)
            .all()
        )

        requirements_by_priority: dict[str, dict[str, int]] = {
            p.priority.value: {"completed": p.completed or 0, "total": p.total}
            for p in priority_stats
        }

        # Get requirements grouped by status
        status_stats = (
            self.db.query(
                RiversideRequirement.status,
                func.count(RiversideRequirement.id).label("count"),
            )
            .group_by(RiversideRequirement.status)
            .all()
        )

        requirements_by_status: dict[str, int] = {
            s.status.value: s.count for s in status_stats
        }

        return RiversideDashboardSummary(
            total_tenants=tenant_count,
            deadline_date=RIVERSIDE_DEADLINE,
            days_until_deadline=days_until,
            overall_maturity_average=avg_maturity,
            overall_maturity_target=TARGET_MATURITY_SCORE,
            total_requirements_completed=total_completed,
            total_requirements=total_requirements,
            overall_completion_percentage=overall_completion,
            total_critical_gaps=total_critical_gaps,
            average_mfa_coverage=avg_mfa,
            average_device_compliance=avg_device,
            financial_risk_exposure="$20M",
            tenant_summaries=tenant_summaries,
            requirements_by_category=requirements_by_category,
            requirements_by_priority=requirements_by_priority,
            requirements_by_status=requirements_by_status,
        )

    def bulk_update_requirements(
        self, updates: list[BulkUpdateItem]
    ) -> BulkUpdateResponse:
        """Perform bulk update operations on requirements.

        Args:
            updates: List of bulk update items containing requirement IDs
                    and field updates

        Returns:
            Bulk update response with success/failure counts
        """
        processed = 0
        succeeded = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for item in updates:
            processed += 1
            try:
                requirement = (
                    self.db.query(RiversideRequirement)
                    .filter(RiversideRequirement.id == item.id)
                    .first()
                )

                if not requirement:
                    failed += 1
                    errors.append(
                        {"id": item.id, "error": f"Requirement {item.id} not found"}
                    )
                    continue

                # Validate and apply updates
                valid_fields = {
                    "status",
                    "evidence_url",
                    "evidence_notes",
                    "due_date",
                    "owner",
                }

                for field, value in item.updates.items():
                    if field not in valid_fields:
                        continue

                    if field == "status":
                        # Validate status value
                        try:
                            requirement.status = RequirementStatus(value)
                        except ValueError:
                            failed += 1
                            errors.append(
                                {
                                    "id": item.id,
                                    "error": f"Invalid status value: {value}",
                                }
                            )
                            continue
                    elif field == "due_date" and value:
                        # Parse date string to date object
                        if isinstance(value, str):
                            requirement.due_date = date.fromisoformat(value)
                        else:
                            requirement.due_date = value
                    else:
                        setattr(requirement, field, value)

                # Update completed_date if status changed to completed
                if (
                    requirement.status == RequirementStatus.COMPLETED
                    and not requirement.completed_date
                ):
                    requirement.completed_date = date.today()

                requirement.updated_at = datetime.utcnow()
                succeeded += 1

            except Exception as e:
                failed += 1
                errors.append({"id": item.id, "error": str(e)})

        self.db.commit()

        return BulkUpdateResponse(
            processed=processed,
            succeeded=succeeded,
            failed=failed,
            errors=errors,
        )

    def get_upcoming_deadlines(
        self, days: int = 30, tenant_id: str | None = None
    ) -> list[RiversideRequirementResponse]:
        """Get requirements with upcoming deadlines.

        Args:
            days: Number of days to look ahead
            tenant_id: Optional tenant ID to filter by

        Returns:
            List of requirements with deadlines within the specified days
        """
        cutoff_date = date.today() + timedelta(days=days)

        query = self.db.query(RiversideRequirement).filter(
            RiversideRequirement.due_date <= cutoff_date,
            RiversideRequirement.due_date >= date.today(),
            RiversideRequirement.status != RequirementStatus.COMPLETED,
        )

        if tenant_id:
            query = query.filter(RiversideRequirement.tenant_id == tenant_id)

        records = query.order_by(RiversideRequirement.due_date).all()
        return [RiversideRequirementResponse.model_validate(r) for r in records]

    def get_critical_gaps(
        self, tenant_id: str | None = None
    ) -> list[RiversideRequirementResponse]:
        """Get P0 (critical) requirements that are not completed.

        Args:
            tenant_id: Optional tenant ID to filter by

        Returns:
            List of critical requirements requiring attention
        """
        query = self.db.query(RiversideRequirement).filter(
            RiversideRequirement.priority == RequirementPriority.P0,
            RiversideRequirement.status != RequirementStatus.COMPLETED,
        )

        if tenant_id:
            query = query.filter(RiversideRequirement.tenant_id == tenant_id)

        records = query.order_by(RiversideRequirement.due_date).all()
        return [RiversideRequirementResponse.model_validate(r) for r in records]


# =============================================================================
# Standalone Business Logic Functions
# =============================================================================
# These functions provide aggregated analysis and calculation capabilities
# for the Riverside compliance tracking system.


def calculate_compliance_summary(db: Session) -> dict:
    """Calculate overall compliance percentages and maturity scores.

    This function computes aggregated compliance metrics across all Riverside
    tenants including overall compliance percentage, average maturity score,
    and weighted maturity calculations based on tenant sizes.

    Args:
        db: Database session for querying compliance data.

    Returns:
        Dictionary containing:
            - overall_compliance_percentage: Weighted compliance percentage
            - average_maturity_score: Average maturity across all tenants
            - weighted_maturity_score: Maturity weighted by user count
            - total_critical_gaps: Total number of critical gaps
            - tenants_analyzed: Number of tenants included
            - maturity_distribution: Breakdown by maturity ranges
            - compliance_trend: Direction of compliance (improving/stable/declining)

    Raises:
        ValueError: If no compliance data is available.
    """
    # Get latest compliance data per tenant
    compliance_subquery = (
        db.query(
            RiversideCompliance.tenant_id,
            func.max(RiversideCompliance.created_at).label("max_created"),
        )
        .group_by(RiversideCompliance.tenant_id)
        .subquery()
    )

    compliance_records = (
        db.query(RiversideCompliance)
        .join(
            compliance_subquery,
            (RiversideCompliance.tenant_id == compliance_subquery.c.tenant_id)
            & (RiversideCompliance.created_at == compliance_subquery.c.max_created),
        )
        .all()
    )

    if not compliance_records:
        raise ValueError("No compliance data available for analysis")

    total_tenants = len(compliance_records)
    total_maturity = 0.0
    total_critical_gaps = 0
    total_requirements = 0
    total_completed = 0

    # Maturity distribution counters
    maturity_distribution = {
        "below_2": 0,  # Critical risk
        "2_to_3": 0,   # Needs improvement
        "3_to_4": 0,   # Good
        "above_4": 0,  # Excellent
    }

    for record in compliance_records:
        maturity = record.overall_maturity_score
        total_maturity += maturity
        total_critical_gaps += record.critical_gaps_count
        total_requirements += record.requirements_total
        total_completed += record.requirements_completed

        # Categorize maturity
        if maturity < 2.0:
            maturity_distribution["below_2"] += 1
        elif maturity < 3.0:
            maturity_distribution["2_to_3"] += 1
        elif maturity < 4.0:
            maturity_distribution["3_to_4"] += 1
        else:
            maturity_distribution["above_4"] += 1

    avg_maturity = total_maturity / total_tenants if total_tenants > 0 else 0.0
    compliance_percentage = (
        (total_completed / total_requirements * 100)
        if total_requirements > 0
        else 0.0
    )

    # Calculate trend based on completed vs total ratio
    trend = "stable"
    if compliance_percentage >= 70:
        trend = "improving"
    elif compliance_percentage < 30:
        trend = "critical"
    elif compliance_percentage < 50:
        trend = "declining"

    return {
        "overall_compliance_percentage": round(compliance_percentage, 1),
        "average_maturity_score": round(avg_maturity, 1),
        "weighted_maturity_score": round(avg_maturity, 1),  # Placeholder for future weighting
        "total_critical_gaps": total_critical_gaps,
        "tenants_analyzed": total_tenants,
        "maturity_distribution": maturity_distribution,
        "compliance_trend": trend,
        "requirements_completed": total_completed,
        "requirements_total": total_requirements,
    }


def analyze_mfa_gaps(db: Session, tenant_id: str | None = None) -> dict:
    """Analyze MFA enrollment gaps and calculate coverage deficits.

    Identifies users without MFA, calculates coverage gaps at both tenant
    and aggregate levels, and provides actionable gap analysis for security
    remediation planning.

    Args:
        db: Database session for querying MFA data.
        tenant_id: Optional tenant ID to filter analysis to a specific tenant.

    Returns:
        Dictionary containing:
            - overall_coverage_percentage: Average MFA coverage across tenants
            - admin_coverage_percentage: Average admin MFA coverage
            - total_unprotected_users: Total count of users without MFA
            - coverage_gap_percentage: Percentage gap from 100% coverage
            - high_risk_tenants: List of tenants with <50% coverage
            - tenant_breakdown: Per-tenant MFA statistics
            - recommendations: List of remediation recommendations

    Raises:
        ValueError: If no MFA data is available.
    """
    # Get latest MFA data per tenant
    mfa_subquery = (
        db.query(
            RiversideMFA.tenant_id,
            func.max(RiversideMFA.snapshot_date).label("max_snapshot"),
        )
        .group_by(RiversideMFA.tenant_id)
        .subquery()
    )

    query = db.query(RiversideMFA).join(
        mfa_subquery,
        (RiversideMFA.tenant_id == mfa_subquery.c.tenant_id)
        & (RiversideMFA.snapshot_date == mfa_subquery.c.max_snapshot),
    )

    if tenant_id:
        query = query.filter(RiversideMFA.tenant_id == tenant_id)

    mfa_records = query.all()

    if not mfa_records:
        raise ValueError("No MFA data available for analysis")

    total_coverage = 0.0
    total_admin_coverage = 0.0
    total_unprotected = 0
    total_users = 0
    high_risk_tenants: list[dict] = []
    tenant_breakdown: list[dict] = []

    for record in mfa_records:
        coverage = record.mfa_coverage_percentage
        admin_coverage = record.admin_mfa_percentage
        unprotected = record.unprotected_users

        total_coverage += coverage
        total_admin_coverage += admin_coverage
        total_unprotected += unprotected
        total_users += record.total_users

        tenant_info = {
            "tenant_id": record.tenant_id,
            "coverage_percentage": round(coverage, 1),
            "admin_coverage_percentage": round(admin_coverage, 1),
            "unprotected_users": unprotected,
            "total_users": record.total_users,
            "risk_level": "critical" if coverage < 50 else "high" if coverage < 75 else "medium",
        }
        tenant_breakdown.append(tenant_info)

        # Identify high-risk tenants (< 50% coverage)
        if coverage < 50:
            high_risk_tenants.append(tenant_info)

    tenant_count = len(mfa_records)
    avg_coverage = total_coverage / tenant_count if tenant_count > 0 else 0.0
    avg_admin_coverage = total_admin_coverage / tenant_count if tenant_count > 0 else 0.0
    coverage_gap = 100.0 - avg_coverage

    # Generate recommendations based on gaps
    recommendations: list[str] = []
    if avg_coverage < 50:
        recommendations.append(
            "CRITICAL: Implement emergency MFA rollout - coverage below 50%"
        )
    if avg_admin_coverage < 100:
        recommendations.append(
            "URGENT: Ensure 100% admin MFA coverage before addressing user MFA"
        )
    if high_risk_tenants:
        recommendations.append(
            f"Prioritize {len(high_risk_tenants)} high-risk tenants for immediate remediation"
        )
    if avg_coverage < 90:
        recommendations.append(
            "Consider conditional access policies to enforce MFA for critical applications"
        )

    return {
        "overall_coverage_percentage": round(avg_coverage, 1),
        "admin_coverage_percentage": round(avg_admin_coverage, 1),
        "total_unprotected_users": total_unprotected,
        "total_users": total_users,
        "coverage_gap_percentage": round(coverage_gap, 1),
        "high_risk_tenants": high_risk_tenants,
        "high_risk_count": len(high_risk_tenants),
        "tenant_breakdown": tenant_breakdown,
        "recommendations": recommendations,
    }


def track_requirement_progress(db: Session, requirement_id: int) -> dict:
    """Track completion status of a specific requirement over time.

    Analyzes the historical progress of a requirement including status
    changes, completion timeline, and velocity metrics.

    Args:
        db: Database session for querying requirement data.
        requirement_id: The unique identifier of the requirement to track.

    Returns:
        Dictionary containing:
            - requirement_id: The tracked requirement ID
            - current_status: Current status of the requirement
            - progress_percentage: Estimated progress percentage
            - days_in_current_status: Days spent in current status
            - estimated_completion: Estimated completion date
            - velocity: Progress velocity (requirements per week)
            - blockers: List of identified blockers
            - related_requirements: IDs of related requirements in same category

    Raises:
        ValueError: If the requirement is not found.
    """
    requirement = (
        db.query(RiversideRequirement)
        .filter(RiversideRequirement.id == requirement_id)
        .first()
    )

    if not requirement:
        raise ValueError(f"Requirement with ID {requirement_id} not found")

    # Calculate progress percentage based on status
    status_progress_map = {
        RequirementStatus.NOT_STARTED: 0,
        RequirementStatus.BLOCKED: 0,
        RequirementStatus.IN_PROGRESS: 50,
        RequirementStatus.COMPLETED: 100,
    }
    progress_percentage = status_progress_map.get(requirement.status, 0)

    # Calculate days in current status
    today = date.today()
    days_in_status = 0
    if requirement.updated_at:
        days_in_status = (today - requirement.updated_at.date()).days

    # Estimate completion based on due date and progress
    estimated_completion = None
    if requirement.due_date:
        if requirement.status == RequirementStatus.COMPLETED:
            estimated_completion = requirement.completed_date
        elif progress_percentage > 0 and requirement.due_date >= today:
            estimated_completion = requirement.due_date

    # Find related requirements in same category
    related = (
        db.query(RiversideRequirement)
        .filter(
            RiversideRequirement.category == requirement.category,
            RiversideRequirement.id != requirement_id,
            RiversideRequirement.tenant_id == requirement.tenant_id,
        )
        .limit(5)
        .all()
    )

    related_ids = [r.id for r in related]

    # Calculate velocity based on tenant's overall completion rate
    tenant_completed = (
        db.query(func.count(RiversideRequirement.id))
        .filter(
            RiversideRequirement.tenant_id == requirement.tenant_id,
            RiversideRequirement.status == RequirementStatus.COMPLETED,
        )
        .scalar()
        or 0
    )

    tenant_total = (
        db.query(func.count(RiversideRequirement.id))
        .filter(RiversideRequirement.tenant_id == requirement.tenant_id)
        .scalar()
        or 1
    )

    velocity = (tenant_completed / tenant_total) * 10  # Rough velocity metric

    # Identify blockers
    blockers: list[str] = []
    if requirement.status == RequirementStatus.BLOCKED:
        blockers.append("Requirement explicitly marked as blocked")
    if days_in_status > 30 and requirement.status != RequirementStatus.COMPLETED:
        blockers.append(f"Stalled for {days_in_status} days without progress")
    if requirement.due_date and requirement.due_date < today:
        blockers.append("Past due date")

    return {
        "requirement_id": requirement_id,
        "requirement_identifier": requirement.requirement_id,
        "title": requirement.title,
        "current_status": requirement.status.value,
        "category": requirement.category.value,
        "priority": requirement.priority.value,
        "progress_percentage": progress_percentage,
        "days_in_current_status": days_in_status,
        "due_date": requirement.due_date.isoformat() if requirement.due_date else None,
        "completed_date": (
            requirement.completed_date.isoformat() if requirement.completed_date else None
        ),
        "estimated_completion": (
            estimated_completion.isoformat() if estimated_completion else None
        ),
        "velocity": round(velocity, 2),
        "blockers": blockers,
        "related_requirements": related_ids,
        "owner": requirement.owner,
        "has_evidence": bool(requirement.evidence_url),
    }


def get_deadline_status(db: Session, days_window: int = 30) -> dict:
    """Calculate days until deadline and identify overdue items.

    Monitors the July 8, 2026 Riverside compliance deadline, calculating
    time remaining and identifying requirements that are overdue or at risk.

    Args:
        db: Database session for querying deadline data.
        days_window: Number of days to look ahead for upcoming deadlines.

    Returns:
        Dictionary containing:
            - deadline_date: The compliance deadline (2026-07-08)
            - days_until_deadline: Days remaining until deadline
            - deadline_status: Status category (at_risk, approaching, on_track)
            - overdue_count: Number of overdue requirements
            - at_risk_count: Requirements due within days_window
            - upcoming_deadlines: List of requirements due soon
            - urgency_score: Calculated urgency metric (0-100)
            - risk_assessment: Overall risk level

    Raises:
        ValueError: If days_window is negative.
    """
    if days_window < 0:
        raise ValueError("days_window must be non-negative")

    today = date.today()
    days_until = (RIVERSIDE_DEADLINE - today).days

    # Determine deadline status
    if days_until < 0:
        deadline_status = "overdue"
    elif days_until < days_window:
        deadline_status = "at_risk"
    elif days_until < 180:  # Less than 6 months
        deadline_status = "approaching"
    else:
        deadline_status = "on_track"

    # Get overdue requirements
    overdue_requirements = (
        db.query(RiversideRequirement)
        .filter(
            RiversideRequirement.due_date < today,
            RiversideRequirement.status != RequirementStatus.COMPLETED,
        )
        .all()
    )

    overdue_count = len(overdue_requirements)

    # Get requirements at risk (due within window)
    cutoff_date = today + timedelta(days=days_window)
    at_risk_requirements = (
        db.query(RiversideRequirement)
        .filter(
            RiversideRequirement.due_date >= today,
            RiversideRequirement.due_date <= cutoff_date,
            RiversideRequirement.status != RequirementStatus.COMPLETED,
        )
        .order_by(RiversideRequirement.due_date)
        .all()
    )

    at_risk_count = len(at_risk_requirements)

    # Format upcoming deadlines
    upcoming_deadlines = [
        {
            "id": req.id,
            "requirement_id": req.requirement_id,
            "title": req.title,
            "due_date": req.due_date.isoformat() if req.due_date else None,
            "days_remaining": (req.due_date - today).days if req.due_date else None,
            "priority": req.priority.value,
            "owner": req.owner,
        }
        for req in at_risk_requirements
    ]

    # Calculate urgency score (0-100)
    total_requirements = (
        db.query(func.count(RiversideRequirement.id)).scalar() or 1
    )
    completed_requirements = (
        db.query(func.count(RiversideRequirement.id))
        .filter(RiversideRequirement.status == RequirementStatus.COMPLETED)
        .scalar()
        or 0
    )

    completion_rate = completed_requirements / total_requirements
    time_remaining_ratio = max(0, days_until) / 365  # Normalize to year

    # Urgency increases as deadline approaches and completion is low
    urgency_score = min(100, max(0, (1 - completion_rate) * 100 + (1 - time_remaining_ratio) * 50))

    # Determine risk assessment
    if overdue_count > 10 or urgency_score > 80:
        risk_assessment = "critical"
    elif overdue_count > 5 or urgency_score > 60:
        risk_assessment = "high"
    elif overdue_count > 0 or urgency_score > 40:
        risk_assessment = "medium"
    else:
        risk_assessment = "low"

    return {
        "deadline_date": RIVERSIDE_DEADLINE.isoformat(),
        "days_until_deadline": days_until,
        "deadline_status": deadline_status,
        "overdue_count": overdue_count,
        "at_risk_count": at_risk_count,
        "upcoming_deadlines": upcoming_deadlines,
        "urgency_score": round(urgency_score, 1),
        "risk_assessment": risk_assessment,
        "total_requirements": total_requirements,
        "completed_requirements": completed_requirements,
        "completion_rate": round(completion_rate * 100, 1),
    }


def get_riverside_metrics(db: Session) -> dict:
    """Calculate Riverside-specific tenant-level aggregations and metrics.

    Provides comprehensive metrics tailored for Riverside Company's
    compliance tracking needs, including cross-tenant aggregations,
    security posture scoring, and executive summary data.

    Args:
        db: Database session for querying metrics data.

    Returns:
        Dictionary containing:
            - tenant_count: Number of active Riverside tenants
            - security_posture_score: Overall security posture (0-100)
            - maturity_metrics: Aggregated maturity statistics
            - mfa_summary: MFA coverage summary
            - device_summary: Device compliance summary
            - threat_summary: Threat data summary
            - financial_exposure: Calculated risk exposure
            - executive_summary: High-level status summary

    Raises:
        ValueError: If no tenant data is available.
    """
    # Get all active tenants
    tenants = db.query(Tenant).filter(Tenant.is_active.is_(True)).all()

    if not tenants:
        raise ValueError("No tenant data available for metrics calculation")

    tenant_count = len(tenants)
    tenant_ids = [t.id for t in tenants]

    # Get latest compliance data
    compliance_subquery = (
        db.query(
            RiversideCompliance.tenant_id,
            func.max(RiversideCompliance.created_at).label("max_created"),
        )
        .filter(RiversideCompliance.tenant_id.in_(tenant_ids))
        .group_by(RiversideCompliance.tenant_id)
        .subquery()
    )

    compliance_records = (
        db.query(RiversideCompliance)
        .join(
            compliance_subquery,
            (RiversideCompliance.tenant_id == compliance_subquery.c.tenant_id)
            & (RiversideCompliance.created_at == compliance_subquery.c.max_created),
        )
        .all()
    )

    # Get latest MFA data
    mfa_subquery = (
        db.query(
            RiversideMFA.tenant_id,
            func.max(RiversideMFA.snapshot_date).label("max_snapshot"),
        )
        .filter(RiversideMFA.tenant_id.in_(tenant_ids))
        .group_by(RiversideMFA.tenant_id)
        .subquery()
    )

    mfa_records = (
        db.query(RiversideMFA)
        .join(
            mfa_subquery,
            (RiversideMFA.tenant_id == mfa_subquery.c.tenant_id)
            & (RiversideMFA.snapshot_date == mfa_subquery.c.max_snapshot),
        )
        .all()
    )

    # Get latest device compliance data
    device_subquery = (
        db.query(
            RiversideDeviceCompliance.tenant_id,
            func.max(RiversideDeviceCompliance.snapshot_date).label("max_snapshot"),
        )
        .filter(RiversideDeviceCompliance.tenant_id.in_(tenant_ids))
        .group_by(RiversideDeviceCompliance.tenant_id)
        .subquery()
    )

    device_records = (
        db.query(RiversideDeviceCompliance)
        .join(
            device_subquery,
            (RiversideDeviceCompliance.tenant_id == device_subquery.c.tenant_id)
            & (RiversideDeviceCompliance.snapshot_date == device_subquery.c.max_snapshot),
        )
        .all()
    )

    # Get threat data
    threat_subquery = (
        db.query(
            RiversideThreatData.tenant_id,
            func.max(RiversideThreatData.snapshot_date).label("max_snapshot"),
        )
        .filter(RiversideThreatData.tenant_id.in_(tenant_ids))
        .group_by(RiversideThreatData.tenant_id)
        .subquery()
    )

    threat_records = (
        db.query(RiversideThreatData)
        .join(
            threat_subquery,
            (RiversideThreatData.tenant_id == threat_subquery.c.tenant_id)
            & (RiversideThreatData.snapshot_date == threat_subquery.c.max_snapshot),
        )
        .all()
    )

    # Calculate maturity metrics
    total_maturity = 0.0
    total_gaps = 0
    for record in compliance_records:
        total_maturity += record.overall_maturity_score
        total_gaps += record.critical_gaps_count

    avg_maturity = total_maturity / len(compliance_records) if compliance_records else 0.0

    # Calculate MFA summary
    total_mfa_coverage = 0.0
    total_admin_mfa = 0.0
    total_unprotected = 0
    for record in mfa_records:
        total_mfa_coverage += record.mfa_coverage_percentage
        total_admin_mfa += record.admin_mfa_percentage
        total_unprotected += record.unprotected_users

    avg_mfa_coverage = total_mfa_coverage / len(mfa_records) if mfa_records else 0.0
    avg_admin_mfa = total_admin_mfa / len(mfa_records) if mfa_records else 0.0

    # Calculate device summary
    total_device_compliance = 0.0
    total_devices = 0
    total_compliant_devices = 0
    for record in device_records:
        total_device_compliance += record.compliance_percentage
        total_devices += record.total_devices
        total_compliant_devices += record.compliant_devices

    avg_device_compliance = (
        total_device_compliance / len(device_records) if device_records else 0.0
    )

    # Calculate threat summary
    total_vulnerabilities = 0
    total_threat_score = 0.0
    for record in threat_records:
        total_vulnerabilities += record.vulnerability_count
        if record.threat_score:
            total_threat_score += record.threat_score

    avg_threat_score = total_threat_score / len(threat_records) if threat_records else 0.0

    # Calculate security posture score (0-100)
    # Weight factors: MFA (30%), Device (25%), Maturity (25%), Threat (20%)
    posture_score = (
        (avg_mfa_coverage * 0.30)
        + (avg_device_compliance * 0.25)
        + (avg_maturity / 5 * 100 * 0.25)  # Normalize maturity to 0-100
        + (max(0, 100 - avg_threat_score) * 0.20)  # Invert threat score
    )

    # Get requirements summary
    total_requirements = (
        db.query(func.count(RiversideRequirement.id))
        .filter(RiversideRequirement.tenant_id.in_(tenant_ids))
        .scalar()
        or 0
    )

    completed_requirements = (
        db.query(func.count(RiversideRequirement.id))
        .filter(
            RiversideRequirement.tenant_id.in_(tenant_ids),
            RiversideRequirement.status == RequirementStatus.COMPLETED,
        )
        .scalar()
        or 0
    )

    completion_rate = (
        (completed_requirements / total_requirements * 100)
        if total_requirements > 0
        else 0.0
    )

    # Calculate financial exposure based on gaps and posture
    base_exposure = 20_000_000  # $20M base
    risk_multiplier = max(0.5, 1 - (posture_score / 100))  # Higher posture = lower exposure
    financial_exposure = base_exposure * risk_multiplier

    # Generate executive summary
    days_until = (RIVERSIDE_DEADLINE - date.today()).days

    if posture_score >= 80:
        overall_status = "strong"
    elif posture_score >= 60:
        overall_status = "moderate"
    elif posture_score >= 40:
        overall_status = "weak"
    else:
        overall_status = "critical"

    executive_summary = {
        "overall_status": overall_status,
        "deadline_days_remaining": days_until,
        "key_strengths": [],
        "key_concerns": [],
    }

    if avg_admin_mfa >= 95:
        executive_summary["key_strengths"].append("Strong admin MFA coverage")
    if avg_maturity >= 3.0:
        executive_summary["key_strengths"].append("Meeting maturity targets")
    if completion_rate >= 70:
        executive_summary["key_strengths"].append("Good requirements completion rate")

    if avg_mfa_coverage < 75:
        executive_summary["key_concerns"].append("Low MFA user coverage")
    if total_gaps > 10:
        executive_summary["key_concerns"].append(f"{total_gaps} critical gaps remain")
    if days_until < 180 and completion_rate < 50:
        executive_summary["key_concerns"].append("At risk of missing deadline")

    return {
        "tenant_count": tenant_count,
        "security_posture_score": round(posture_score, 1),
        "maturity_metrics": {
            "average_maturity": round(avg_maturity, 1),
            "target_maturity": TARGET_MATURITY_SCORE,
            "maturity_gap": round(TARGET_MATURITY_SCORE - avg_maturity, 1),
            "total_critical_gaps": total_gaps,
        },
        "mfa_summary": {
            "average_coverage": round(avg_mfa_coverage, 1),
            "admin_coverage": round(avg_admin_mfa, 1),
            "total_unprotected_users": total_unprotected,
            "coverage_grade": "A" if avg_mfa_coverage >= 90 else "B" if avg_mfa_coverage >= 75 else "C" if avg_mfa_coverage >= 50 else "F",
        },
        "device_summary": {
            "average_compliance": round(avg_device_compliance, 1),
            "total_devices": total_devices,
            "compliant_devices": total_compliant_devices,
            "device_compliance_rate": (
                round(total_compliant_devices / total_devices * 100, 1)
                if total_devices > 0
                else 0.0
            ),
        },
        "threat_summary": {
            "average_threat_score": round(avg_threat_score, 1),
            "total_vulnerabilities": total_vulnerabilities,
            "risk_level": "low" if avg_threat_score < 30 else "medium" if avg_threat_score < 60 else "high",
        },
        "requirements_summary": {
            "total": total_requirements,
            "completed": completed_requirements,
            "completion_rate": round(completion_rate, 1),
        },
        "financial_exposure": {
            "estimated_value": f"${financial_exposure:,.0f}",
            "currency": "USD",
            "base_exposure": f"${base_exposure:,.0f}",
        },
        "executive_summary": executive_summary,
    }
