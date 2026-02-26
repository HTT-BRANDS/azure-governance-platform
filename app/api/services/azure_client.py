"""Azure SDK client wrapper for multi-tenant access."""

import logging
from typing import Dict, Optional

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.policyinsights import PolicyInsightsClient
from azure.mgmt.security import SecurityCenter

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AzureClientManager:
    """Manages Azure SDK clients for multiple tenants.

    Supports both per-tenant credentials and Azure Lighthouse
    delegated access patterns.
    """

    def __init__(self):
        self._credentials: Dict[str, ClientSecretCredential] = {}
        self._default_credential: Optional[DefaultAzureCredential] = None

    def get_credential(self, tenant_id: str) -> ClientSecretCredential:
        """Get or create credential for a tenant."""
        if tenant_id not in self._credentials:
            # TODO: Fetch from Key Vault in production
            self._credentials[tenant_id] = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=settings.azure_client_id,
                client_secret=settings.azure_client_secret,
            )
        return self._credentials[tenant_id]

    def get_default_credential(self) -> DefaultAzureCredential:
        """Get default credential for Lighthouse scenarios."""
        if not self._default_credential:
            self._default_credential = DefaultAzureCredential()
        return self._default_credential

    def get_subscription_client(self, tenant_id: str) -> SubscriptionClient:
        """Get subscription client for a tenant."""
        credential = self.get_credential(tenant_id)
        return SubscriptionClient(credential)

    def get_resource_client(
        self, tenant_id: str, subscription_id: str
    ) -> ResourceManagementClient:
        """Get resource management client."""
        credential = self.get_credential(tenant_id)
        return ResourceManagementClient(credential, subscription_id)

    def get_cost_client(
        self, tenant_id: str, subscription_id: str
    ) -> CostManagementClient:
        """Get cost management client."""
        credential = self.get_credential(tenant_id)
        return CostManagementClient(credential, subscription_id)

    def get_policy_client(
        self, tenant_id: str, subscription_id: str
    ) -> PolicyInsightsClient:
        """Get policy insights client."""
        credential = self.get_credential(tenant_id)
        return PolicyInsightsClient(credential, subscription_id)

    def get_security_client(
        self, tenant_id: str, subscription_id: str
    ) -> SecurityCenter:
        """Get security center client."""
        credential = self.get_credential(tenant_id)
        return SecurityCenter(credential, subscription_id)

    async def list_subscriptions(self, tenant_id: str) -> list:
        """List all subscriptions in a tenant."""
        try:
            client = self.get_subscription_client(tenant_id)
            subscriptions = []
            for sub in client.subscriptions.list():
                subscriptions.append({
                    "subscription_id": sub.subscription_id,
                    "display_name": sub.display_name,
                    "state": sub.state.value if sub.state else "Unknown",
                })
            return subscriptions
        except Exception as e:
            logger.error(f"Failed to list subscriptions for tenant {tenant_id}: {e}")
            raise


# Global client manager instance
azure_client_manager = AzureClientManager()
