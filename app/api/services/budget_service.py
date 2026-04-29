"""Budget management service with Azure Cost Management API integration.

Provides CRUD operations for budgets, threshold management, alert handling,
and synchronization with Azure Cost Management Budget API.
"""

import logging

import httpx as httpx
from sqlalchemy.orm import Session

from app.api.services.azure_client import azure_client_manager as azure_client_manager
from app.api.services.budget_alerts import BudgetAlertMixin
from app.api.services.budget_azure import BudgetAzureMixin
from app.api.services.budget_crud import BudgetCrudMixin
from app.api.services.budget_mapping import BudgetMappingMixin
from app.api.services.budget_summary import BudgetSummaryMixin
from app.api.services.budget_sync import BudgetSyncMixin
from app.core.cache import (
    cached as cached,
)
from app.core.cache import (
    invalidate_on_sync_completion as invalidate_on_sync_completion,
)

logger = logging.getLogger(__name__)

BUDGET_API_VERSION = "2023-11-01"


class BudgetServiceError(Exception):
    """Raised when budget operations fail."""

    pass


class BudgetService(
    BudgetCrudMixin,
    BudgetAlertMixin,
    BudgetSummaryMixin,
    BudgetSyncMixin,
    BudgetAzureMixin,
    BudgetMappingMixin,
):
    """Service for budget management operations with Azure integration."""

    def __init__(self, db: Session):
        self.db = db

    @cached("budget_detail")
    async def get_budget(self, budget_id: str):
        """Get detailed budget information by ID."""
        return await super().get_budget(budget_id)

    @cached("budget_summary")
    async def get_budget_summary(self, tenant_ids: list[str] | None = None):
        """Get aggregated budget summary."""
        return await super().get_budget_summary(tenant_ids)

    # =========================================================================
    # Budget CRUD Operations
    # =========================================================================
