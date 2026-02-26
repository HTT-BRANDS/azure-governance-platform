"""Preflight check module for Azure Governance Platform.

This module provides comprehensive preflight checks for validating Azure
tenant connectivity, permissions, and API access before operations.

Two API styles are available:

1. **Class-based checks** (for PreflightRunner integration):
   >>> from app.preflight import AzureAuthCheck, AzureSubscriptionsCheck
   >>> check = AzureAuthCheck()
   >>> result = await check.run(tenant_id="12345678-1234-1234-1234-123456789012")

2. **Function-based checks** (for direct use):
   >>> from app.preflight import check_azure_authentication, run_all_azure_checks
   >>> results = await run_all_azure_checks("12345678-1234-1234-1234-123456789012")

Multi-tenant orchestration:
   >>> from app.preflight import check_all_tenants
   >>> all_results = await check_all_tenants()
"""

# Base and models
# Class-based Azure checks
# Function-based Azure checks
from app.preflight.azure_checks import (
    AzureAuthCheck,
    AzureCostManagementCheck,
    AzureGraphCheck,
    AzurePolicyCheck,
    AzureRBACCheck,
    AzureResourcesCheck,
    AzureSecurityCheck,
    AzureSubscriptionsCheck,
    check_azure_authentication,
    check_azure_subscriptions,
    check_cost_management_access,
    check_graph_api_access,
    check_policy_access,
    check_rbac_permissions,
    check_resource_manager_access,
    check_security_center_access,
    run_all_azure_checks,
)
from app.preflight.base import BasePreflightCheck
from app.preflight.models import (
    CheckCategory,
    CheckResult,
    CheckStatus,
    PreflightReport,
)

# Tenant orchestration
from app.preflight.tenant_checks import (
    check_all_tenants,
    check_single_tenant,
    check_tenant_connectivity,
    check_tenants_quick,
    format_check_results,
)

__all__ = [
    # Base classes
    "BasePreflightCheck",
    # Models
    "CheckCategory",
    "CheckResult",
    "CheckStatus",
    "PreflightReport",
    # Class-based checks
    "AzureAuthCheck",
    "AzureSubscriptionsCheck",
    "AzureCostManagementCheck",
    "AzureGraphCheck",
    "AzurePolicyCheck",
    "AzureResourcesCheck",
    "AzureSecurityCheck",
    "AzureRBACCheck",
    # Function-based checks
    "check_azure_authentication",
    "check_azure_subscriptions",
    "check_cost_management_access",
    "check_graph_api_access",
    "check_policy_access",
    "check_resource_manager_access",
    "check_rbac_permissions",
    "check_security_center_access",
    "run_all_azure_checks",
    # Tenant orchestration
    "check_all_tenants",
    "check_single_tenant",
    "check_tenant_connectivity",
    "check_tenants_quick",
    "format_check_results",
]
