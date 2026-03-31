"""Azure preflight check modules.

This package provides modular Azure preflight checks organized by category:

- identity: Azure AD authentication and Graph API checks
- network: Azure subscription and Graph API connectivity checks
- compute: Azure Resource Manager and resource access checks
- storage: Azure Cost Management and Policy Insights checks
- security: Azure Security Center and RBAC permission checks
- base: Common utilities and exceptions
- azure_checks: Main orchestrator and backward-compatible exports

Example usage:
    >>> from app.preflight.azure import AzureAuthCheck, NetworkChecks
    >>> auth_check = AzureAuthCheck()
    >>> result = await auth_check.run(tenant_id="...")
    
    >>> from app.preflight.azure.azure_checks import run_all_azure_checks
    >>> results = await run_all_azure_checks(tenant_id="...")
"""

# Import all check classes for convenient access
from app.preflight.azure.identity import AzureAuthCheck, check_azure_authentication
from app.preflight.azure.network import (
    AzureSubscriptionsCheck,
    AzureGraphCheck,
    check_azure_subscriptions,
    check_graph_api_access,
)
from app.preflight.azure.compute import (
    AzureResourcesCheck,
    check_resource_manager_access,
)
from app.preflight.azure.storage import (
    AzureCostManagementCheck,
    AzurePolicyCheck,
    check_cost_management_access,
    check_policy_access,
)
from app.preflight.azure.security import (
    AzureSecurityCheck,
    AzureRBACCheck,
    check_security_center_access,
    check_rbac_permissions,
)
from app.preflight.azure.base import (
    AzureCheckError,
    REQUIRED_GRAPH_PERMISSIONS,
    REQUIRED_AZURE_ROLES,
)

# For the requested interface in the task, provide NetworkChecks, ComputeChecks, etc.
# These are convenience aliases that group related checks
class NetworkChecks:
    """Network-related Azure preflight checks (subscriptions and Graph API)."""
    
    def __init__(self) -> None:
        self.subscriptions_check = AzureSubscriptionsCheck()
        self.graph_check = AzureGraphCheck()


class ComputeChecks:
    """Compute-related Azure preflight checks (Resource Manager)."""
    
    def __init__(self) -> None:
        self.resources_check = AzureResourcesCheck()


class StorageChecks:
    """Storage-related Azure preflight checks (Cost Management and Policy)."""
    
    def __init__(self) -> None:
        self.cost_management_check = AzureCostManagementCheck()
        self.policy_check = AzurePolicyCheck()


class IdentityChecks:
    """Identity-related Azure preflight checks (Azure AD Authentication)."""
    
    def __init__(self) -> None:
        self.auth_check = AzureAuthCheck()


class SecurityChecks:
    """Security-related Azure preflight checks (Security Center and RBAC)."""
    
    def __init__(self) -> None:
        self.security_check = AzureSecurityCheck()
        self.rbac_check = AzureRBACCheck()


# Re-export run_all_azure_checks from the main module
from app.preflight.azure.azure_checks import run_all_azure_checks


__all__ = [
    # Convenience classes
    "NetworkChecks",
    "ComputeChecks",
    "StorageChecks",
    "IdentityChecks",
    "SecurityChecks",
    # Individual check classes
    "AzureAuthCheck",
    "AzureSubscriptionsCheck",
    "AzureGraphCheck",
    "AzureResourcesCheck",
    "AzureCostManagementCheck",
    "AzurePolicyCheck",
    "AzureSecurityCheck",
    "AzureRBACCheck",
    # Function-based checks
    "check_azure_authentication",
    "check_azure_subscriptions",
    "check_graph_api_access",
    "check_resource_manager_access",
    "check_cost_management_access",
    "check_policy_access",
    "check_security_center_access",
    "check_rbac_permissions",
    "run_all_azure_checks",
    # Error and constants
    "AzureCheckError",
    "REQUIRED_GRAPH_PERMISSIONS",
    "REQUIRED_AZURE_ROLES",
]
