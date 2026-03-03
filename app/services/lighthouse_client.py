"""Azure Lighthouse Client for multi-tenant management.

This module provides a client for interacting with Azure resources
delegated via Azure Lighthouse, enabling cross-tenant operations
without per-tenant credential management.
"""

from typing import Any


class LighthouseDelegationError(Exception):
    """Raised when Lighthouse delegation fails or is invalid."""
    pass


class LighthouseAzureClient:
    """Client for Azure Lighthouse delegated access.
    
    This client uses Azure Managed Identity and Lighthouse delegation
to access customer resources without storing per-tenant credentials.
    
    Attributes:
        credential: Azure credential for authentication.
        service_provider_tenant_id: The MSP's tenant ID.
    """
    
    def __init__(self, credential: Any = None):
        """Initialize the Lighthouse Azure Client.
        
        Args:
            credential: Optional Azure credential. If not provided,
                       DefaultAzureCredential will be used.
        """
        self.credential = credential
        self.service_provider_tenant_id = None
        
        if credential is None:
            try:
                from azure.identity import DefaultAzureCredential
                self.credential = DefaultAzureCredential()
            except ImportError:
                raise LighthouseDelegationError("Azure SDK not available")
    
    async def verify_delegation(self, subscription_id: str) -> dict:
        """Verify that a subscription is accessible via Lighthouse delegation.
        
        Args:
            subscription_id: The Azure subscription ID to verify.
            
        Returns:
            dict: Verification result with keys:
                - success: bool
                - subscription_id: str
                - is_delegated: bool
                - tenant_id: str (optional)
                - state: str (optional)
                - error: str (if success is False)
                
        Raises:
            LighthouseDelegationError: If Azure API fails.
        """
        from azure.mgmt.resource import SubscriptionClient
        
        try:
            client = SubscriptionClient(self.credential)
            
            # List all accessible subscriptions (including delegated)
            subscriptions = list(client.subscriptions.list())
            
            for sub in subscriptions:
                if sub.subscription_id == subscription_id:
                    # Check if it's delegated via Lighthouse
                    is_delegated = self._is_lighthouse_delegated(sub)
                    
                    if sub.state != "Enabled":
                        return {
                            "success": False,
                            "subscription_id": subscription_id,
                            "is_delegated": is_delegated,
                            "state": sub.state,
                            "error": f"Subscription is {sub.state}"
                        }
                    
                    return {
                        "success": True,
                        "subscription_id": subscription_id,
                        "is_delegated": is_delegated,
                        "tenant_id": getattr(sub, 'tenant_id', None),
                        "state": sub.state,
                        "display_name": sub.display_name
                    }
            
            return {
                "success": False,
                "subscription_id": subscription_id,
                "is_delegated": False,
                "error": "Subscription not found or not accessible via Lighthouse"
            }
            
        except Exception as e:
            raise LighthouseDelegationError(f"Azure API Error: {str(e)}")
    
    async def get_cost_data(
        self,
        subscription_id: str,
        start_date: str,
        end_date: str,
        group_by: list[str] | None = None
    ) -> dict:
        """Get cost data for a delegated subscription.
        
        Args:
            subscription_id: The Azure subscription ID.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            group_by: Optional list of dimensions to group by.
            
        Returns:
            dict: Cost data with keys:
                - success: bool
                - cost: float
                - currency: str
                - breakdown: list (optional)
                - error: str (if success is False)
                
        Raises:
            LighthouseDelegationError: If permission denied or API fails.
        """
        from azure.mgmt.costmanagement import CostManagementClient
        
        try:
            client = CostManagementClient(self.credential)
            scope = f"/subscriptions/{subscription_id}"
            
            # Build query
            query = {
                "type": "Usage",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date,
                    "to": end_date
                },
                "dataset": {
                    "granularity": "None",
                    "aggregation": {
                        "totalCost": {
                            "name": "PreTaxCost",
                            "function": "Sum"
                        }
                    }
                }
            }
            
            # Add grouping if requested
            if group_by:
                query["dataset"]["grouping"] = [
                    {"type": "Dimension", "name": dim}
                    for dim in group_by
                ]
            
            result = client.query.usage(scope, query)
            
            # Parse result
            total_cost = 0.0
            currency = "USD"
            breakdown = []
            
            if result.rows:
                total_cost = float(result.rows[0][0])
                if len(result.rows[0]) > 1:
                    currency = result.rows[0][1]
                
                # Build breakdown if available
                for row in result.rows:
                    entry = {"cost": float(row[0])}
                    if len(row) > 1:
                        entry["currency"] = row[1]
                    breakdown.append(entry)
            
            return {
                "success": True,
                "cost": total_cost,
                "currency": currency,
                "subscription_id": subscription_id,
                "breakdown": breakdown if group_by else None
            }
            
        except Exception as e:
            if "Forbidden" in str(e) or "permission" in str(e).lower():
                raise LighthouseDelegationError(f"Permission denied: {str(e)}")
            raise LighthouseDelegationError(f"Cost data retrieval failed: {str(e)}")
    
    async def get_security_assessments(self, subscription_id: str) -> dict:
        """Get security assessments for a delegated subscription.
        
        Args:
            subscription_id: The Azure subscription ID.
            
        Returns:
            dict: Security data with keys:
                - success: bool
                - secure_score: float (optional)
                - max_score: float (optional)
                - percentage: float
                - assessments: list (optional)
                - error: str (if success is False)
                
        Raises:
            LighthouseDelegationError: If API fails.
        """
        from azure.mgmt.security import SecurityCenter
        
        try:
            client = SecurityCenter(
                self.credential,
                subscription_id,
                asc_location="centralus"
            )
            
            # Get secure scores
            scores = list(client.secure_scores.list())
            
            secure_score = None
            max_score = None
            percentage = 0.0
            
            if scores:
                secure_score = scores[0].score
                max_score = scores[0].max
                if max_score and max_score > 0:
                    percentage = (secure_score / max_score) * 100
            
            # Get assessments
            assessments = []
            try:
                assessment_list = list(client.assessments.list())
                for assessment in assessment_list:
                    assessments.append({
                        "display_name": assessment.display_name,
                        "status": assessment.status.code if assessment.status else "Unknown",
                        "impact": assessment.impact,
                        "severity": assessment.severity
                    })
            except Exception:
                # Assessments may not be available
                pass
            
            return {
                "success": True,
                "subscription_id": subscription_id,
                "secure_score": secure_score,
                "max_score": max_score,
                "percentage": percentage,
                "assessments": assessments
            }
            
        except Exception as e:
            raise LighthouseDelegationError(f"Security assessment failed: {str(e)}")
    
    async def list_resources(
        self,
        subscription_id: str,
        resource_type: str | None = None
    ) -> dict:
        """List resources in a delegated subscription.
        
        Args:
            subscription_id: The Azure subscription ID.
            resource_type: Optional filter by resource type.
            
        Returns:
            dict: Resources with keys:
                - success: bool
                - resources: list
                - count: int
                - error: str (if success is False)
        """
        from azure.mgmt.resource import ResourceManagementClient
        
        try:
            client = ResourceManagementClient(self.credential, subscription_id)
            
            resources = []
            
            # List resource groups
            resource_groups = list(client.resource_groups.list())
            
            for rg in resource_groups:
                # List resources in each resource group
                rg_resources = list(client.resources.list_by_resource_group(rg.name))
                
                for resource in rg_resources:
                    if resource_type and resource.type != resource_type:
                        continue
                    
                    resources.append({
                        "id": resource.id,
                        "name": resource.name,
                        "type": resource.type,
                        "location": resource.location,
                        "resource_group": rg.name,
                        "tags": resource.tags or {}
                    })
            
            return {
                "success": True,
                "subscription_id": subscription_id,
                "resources": resources,
                "count": len(resources)
            }
            
        except Exception as e:
            raise LighthouseDelegationError(f"Resource listing failed: {str(e)}")
    
    async def validate_tenant_access(self, tenant_id: str) -> dict:
        """Validate access to a tenant via Lighthouse delegation.
        
        Args:
            tenant_id: The Azure AD tenant ID to validate.
            
        Returns:
            dict: Validation result with keys:
                - success: bool
                - tenant_id: str
                - has_delegation: bool
                - accessible_subscriptions: int
                - error: str (if success is False)
        """
        from azure.mgmt.managedservices import ManagedServicesClient
        from azure.mgmt.resource import SubscriptionClient
        
        try:
            # Get all accessible subscriptions
            sub_client = SubscriptionClient(self.credential)
            subscriptions = list(sub_client.subscriptions.list())
            
            # Filter subscriptions for this tenant
            tenant_subs = [
                sub for sub in subscriptions
                if getattr(sub, 'tenant_id', None) == tenant_id
            ]
            
            if not tenant_subs:
                return {
                    "success": False,
                    "tenant_id": tenant_id,
                    "has_delegation": False,
                    "accessible_subscriptions": 0,
                    "error": "No accessible subscriptions found for tenant"
                }
            
            # Check for Lighthouse delegations
            ms_client = ManagedServicesClient(self.credential)
            
            has_delegation = False
            for sub in tenant_subs:
                try:
                    assignments = list(ms_client.registration_assignments.list(
                        scope=f"/subscriptions/{sub.subscription_id}"
                    ))
                    if assignments:
                        has_delegation = True
                        break
                except Exception:
                    continue
            
            return {
                "success": has_delegation,
                "tenant_id": tenant_id,
                "has_delegation": has_delegation,
                "accessible_subscriptions": len(tenant_subs),
                "error": None if has_delegation else "No active Lighthouse delegation found"
            }
            
        except Exception as e:
            return {
                "success": False,
                "tenant_id": tenant_id,
                "has_delegation": False,
                "accessible_subscriptions": 0,
                "error": str(e)
            }
    
    def _is_lighthouse_delegated(self, subscription) -> bool:
        """Check if a subscription is delegated via Lighthouse.
        
        Args:
            subscription: Azure subscription object.
            
        Returns:
            bool: True if delegated via Lighthouse.
        """
        # Check tags for Lighthouse indicators
        tags = getattr(subscription, 'tags', {}) or {}
        
        lighthouse_tags = [
            'managedBy',
            'MSP',
            'lighthouse',
            'delegation'
        ]
        
        for tag in lighthouse_tags:
            if tag in tags:
                return True
        
        return False
    
    def _validate_subscription_id(self, subscription_id: str) -> bool:
        """Validate subscription ID format.
        
        Args:
            subscription_id: The subscription ID to validate.
            
        Returns:
            bool: True if valid format.
        """
        import re
        
        # Azure subscription IDs are UUIDs
        pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        return bool(re.match(pattern, subscription_id))
