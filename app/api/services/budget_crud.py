"""BudgetCrudMixin implementation for BudgetService."""

import json
import logging
import uuid
from datetime import UTC, datetime

from app.api.services.budget_support import budget_module
from app.models.budget import (
    AlertStatus,
    Budget,
    BudgetAlert,
    BudgetNotification,
    BudgetStatus,
    BudgetThreshold,
)
from app.schemas.budget import (
    BudgetCreate,
    BudgetListItem,
    BudgetResponse,
    BudgetUpdate,
)

logger = logging.getLogger(__name__)


class BudgetCrudMixin:
    async def get_budgets(
        self,
        tenant_ids: list[str] | None = None,
        subscription_ids: list[str] | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BudgetListItem]:
        """Get list of budgets with optional filtering.

        Args:
            tenant_ids: Filter by tenant IDs
            subscription_ids: Filter by subscription IDs
            status: Filter by budget status
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of budget list items
        """
        query = self.db.query(Budget)

        if tenant_ids:
            query = query.filter(Budget.tenant_id.in_(tenant_ids))
        if subscription_ids:
            query = query.filter(Budget.subscription_id.in_(subscription_ids))
        if status:
            query = query.filter(Budget.status == status)

        query.count()
        budgets = query.order_by(Budget.created_at.desc()).offset(offset).limit(limit).all()

        # Build response with alert counts
        result = []
        for budget in budgets:
            pending_alerts = (
                budget.alerts.filter(BudgetAlert.status == AlertStatus.PENDING).count()
                if hasattr(budget.alerts, "filter")
                else sum(1 for a in budget.alerts if a.status == AlertStatus.PENDING)
            )

            result.append(
                BudgetListItem(
                    id=budget.id,
                    name=budget.name,
                    amount=budget.amount,
                    current_spend=budget.current_spend,
                    utilization_percentage=budget.utilization_percentage,
                    status=budget.status,
                    time_grain=budget.time_grain,
                    currency=budget.currency,
                    start_date=budget.start_date,
                    end_date=budget.end_date,
                    subscription_id=budget.subscription_id,
                    resource_group=budget.resource_group,
                    alert_count=pending_alerts,
                    last_synced_at=budget.last_synced_at,
                )
            )

        return result

    async def get_budget(self, budget_id: str) -> BudgetResponse | None:
        """Get detailed budget information by ID.

        Args:
            budget_id: Budget UUID

        Returns:
            Budget response or None if not found
        """
        budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            return None

        return self._to_budget_response(budget)

    async def create_budget(self, data: BudgetCreate) -> BudgetResponse:
        """Create a new budget locally and in Azure.

        Args:
            data: Budget creation data

        Returns:
            Created budget response

        Raises:
            BudgetServiceError: If creation fails
        """
        # Generate UUID for new budget
        budget_id = str(uuid.uuid4())

        # Create local budget record
        budget = Budget(
            id=budget_id,
            tenant_id=data.tenant_id,
            subscription_id=data.subscription_id,
            resource_group=data.resource_group,
            name=data.name,
            amount=data.amount,
            time_grain=data.time_grain,
            category=data.category,
            start_date=data.start_date,
            end_date=data.end_date,
            currency=data.currency,
            current_spend=0.0,
            status=BudgetStatus.ACTIVE,
            utilization_percentage=0.0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        self.db.add(budget)

        # Create thresholds if provided
        for threshold_config in data.thresholds:
            threshold = BudgetThreshold(
                budget_id=budget_id,
                percentage=threshold_config.percentage,
                alert_type=threshold_config.alert_type,
                contact_emails=json.dumps(threshold_config.contact_emails)
                if threshold_config.contact_emails
                else None,
                contact_roles=json.dumps(threshold_config.contact_roles)
                if threshold_config.contact_roles
                else None,
                contact_groups=json.dumps(threshold_config.contact_groups)
                if threshold_config.contact_groups
                else None,
                is_enabled=threshold_config.is_enabled,
                amount=budget.amount * (threshold_config.percentage / 100.0),
            )
            self.db.add(threshold)

        # Create notifications if provided
        for notification_config in data.notifications:
            notification = BudgetNotification(
                budget_id=budget_id,
                notification_type=notification_config.notification_type,
                config=json.dumps(notification_config.config)
                if notification_config.config
                else None,
                is_enabled=notification_config.is_enabled,
            )
            self.db.add(notification)

        try:
            self.db.commit()
            self.db.refresh(budget)

            # Try to create in Azure (best effort - don't fail if Azure creation fails)
            try:
                await self._create_budget_in_azure(budget)
            except Exception as e:
                logger.warning(
                    f"Failed to create budget in Azure: {e}. Budget created locally only."
                )

            return self._to_budget_response(budget)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create budget: {e}")
            raise budget_module().BudgetServiceError(f"Failed to create budget: {e}") from e

    async def update_budget(self, budget_id: str, data: BudgetUpdate) -> BudgetResponse | None:
        """Update an existing budget.

        Args:
            budget_id: Budget UUID
            data: Update data

        Returns:
            Updated budget response or None if not found
        """
        budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            return None

        # Update fields
        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            if hasattr(budget, field):
                setattr(budget, field, value)

        budget.updated_at = datetime.now(UTC)

        # Recalculate utilization if amount changed
        if "amount" in update_fields and budget.amount > 0:
            budget.utilization_percentage = (budget.current_spend / budget.amount) * 100
            budget.update_status()

        try:
            self.db.commit()
            self.db.refresh(budget)

            # Try to update in Azure
            try:
                await self._update_budget_in_azure(budget)
            except Exception as e:
                logger.warning(f"Failed to update budget in Azure: {e}")

            # Invalidate cache
            await budget_module().invalidate_on_sync_completion(budget.tenant_id)

            return self._to_budget_response(budget)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update budget: {e}")
            raise budget_module().BudgetServiceError(f"Failed to update budget: {e}") from e

    async def delete_budget(self, budget_id: str) -> bool:
        """Delete a budget.

        Args:
            budget_id: Budget UUID

        Returns:
            True if deleted, False if not found
        """
        budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            return False

        tenant_id = budget.tenant_id

        try:
            # Try to delete from Azure first
            try:
                await self._delete_budget_from_azure(budget)
            except Exception as e:
                logger.warning(f"Failed to delete budget from Azure: {e}")

            self.db.delete(budget)
            self.db.commit()

            # Invalidate cache
            await budget_module().invalidate_on_sync_completion(tenant_id)

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete budget: {e}")
            raise budget_module().BudgetServiceError(f"Failed to delete budget: {e}") from e

    # =========================================================================
    # Budget Alerts
    # =========================================================================
