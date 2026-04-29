"""BudgetSummaryMixin implementation for BudgetService."""

import logging

from app.models.budget import (
    AlertStatus,
    Budget,
    BudgetAlert,
)
from app.models.tenant import Tenant
from app.schemas.budget import (
    BudgetSummary,
)

logger = logging.getLogger(__name__)


class BudgetSummaryMixin:
    async def get_budget_summary(self, tenant_ids: list[str] | None = None) -> BudgetSummary:
        """Get aggregated budget summary.

        Args:
            tenant_ids: Filter by tenant IDs

        Returns:
            Budget summary
        """
        query = self.db.query(Budget)
        if tenant_ids:
            query = query.filter(Budget.tenant_id.in_(tenant_ids))

        budgets = query.all()

        total_amount = sum(b.amount for b in budgets)
        total_spend = sum(b.current_spend for b in budgets)
        overall_utilization = (total_spend / total_amount * 100) if total_amount > 0 else 0

        # Count by status
        status_counts = {"active": 0, "warning": 0, "critical": 0, "exceeded": 0}
        for budget in budgets:
            status_counts[budget.status] = status_counts.get(budget.status, 0) + 1

        # Count alerts
        alert_query = self.db.query(BudgetAlert).join(Budget)
        if tenant_ids:
            alert_query = alert_query.filter(Budget.tenant_id.in_(tenant_ids))

        pending_alerts = alert_query.filter(BudgetAlert.status == AlertStatus.PENDING).count()
        acknowledged_alerts = alert_query.filter(
            BudgetAlert.status == AlertStatus.ACKNOWLEDGED
        ).count()

        # Per-tenant breakdown
        by_tenant = []
        tenant_ids_found = {b.tenant_id for b in budgets}
        tenants = self.db.query(Tenant).filter(Tenant.id.in_(tenant_ids_found)).all()
        tenant_names = {t.id: t.name for t in tenants}

        for tenant_id in tenant_ids_found:
            tenant_budgets = [b for b in budgets if b.tenant_id == tenant_id]
            tenant_amount = sum(b.amount for b in tenant_budgets)
            tenant_spend = sum(b.current_spend for b in tenant_budgets)
            tenant_utilization = (tenant_spend / tenant_amount * 100) if tenant_amount > 0 else 0

            by_tenant.append(
                {
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_names.get(tenant_id, "Unknown"),
                    "budget_count": len(tenant_budgets),
                    "total_amount": tenant_amount,
                    "total_spend": tenant_spend,
                    "utilization_percentage": tenant_utilization,
                }
            )

        return BudgetSummary(
            total_budgets=len(budgets),
            total_budget_amount=total_amount,
            total_current_spend=total_spend,
            overall_utilization=overall_utilization,
            active_count=status_counts.get("active", 0),
            warning_count=status_counts.get("warning", 0),
            critical_count=status_counts.get("critical", 0),
            exceeded_count=status_counts.get("exceeded", 0),
            pending_alerts=pending_alerts,
            acknowledged_alerts=acknowledged_alerts,
            by_tenant=by_tenant,
        )

    # =========================================================================
    # Azure Sync Operations
    # =========================================================================
