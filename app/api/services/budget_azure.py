"""BudgetAzureMixin implementation for BudgetService."""

import json
import logging

from app.api.services.budget_support import budget_module
from app.models.budget import (
    Budget,
    BudgetThreshold,
)

logger = logging.getLogger(__name__)


class BudgetAzureMixin:
    async def _create_budget_in_azure(self, budget: Budget) -> None:
        """Create budget in Azure Cost Management.

        Args:
            budget: Local budget to create in Azure
        """
        # Get thresholds
        thresholds = (
            self.db.query(BudgetThreshold).filter(BudgetThreshold.budget_id == budget.id).all()
        )

        # Build notifications
        notifications = {}
        for i, threshold in enumerate(thresholds):
            notif_name = f"Notification{i + 1}"
            notifications[notif_name] = {
                "enabled": threshold.is_enabled,
                "operator": "GreaterThan",
                "threshold": threshold.percentage,
                "contactEmails": json.loads(threshold.contact_emails or "[]"),
                "contactRoles": json.loads(threshold.contact_roles or "[]"),
                "contactGroups": json.loads(threshold.contact_groups or "[]"),
            }

        body = {
            "properties": {
                "category": budget.category,
                "amount": budget.amount,
                "timeGrain": budget.time_grain,
                "timePeriod": {
                    "startDate": budget.start_date.isoformat(),
                    "endDate": budget.end_date.isoformat() if budget.end_date else None,
                },
                "notifications": notifications,
            }
        }

        # Remove None values
        if not body["properties"]["timePeriod"]["endDate"]:
            del body["properties"]["timePeriod"]["endDate"]

        credential = budget_module().azure_client_manager.get_credential(budget.tenant_id)
        token = credential.get_token("https://management.azure.com/.default")

        url = (
            f"https://management.azure.com/subscriptions/{budget.subscription_id}"
            f"/providers/Microsoft.Consumption/budgets/{budget.name}"
            f"?api-version={budget_module().BUDGET_API_VERSION}"
        )

        async with budget_module().httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(
                url,
                json=body,
                headers={"Authorization": f"Bearer {token.token}"},
            )
            resp.raise_for_status()

            # Update local budget with Azure ID
            data = resp.json()
            budget.azure_budget_id = data.get("id")
            budget.etag = data.get("etag")
            self.db.commit()

    async def _update_budget_in_azure(self, budget: Budget) -> None:
        """Update budget in Azure Cost Management."""
        if not budget.azure_budget_id:
            # Create instead
            await self._create_budget_in_azure(budget)
            return

        # Similar to create but with PATCH semantics
        body = {
            "properties": {
                "amount": budget.amount,
                "timePeriod": {
                    "startDate": budget.start_date.isoformat(),
                    "endDate": budget.end_date.isoformat() if budget.end_date else None,
                },
            }
        }

        if not body["properties"]["timePeriod"].get("endDate"):
            del body["properties"]["timePeriod"]["endDate"]

        credential = budget_module().azure_client_manager.get_credential(budget.tenant_id)
        token = credential.get_token("https://management.azure.com/.default")

        url = f"https://management.azure.com{budget.azure_budget_id}?api-version={budget_module().BUDGET_API_VERSION}"

        async with budget_module().httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(
                url,
                json=body,
                headers={
                    "Authorization": f"Bearer {token.token}",
                    "If-Match": budget.etag or "*",
                },
            )
            resp.raise_for_status()

            # Update ETag
            data = resp.json()
            budget.etag = data.get("etag")
            self.db.commit()

    async def _delete_budget_from_azure(self, budget: Budget) -> None:
        """Delete budget from Azure Cost Management."""
        if not budget.azure_budget_id:
            return

        credential = budget_module().azure_client_manager.get_credential(budget.tenant_id)
        token = credential.get_token("https://management.azure.com/.default")

        url = f"https://management.azure.com{budget.azure_budget_id}?api-version={budget_module().BUDGET_API_VERSION}"

        async with budget_module().httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(
                url,
                headers={"Authorization": f"Bearer {token.token}"},
            )
            resp.raise_for_status()

    # =========================================================================
    # Conversion Helpers
    # =========================================================================
