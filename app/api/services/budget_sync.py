"""BudgetSyncMixin implementation for BudgetService."""

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.api.services.budget_support import budget_module
from app.core.circuit_breaker import BUDGET_SYNC_BREAKER, circuit_breaker
from app.core.retry import BUDGET_SYNC_POLICY, retry_with_backoff
from app.models.budget import (
    AlertStatus,
    AlertType,
    Budget,
    BudgetAlert,
    BudgetSyncResult,
    BudgetThreshold,
)
from app.schemas.budget import (
    BudgetSyncResultResponse,
)

logger = logging.getLogger(__name__)


class BudgetSyncMixin:
    @circuit_breaker(BUDGET_SYNC_BREAKER)
    @retry_with_backoff(BUDGET_SYNC_POLICY)
    async def sync_budgets_from_azure(
        self, tenant_id: str, subscription_ids: list[str] | None = None
    ) -> BudgetSyncResultResponse:
        """Sync budgets from Azure Cost Management API.

        Args:
            tenant_id: Tenant ID to sync
            subscription_ids: Specific subscriptions (None for all)

        Returns:
            Sync result
        """
        sync_result = BudgetSyncResult(
            tenant_id=tenant_id,
            sync_type="incremental",
            status="running",
            started_at=datetime.now(UTC),
        )
        self.db.add(sync_result)
        self.db.commit()

        try:
            # Get subscriptions to sync
            if subscription_ids:
                subscriptions = [{"subscription_id": sub_id} for sub_id in subscription_ids]
            else:
                subscriptions = await budget_module().azure_client_manager.list_subscriptions(
                    tenant_id
                )

            total_synced = 0
            total_created = 0
            total_updated = 0
            total_errors = 0

            for sub in subscriptions:
                sub_id = sub["subscription_id"]

                try:
                    azure_budgets = await self._fetch_budgets_from_azure(tenant_id, sub_id)

                    for azure_budget in azure_budgets:
                        try:
                            result = await self._sync_single_budget(tenant_id, sub_id, azure_budget)
                            if result == "created":
                                total_created += 1
                            elif result == "updated":
                                total_updated += 1
                            total_synced += 1
                        except Exception as e:
                            logger.error(f"Failed to sync budget: {e}")
                            total_errors += 1

                except Exception as e:
                    logger.error(f"Failed to fetch budgets for subscription {sub_id}: {e}")
                    total_errors += 1

            # Update sync result
            sync_result.status = "completed" if total_errors == 0 else "partial"
            sync_result.budgets_synced = total_synced
            sync_result.budgets_created = total_created
            sync_result.budgets_updated = total_updated
            sync_result.errors_count = total_errors
            sync_result.complete(sync_result.status)

            self.db.commit()

            # Check for threshold breaches
            await self._check_budget_thresholds(tenant_id)

            # Invalidate cache
            await budget_module().invalidate_on_sync_completion(tenant_id)

            return self._to_sync_result_response(sync_result)

        except Exception as e:
            sync_result.status = "failed"
            sync_result.error_message = str(e)[:5000]
            sync_result.complete("failed")
            self.db.commit()
            logger.error(f"Budget sync failed for tenant {tenant_id}: {e}")
            raise budget_module().BudgetServiceError(f"Sync failed: {e}") from e

    async def _fetch_budgets_from_azure(
        self, tenant_id: str, subscription_id: str
    ) -> list[dict[str, Any]]:
        """Fetch budgets from Azure Cost Management API.

        Args:
            tenant_id: Azure tenant ID
            subscription_id: Azure subscription ID

        Returns:
            List of budget dictionaries from Azure
        """
        credential = budget_module().azure_client_manager.get_credential(tenant_id)
        token = credential.get_token("https://management.azure.com/.default")

        url = (
            f"https://management.azure.com/subscriptions/{subscription_id}"
            f"/providers/Microsoft.Consumption/budgets"
            f"?api-version={budget_module().BUDGET_API_VERSION}"
        )

        async with budget_module().httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token.token}"},
            )
            resp.raise_for_status()

        data = resp.json()
        return data.get("value", [])

    async def _sync_single_budget(
        self, tenant_id: str, subscription_id: str, azure_budget: dict[str, Any]
    ) -> str:
        """Sync a single budget from Azure.

        Args:
            tenant_id: Tenant ID
            subscription_id: Subscription ID
            azure_budget: Budget data from Azure API

        Returns:
            "created", "updated", or "unchanged"
        """
        properties = azure_budget.get("properties", {})
        azure_id = azure_budget.get("id", "")
        name = azure_budget.get("name", "")
        etag = azure_budget.get("etag", "")

        # Check if budget exists locally
        existing = self.db.query(Budget).filter(Budget.azure_budget_id == azure_id).first()

        # Extract budget details
        amount = properties.get("amount", 0)
        time_grain = properties.get("timeGrain", "Monthly")
        category = properties.get("category", "Cost")

        time_period = properties.get("timePeriod", {})
        start_date = datetime.strptime(
            time_period.get("startDate", "2024-01-01"), "%Y-%m-%d"
        ).date()
        end_date_str = time_period.get("endDate")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        # Current spend
        current_spend = properties.get("currentSpend", {}).get("amount", 0)
        forecasted_spend = properties.get("forecast", {}).get("amount")
        currency = properties.get("currentSpend", {}).get("unit", "USD")

        # Calculate utilization
        utilization = (float(current_spend) / float(amount) * 100) if amount > 0 else 0

        if existing:
            # Update existing
            existing.name = name
            existing.amount = float(amount)
            existing.time_grain = time_grain
            existing.category = category
            existing.start_date = start_date
            existing.end_date = end_date
            existing.current_spend = float(current_spend)
            existing.forecasted_spend = float(forecasted_spend) if forecasted_spend else None
            existing.currency = currency
            existing.utilization_percentage = utilization
            existing.etag = etag
            existing.last_synced_at = datetime.now(UTC)
            existing.update_status()

            result = "updated"
        else:
            # Create new
            budget = Budget(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                name=name,
                amount=float(amount),
                time_grain=time_grain,
                category=category,
                start_date=start_date,
                end_date=end_date,
                current_spend=float(current_spend),
                forecasted_spend=float(forecasted_spend) if forecasted_spend else None,
                currency=currency,
                utilization_percentage=utilization,
                azure_budget_id=azure_id,
                etag=etag,
                last_synced_at=datetime.now(UTC),
            )
            budget.update_status()
            self.db.add(budget)

            # Sync notification thresholds
            notifications = properties.get("notifications", {})
            for _notif_name, notif_config in notifications.items():
                threshold = BudgetThreshold(
                    budget_id=budget.id,
                    percentage=float(notif_config.get("threshold", 100)),
                    alert_type=notif_config.get("operator", "GreaterThan"),
                    contact_emails=json.dumps(notif_config.get("contactEmails", [])),
                    contact_roles=json.dumps(notif_config.get("contactRoles", [])),
                    contact_groups=json.dumps(notif_config.get("contactGroups", [])),
                    is_enabled=notif_config.get("enabled", True),
                )
                self.db.add(threshold)

            result = "created"

        self.db.commit()
        return result

    async def _check_budget_thresholds(self, tenant_id: str) -> int:
        """Check all budget thresholds and create alerts for breaches.

        Args:
            tenant_id: Tenant to check

        Returns:
            Number of alerts triggered
        """
        budgets = self.db.query(Budget).filter(Budget.tenant_id == tenant_id).all()
        alerts_triggered = 0

        for budget in budgets:
            for threshold in budget.thresholds:
                if not threshold.is_enabled:
                    continue

                threshold_amount = threshold.calculate_amount(budget.amount)

                # Check if threshold is breached
                if budget.current_spend >= threshold_amount:
                    # Check if alert already exists for this threshold
                    existing_alert = (
                        self.db.query(BudgetAlert)
                        .filter(
                            BudgetAlert.budget_id == budget.id,
                            BudgetAlert.threshold_id == threshold.id,
                            BudgetAlert.status.in_([AlertStatus.PENDING, AlertStatus.ACKNOWLEDGED]),
                        )
                        .first()
                    )

                    if not existing_alert:
                        # Create new alert
                        alert = BudgetAlert(
                            budget_id=budget.id,
                            threshold_id=threshold.id,
                            alert_type=self._map_alert_type(threshold.alert_type),
                            threshold_percentage=threshold.percentage,
                            threshold_amount=threshold_amount,
                            current_spend=budget.current_spend,
                            forecasted_spend=budget.forecasted_spend,
                            utilization_percentage=budget.utilization_percentage,
                        )
                        self.db.add(alert)
                        alerts_triggered += 1

                        # Update threshold trigger count
                        threshold.trigger_count += 1
                        threshold.last_triggered_at = datetime.now(UTC)

        self.db.commit()
        return alerts_triggered

    def _map_alert_type(self, azure_operator: str) -> str:
        """Map Azure alert operator to our alert type."""
        operator_map = {
            "GreaterThan": AlertType.WARNING,
            "GreaterThanOrEqualTo": AlertType.WARNING,
            "LessThan": AlertType.FORECASTED,
        }
        return operator_map.get(azure_operator, AlertType.WARNING)

    # =========================================================================
    # Azure CRUD Operations (Best Effort)
    # =========================================================================
