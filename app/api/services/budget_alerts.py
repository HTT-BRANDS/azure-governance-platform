"""BudgetAlertMixin implementation for BudgetService."""

import logging
from datetime import UTC, datetime

from app.api.services.budget_support import budget_module
from app.models.budget import (
    AlertStatus,
    Budget,
    BudgetAlert,
)
from app.schemas.budget import (
    BudgetAlertBulkResponse,
    BudgetAlertResponse,
)

logger = logging.getLogger(__name__)


class BudgetAlertMixin:
    async def get_budget_alerts(
        self,
        budget_id: str | None = None,
        tenant_ids: list[str] | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[BudgetAlertResponse]:
        """Get budget alerts with optional filtering.

        Args:
            budget_id: Filter by specific budget
            tenant_ids: Filter by tenant IDs
            status: Filter by alert status
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of budget alerts
        """
        query = self.db.query(BudgetAlert)

        if budget_id:
            query = query.filter(BudgetAlert.budget_id == budget_id)
        if tenant_ids:
            # Join with budget to filter by tenant
            query = query.join(Budget).filter(Budget.tenant_id.in_(tenant_ids))
        if status:
            query = query.filter(BudgetAlert.status == status)

        alerts = query.order_by(BudgetAlert.triggered_at.desc()).offset(offset).limit(limit).all()

        return [self._to_alert_response(alert) for alert in alerts]

    async def acknowledge_alert(self, alert_id: int, user_id: str, note: str | None = None) -> bool:
        """Acknowledge a budget alert.

        Args:
            alert_id: Alert ID
            user_id: User acknowledging the alert
            note: Optional resolution note

        Returns:
            True if acknowledged, False if not found
        """
        alert = self.db.query(BudgetAlert).filter(BudgetAlert.id == alert_id).first()
        if not alert:
            return False

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(UTC)
        if note:
            alert.resolution_note = note

        try:
            self.db.commit()

            # Invalidate cache
            await budget_module().invalidate_on_sync_completion(alert.budget.tenant_id)

            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to acknowledge alert: {e}")
            return False

    async def bulk_acknowledge_alerts(
        self, alert_ids: list[int], user_id: str, note: str | None = None
    ) -> BudgetAlertBulkResponse:
        """Acknowledge multiple budget alerts at once.

        Args:
            alert_ids: List of alert IDs
            user_id: User acknowledging
            note: Optional resolution note

        Returns:
            Bulk acknowledge response
        """
        acknowledged_count = 0
        failed_ids = []

        for alert_id in alert_ids:
            success = await self.acknowledge_alert(alert_id, user_id, note)
            if success:
                acknowledged_count += 1
            else:
                failed_ids.append(alert_id)

        return BudgetAlertBulkResponse(
            success=len(failed_ids) == 0,
            acknowledged_count=acknowledged_count,
            failed_ids=failed_ids,
            acknowledged_at=datetime.now(UTC),
        )

    # =========================================================================
    # Budget Summary
    # =========================================================================
