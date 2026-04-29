"""BudgetMappingMixin implementation for BudgetService."""

import logging

from app.models.budget import (
    Budget,
    BudgetAlert,
    BudgetSyncResult,
)
from app.schemas.budget import (
    BudgetAlertResponse,
    BudgetResponse,
    BudgetSyncResultResponse,
    BudgetThresholdResponse,
)

logger = logging.getLogger(__name__)


class BudgetMappingMixin:
    def _to_budget_response(self, budget: Budget) -> BudgetResponse:
        """Convert Budget model to BudgetResponse schema."""
        # Get thresholds (handle lazy loading)
        try:
            thresholds = [
                BudgetThresholdResponse(
                    id=t.id,
                    budget_id=t.budget_id,
                    percentage=t.percentage,
                    amount=t.amount,
                    alert_type=t.alert_type,
                    contact_emails=t.contact_emails,
                    contact_roles=t.contact_roles,
                    contact_groups=t.contact_groups,
                    is_enabled=t.is_enabled,
                    trigger_count=t.trigger_count,
                    last_triggered_at=t.last_triggered_at,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in budget.thresholds
            ]
        except Exception:
            thresholds = []

        # Get recent alerts (handle lazy loading)
        try:
            if hasattr(budget.alerts, "order_by"):
                recent_alerts = [
                    self._to_alert_response(a)
                    for a in budget.alerts.order_by(BudgetAlert.triggered_at.desc()).limit(10).all()
                ]
            else:
                # Fallback for detached instances - query directly
                from sqlalchemy.orm import joinedload

                alerts = (
                    self.db.query(BudgetAlert)
                    .options(joinedload(BudgetAlert.budget))
                    .filter(BudgetAlert.budget_id == budget.id)
                    .order_by(BudgetAlert.triggered_at.desc())
                    .limit(10)
                    .all()
                )
                recent_alerts = [self._to_alert_response(a) for a in alerts]
        except Exception:
            recent_alerts = []

        return BudgetResponse(
            id=budget.id,
            tenant_id=budget.tenant_id,
            subscription_id=budget.subscription_id,
            name=budget.name,
            amount=budget.amount,
            time_grain=budget.time_grain,
            category=budget.category,
            start_date=budget.start_date,
            end_date=budget.end_date,
            resource_group=budget.resource_group,
            currency=budget.currency,
            current_spend=budget.current_spend,
            forecasted_spend=budget.forecasted_spend,
            utilization_percentage=budget.utilization_percentage,
            status=budget.status,
            azure_budget_id=budget.azure_budget_id,
            etag=budget.etag,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
            last_synced_at=budget.last_synced_at,
            thresholds=thresholds,
            recent_alerts=recent_alerts,
            remaining_amount=budget.remaining_amount,
            is_exceeded=budget.is_exceeded,
            days_remaining=budget.days_remaining,
        )

    def _to_alert_response(self, alert: BudgetAlert) -> BudgetAlertResponse:
        """Convert BudgetAlert model to BudgetAlertResponse schema."""
        budget = alert.budget

        return BudgetAlertResponse(
            id=alert.id,
            budget_id=alert.budget_id,
            budget_name=budget.name if budget else None,
            tenant_id=budget.tenant_id if budget else None,
            subscription_id=budget.subscription_id if budget else None,
            threshold_id=alert.threshold_id,
            alert_type=alert.alert_type,
            status=alert.status,
            threshold_percentage=alert.threshold_percentage,
            threshold_amount=alert.threshold_amount,
            current_spend=alert.current_spend,
            forecasted_spend=alert.forecasted_spend,
            utilization_percentage=alert.utilization_percentage,
            triggered_at=alert.triggered_at,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            resolved_at=alert.resolved_at,
            resolution_note=alert.resolution_note,
            notification_sent=alert.notification_sent,
            notification_sent_at=alert.notification_sent_at,
        )

    def _to_sync_result_response(self, result: BudgetSyncResult) -> BudgetSyncResultResponse:
        """Convert BudgetSyncResult model to response schema."""
        return BudgetSyncResultResponse(
            id=result.id,
            tenant_id=result.tenant_id,
            sync_type=result.sync_type,
            status=result.status,
            budgets_synced=result.budgets_synced,
            budgets_created=result.budgets_created,
            budgets_updated=result.budgets_updated,
            budgets_deleted=result.budgets_deleted,
            alerts_triggered=result.alerts_triggered,
            errors_count=result.errors_count,
            error_message=result.error_message,
            error_details=result.error_details,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_seconds=result.duration_seconds,
        )
