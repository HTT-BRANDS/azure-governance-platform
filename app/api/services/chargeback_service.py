"""Chargeback / Showback reporting service (CO-010).

Provides per-tenant cost allocation reports with CSV and JSON export support.
Builds on the existing CostSnapshot / Tenant data model used by CostService.
"""

import csv
import io
import logging
from datetime import UTC, date, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.cost import CostSnapshot
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Azure service-name → normalised billing category mapping
# ---------------------------------------------------------------------------

_CATEGORY_MAP: dict[str, str] = {
    # Compute
    "virtual machines": "compute",
    "app service": "compute",
    "azure kubernetes service": "compute",
    "azure functions": "compute",
    "container instances": "compute",
    "azure container apps": "compute",
    "azure batch": "compute",
    "azure spring apps": "compute",
    # Storage
    "storage": "storage",
    "azure blob storage": "storage",
    "azure files": "storage",
    "azure data lake storage": "storage",
    "azure disk storage": "storage",
    "azure backup": "storage",
    # Network
    "vpn gateway": "network",
    "azure firewall": "network",
    "load balancer": "network",
    "azure cdn": "network",
    "bandwidth": "network",
    "virtual network": "network",
    "azure dns": "network",
    "azure front door": "network",
    "azure expressroute": "network",
    # Database
    "azure sql database": "database",
    "cosmos db": "database",
    "azure database for postgresql": "database",
    "azure database for mysql": "database",
    "azure cache for redis": "database",
    "azure synapse analytics": "database",
    # Monitoring & Management
    "azure monitor": "monitoring",
    "log analytics": "monitoring",
    "application insights": "monitoring",
    "azure security center": "monitoring",
}


def _normalize_category(
    service_name: str | None,
    meter_category: str | None,
) -> str:
    """Map an Azure service / meter name to a normalised billing category.

    Tries meter_category first (more specific), then service_name.  Falls
    back to ``"other"`` for anything unrecognised.
    """
    for raw in (meter_category, service_name):
        if raw:
            key = raw.strip().lower()
            if key in _CATEGORY_MAP:
                return _CATEGORY_MAP[key]
    return "other"


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------


class TenantChargebackEntry(BaseModel):
    """Cost allocation entry for a single tenant."""

    tenant_id: str
    tenant_name: str
    total_cost: float
    percentage_of_total: float = Field(
        ..., description="Percentage of the grand total attributed to this tenant"
    )
    breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Cost broken down by category (compute, storage, network, etc.)",
    )
    cost_per_resource: float | None = Field(
        None,
        description="Average cost per tracked resource group / subscription unit",
    )
    resource_count: int = Field(
        ...,
        description=(
            "Number of distinct resource-group / subscription units observed in this period"
        ),
    )


class ChargebackReport(BaseModel):
    """Full chargeback / showback report for one billing period."""

    period_start: date
    period_end: date
    generated_at: datetime
    tenants: list[TenantChargebackEntry]
    total_cost: float
    currency: str = "USD"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ChargebackService:
    """Service for generating chargeback / showback reports.

    Aggregates :class:`~app.models.cost.CostSnapshot` data into per-tenant
    cost attribution reports and supports CSV / JSON export.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Core report builder
    # ------------------------------------------------------------------

    async def get_chargeback_report(
        self,
        tenant_ids: list[str] | None,
        start_date: date,
        end_date: date,
        include_breakdown: bool = True,
    ) -> ChargebackReport:
        """Build a chargeback report for the requested tenants and period.

        Args:
            tenant_ids: Optional list of tenant IDs to include.  When
                ``None`` all tenants are included.
            start_date: First day of the billing period (inclusive).
            end_date: Last day of the billing period (inclusive).
            include_breakdown: When ``True`` the per-category cost breakdown
                is computed and included in each entry.

        Returns:
            A :class:`ChargebackReport` with one entry per tenant that has
            cost data in the requested period.
        """
        # ----------------------------------------------------------------
        # Fetch cost snapshots
        # ----------------------------------------------------------------
        snap_query = self.db.query(CostSnapshot).filter(
            CostSnapshot.date >= start_date,
            CostSnapshot.date <= end_date,
        )
        if tenant_ids:
            snap_query = snap_query.filter(CostSnapshot.tenant_id.in_(tenant_ids))
        snapshots: list[CostSnapshot] = snap_query.all()

        # ----------------------------------------------------------------
        # Fetch tenant name lookup (all relevant tenants)
        # ----------------------------------------------------------------
        tenant_name_lookup: dict[str, str] = {}
        all_tenant_ids = list({s.tenant_id for s in snapshots})
        if all_tenant_ids:
            db_tenants = self.db.query(Tenant).filter(Tenant.id.in_(all_tenant_ids)).all()
            tenant_name_lookup = {t.id: t.name for t in db_tenants}

        # ----------------------------------------------------------------
        # Aggregate per-tenant data
        # ----------------------------------------------------------------
        tenant_costs: dict[str, float] = {}
        tenant_breakdowns: dict[str, dict[str, float]] = {}
        # Track unique (subscription_id, resource_group) pairs per tenant
        tenant_resource_keys: dict[str, set[str]] = {}

        for snap in snapshots:
            tid = snap.tenant_id

            # Accumulate total cost
            tenant_costs[tid] = tenant_costs.get(tid, 0.0) + snap.total_cost

            # Accumulate breakdown by category
            if include_breakdown:
                category = _normalize_category(snap.service_name, snap.meter_category)
                tenant_breakdowns.setdefault(tid, {})
                tenant_breakdowns[tid][category] = (
                    tenant_breakdowns[tid].get(category, 0.0) + snap.total_cost
                )

            # Track resource key for resource_count proxy
            tenant_resource_keys.setdefault(tid, set())
            resource_key = (
                f"{snap.subscription_id}::{snap.resource_group}"
                if snap.resource_group
                else snap.subscription_id
            )
            tenant_resource_keys[tid].add(resource_key)

        # ----------------------------------------------------------------
        # Build TenantChargebackEntry list
        # ----------------------------------------------------------------
        grand_total = sum(tenant_costs.values())

        entries: list[TenantChargebackEntry] = []
        for tid, cost in tenant_costs.items():
            resource_count = len(tenant_resource_keys.get(tid, set()))
            cost_per_resource = cost / resource_count if resource_count > 0 else None
            percentage = (cost / grand_total * 100.0) if grand_total > 0 else 0.0
            breakdown = tenant_breakdowns.get(tid, {}) if include_breakdown else {}

            entries.append(
                TenantChargebackEntry(
                    tenant_id=tid,
                    tenant_name=tenant_name_lookup.get(tid, "Unknown"),
                    total_cost=round(cost, 4),
                    percentage_of_total=round(percentage, 4),
                    breakdown={k: round(v, 4) for k, v in breakdown.items()},
                    cost_per_resource=(
                        round(cost_per_resource, 4) if cost_per_resource is not None else None
                    ),
                    resource_count=resource_count,
                )
            )

        # Sort descending by cost so the biggest spenders come first
        entries.sort(key=lambda e: e.total_cost, reverse=True)

        return ChargebackReport(
            period_start=start_date,
            period_end=end_date,
            generated_at=datetime.now(UTC),
            tenants=entries,
            total_cost=round(grand_total, 4),
            currency="USD",
        )

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def export_chargeback_csv(self, report: ChargebackReport) -> str:
        """Serialise a :class:`ChargebackReport` to a CSV string.

        Each row represents one tenant.  Dynamic breakdown categories are
        expanded into individual columns, sorted alphabetically after the
        fixed base columns.

        Args:
            report: The report to serialise.

        Returns:
            A UTF-8 CSV string ready to write to a file or HTTP response.
        """
        output = io.StringIO()

        # Collect all unique breakdown keys across all tenants
        all_categories: list[str] = []
        seen_categories: set[str] = set()
        for entry in report.tenants:
            for cat in entry.breakdown:
                if cat not in seen_categories:
                    all_categories.append(cat)
                    seen_categories.add(cat)
        all_categories.sort()

        base_fields: list[str] = [
            "tenant_id",
            "tenant_name",
            "total_cost",
            "percentage_of_total",
            "resource_count",
            "cost_per_resource",
        ]
        fieldnames = base_fields + all_categories

        writer = csv.DictWriter(output, fieldnames=fieldnames, restval="0.0")
        writer.writeheader()

        for entry in report.tenants:
            row: dict[str, Any] = {
                "tenant_id": entry.tenant_id,
                "tenant_name": entry.tenant_name,
                "total_cost": entry.total_cost,
                "percentage_of_total": entry.percentage_of_total,
                "resource_count": entry.resource_count,
                "cost_per_resource": (
                    entry.cost_per_resource if entry.cost_per_resource is not None else ""
                ),
            }
            for cat in all_categories:
                row[cat] = entry.breakdown.get(cat, 0.0)
            writer.writerow(row)

        return output.getvalue()

    def export_chargeback_json(self, report: ChargebackReport) -> str:
        """Serialise a :class:`ChargebackReport` to a JSON string.

        Args:
            report: The report to serialise.

        Returns:
            A pretty-printed JSON string.
        """
        return report.model_dump_json(indent=2)
