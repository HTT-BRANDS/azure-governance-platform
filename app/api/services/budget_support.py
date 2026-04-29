"""Shared helpers for BudgetService mixins."""

import sys
from types import ModuleType


def budget_module() -> ModuleType:
    """Return the public budget_service module for patch-compatible lookups."""
    return sys.modules["app.api.services.budget_service"]
