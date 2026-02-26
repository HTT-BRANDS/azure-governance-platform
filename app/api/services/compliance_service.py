"""Compliance management service."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.compliance import ComplianceSnapshot, PolicyState
from app.models.tenant import Tenant
from app.schemas.compliance import (
    ComplianceScore,
    ComplianceSummary,
    PolicyStatus,
    PolicyViolation,
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for compliance monitoring operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_compliance_summary(self) -> ComplianceSummary:
        """Get aggregated compliance summary across all tenants."""
        # Get latest snapshots per tenant
        tenants = self.db.query(Tenant).filter(Tenant.is_active == True).all()

        scores = []
        total_compliant = 0
        total_non_compliant = 0
        total_exempt = 0

        for tenant in tenants:
            # Get most recent snapshot for this tenant
            latest = (
                self.db.query(ComplianceSnapshot)
                .filter(ComplianceSnapshot.tenant_id == tenant.id)
                .order_by(ComplianceSnapshot.snapshot_date.desc())
                .first()
            )

            if latest:
                scores.append(
                    ComplianceScore(
                        tenant_id=tenant.id,
                        tenant_name=tenant.name,
                        subscription_id=latest.subscription_id,
                        overall_compliance_percent=latest.overall_compliance_percent,
                        secure_score=latest.secure_score,
                        compliant_resources=latest.compliant_resources,
                        non_compliant_resources=latest.non_compliant_resources,
                        exempt_resources=latest.exempt_resources,
                        last_updated=latest.synced_at,
                    )
                )
                total_compliant += latest.compliant_resources
                total_non_compliant += latest.non_compliant_resources
                total_exempt += latest.exempt_resources

        # Calculate average compliance
        avg_compliance = 0.0
        if scores:
            avg_compliance = sum(s.overall_compliance_percent for s in scores) / len(scores)

        # Get top violations
        top_violations = self._get_top_violations()

        return ComplianceSummary(
            average_compliance_percent=avg_compliance,
            total_compliant_resources=total_compliant,
            total_non_compliant_resources=total_non_compliant,
            total_exempt_resources=total_exempt,
            scores_by_tenant=scores,
            top_violations=top_violations,
        )

    def _get_top_violations(self, limit: int = 10) -> List[PolicyViolation]:
        """Get top policy violations by count."""
        # Aggregate non-compliant policies
        policies = (
            self.db.query(PolicyState)
            .filter(PolicyState.compliance_state == "NonCompliant")
            .all()
        )

        # Group by policy name
        violation_map = {}
        for policy in policies:
            if policy.policy_name not in violation_map:
                violation_map[policy.policy_name] = {
                    "policy_name": policy.policy_name,
                    "policy_category": policy.policy_category,
                    "violation_count": 0,
                    "tenants": set(),
                }
            violation_map[policy.policy_name]["violation_count"] += policy.non_compliant_count
            violation_map[policy.policy_name]["tenants"].add(policy.tenant_id)

        # Convert to list and sort
        violations = [
            PolicyViolation(
                policy_name=v["policy_name"],
                policy_category=v["policy_category"],
                violation_count=v["violation_count"],
                affected_tenants=len(v["tenants"]),
                severity="Medium",  # TODO: Map from policy metadata
            )
            for v in violation_map.values()
        ]

        return sorted(violations, key=lambda x: x.violation_count, reverse=True)[:limit]

    def get_scores_by_tenant(self, tenant_id: Optional[str] = None) -> List[ComplianceScore]:
        """Get compliance scores, optionally filtered by tenant."""
        query = self.db.query(Tenant).filter(Tenant.is_active == True)

        if tenant_id:
            query = query.filter(Tenant.id == tenant_id)

        tenants = query.all()
        scores = []

        for tenant in tenants:
            latest = (
                self.db.query(ComplianceSnapshot)
                .filter(ComplianceSnapshot.tenant_id == tenant.id)
                .order_by(ComplianceSnapshot.snapshot_date.desc())
                .first()
            )

            if latest:
                scores.append(
                    ComplianceScore(
                        tenant_id=tenant.id,
                        tenant_name=tenant.name,
                        subscription_id=latest.subscription_id,
                        overall_compliance_percent=latest.overall_compliance_percent,
                        secure_score=latest.secure_score,
                        compliant_resources=latest.compliant_resources,
                        non_compliant_resources=latest.non_compliant_resources,
                        exempt_resources=latest.exempt_resources,
                        last_updated=latest.synced_at,
                    )
                )

        return scores

    def get_non_compliant_policies(
        self, tenant_id: Optional[str] = None
    ) -> List[PolicyStatus]:
        """Get non-compliant policy details."""
        query = self.db.query(PolicyState).filter(
            PolicyState.compliance_state == "NonCompliant"
        )

        if tenant_id:
            query = query.filter(PolicyState.tenant_id == tenant_id)

        policies = query.order_by(PolicyState.non_compliant_count.desc()).limit(100).all()

        return [
            PolicyStatus(
                policy_definition_id=p.policy_definition_id,
                policy_name=p.policy_name,
                policy_category=p.policy_category,
                compliance_state=p.compliance_state,
                non_compliant_count=p.non_compliant_count,
                tenant_id=p.tenant_id,
                subscription_id=p.subscription_id,
                recommendation=p.recommendation,
            )
            for p in policies
        ]
