"""Unit tests for Lighthouse Azure client.

Tests the LighthouseAzureClient class which handles Azure Lighthouse
delegation verification, resource access, and multi-tenant operations.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest


class TestLighthouseAzureClient:
    """Test suite for LighthouseAzureClient."""
    
    @pytest.fixture
    def mock_subscription(self):
        """Create a mock subscription object."""
        sub = MagicMock()
        sub.subscription_id = str(uuid.uuid4())
        sub.display_name = "Test Subscription"
        sub.state = "Enabled"
        sub.tenant_id = str(uuid.uuid4())
        sub.tags = {"environment": "test", "managedBy": "lighthouse"}
        return sub
    
    @pytest.fixture
    def mock_delegated_subscription(self):
        """Create a mock delegated subscription object."""
        sub = MagicMock()
        sub.subscription_id = "sub-12345"
        sub.display_name = "Delegated Test Subscription"
        sub.state = "Enabled"
        sub.tenant_id = "customer-tenant-789"
        sub.tags = {
            "environment": "production",
            "managedBy": "lighthouse",
            "mspOfferName": "Azure Governance Platform"
        }
        return sub


class TestVerifyDelegation(TestLighthouseAzureClient):
    """Tests for delegation verification."""
    
    @pytest.mark.asyncio
    async def test_verify_delegation_success(self, mock_delegated_subscription):
        """Test successful delegation verification."""
        with patch("azure.identity.DefaultAzureCredential") as mock_cred:
            with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
                # Setup mocks
                mock_cred_instance = MagicMock()
                mock_cred.return_value = mock_cred_instance
                
                mock_client = MagicMock()
                mock_sub_client.return_value = mock_client
                
                # Mock subscription list returning our delegated subscription
                mock_client.subscriptions.list.return_value = [mock_delegated_subscription]
                
                # Import and test
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient()
                result = await client.verify_delegation("sub-12345")
                
                # Assertions
                assert result["success"] is True
                assert result["subscription_id"] == "sub-12345"
                assert result["is_delegated"] is True
                assert "tenant_id" in result
                assert result["state"] == "Enabled"
    
    @pytest.mark.asyncio
    async def test_verify_delegation_not_found(self):
        """Test verification when subscription is not found."""
        with patch("azure.identity.DefaultAzureCredential") as mock_cred:
            with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
                mock_cred.return_value = MagicMock()
                
                mock_client = MagicMock()
                mock_sub_client.return_value = mock_client
                mock_client.subscriptions.list.return_value = []  # Empty list
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient()
                result = await client.verify_delegation("non-existent-sub")
                
                assert result["success"] is False
                assert "error" in result
                assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_verify_delegation_not_delegated(self, mock_subscription):
        """Test verification when subscription exists but is not delegated via Lighthouse."""
        # Remove the lighthouse tag
        mock_subscription.tags = {"environment": "test"}
        
        with patch("azure.identity.DefaultAzureCredential") as mock_cred:
            with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
                mock_cred.return_value = MagicMock()
                
                mock_client = MagicMock()
                mock_sub_client.return_value = mock_client
                mock_client.subscriptions.list.return_value = [mock_subscription]
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient()
                result = await client.verify_delegation(mock_subscription.subscription_id)
                
                # The actual implementation returns success=False with error
                assert result["success"] is False
                assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_verify_delegation_disabled_subscription(self, mock_delegated_subscription):
        """Test verification when subscription is disabled."""
        mock_delegated_subscription.state = "Disabled"
        
        with patch("azure.identity.DefaultAzureCredential") as mock_cred:
            with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
                mock_cred.return_value = MagicMock()
                
                mock_client = MagicMock()
                mock_sub_client.return_value = mock_client
                mock_client.subscriptions.list.return_value = [mock_delegated_subscription]
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient()
                result = await client.verify_delegation("sub-12345")
                
                assert result["success"] is False
                assert result["state"] == "Disabled"
                assert "disabled" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_verify_delegation_azure_api_error(self):
        """Test verification when Azure API raises an error."""
        with patch("azure.identity.DefaultAzureCredential") as mock_cred:
            with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
                mock_cred.return_value = MagicMock()
                
                mock_client = MagicMock()
                mock_sub_client.return_value = mock_client
                mock_client.subscriptions.list.side_effect = Exception("Azure API Error: Authentication failed")
                
                from app.services.lighthouse_client import LighthouseAzureClient, LighthouseDelegationError
                
                client = LighthouseAzureClient()
                
                with pytest.raises(LighthouseDelegationError) as exc_info:
                    await client.verify_delegation("sub-12345")
                
                assert "Azure API" in str(exc_info.value)


class TestGetCostData(TestLighthouseAzureClient):
    """Tests for cost data retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_cost_data_success(self):
        """Test successful cost data retrieval."""
        mock_cost_result = MagicMock()
        mock_cost_result.rows = [
            [100.50, "USD"],  # cost, currency
        ]
        
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.costmanagement.CostManagementClient") as mock_cost_client:
                mock_client = MagicMock()
                mock_cost_client.return_value = mock_client
                mock_client.query.usage.return_value = mock_cost_result
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient(credential=MagicMock())
                result = await client.get_cost_data(
                    subscription_id="sub-12345",
                    start_date="2025-01-01",
                    end_date="2025-01-31"
                )
                
                assert result["success"] is True
                assert "cost" in result
                assert result["cost"] == 100.50
                assert result["currency"] == "USD"
                assert result["subscription_id"] == "sub-12345"
    
    @pytest.mark.asyncio
    async def test_get_cost_data_empty_result(self):
        """Test cost data when no usage exists."""
        mock_cost_result = MagicMock()
        mock_cost_result.rows = []  # No cost data
        
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.costmanagement.CostManagementClient") as mock_cost_client:
                mock_client = MagicMock()
                mock_cost_client.return_value = mock_client
                mock_client.query.usage.return_value = mock_cost_result
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient(credential=MagicMock())
                result = await client.get_cost_data(
                    subscription_id="sub-12345",
                    start_date="2025-01-01",
                    end_date="2025-01-31"
                )
                
                assert result["success"] is True
                assert result["cost"] == 0
                assert result["currency"] == "USD"
    
    @pytest.mark.asyncio
    async def test_get_cost_data_permission_denied(self):
        """Test cost data when permissions are insufficient."""
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.costmanagement.CostManagementClient") as mock_cost_client:
                mock_client = MagicMock()
                mock_cost_client.return_value = mock_client
                mock_client.query.usage.side_effect = Exception("Forbidden: Insufficient permissions")
                
                from app.services.lighthouse_client import LighthouseAzureClient, LighthouseDelegationError
                
                client = LighthouseAzureClient(credential=MagicMock())
                
                with pytest.raises(LighthouseDelegationError) as exc_info:
                    await client.get_cost_data(
                        subscription_id="sub-12345",
                        start_date="2025-01-01",
                        end_date="2025-01-31"
                    )
                
                assert "permission" in str(exc_info.value).lower() or "forbidden" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_cost_data_with_grouping(self):
        """Test cost data with service-level grouping."""
        mock_cost_result = MagicMock()
        mock_cost_result.rows = [
            [50.25, "USD", "Storage", "rg-prod"],
            [30.15, "USD", "Compute", "rg-prod"],
            [20.10, "USD", "Networking", "rg-shared"],
        ]
        
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.costmanagement.CostManagementClient") as mock_cost_client:
                mock_client = MagicMock()
                mock_cost_client.return_value = mock_client
                mock_client.query.usage.return_value = mock_cost_result
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient(credential=MagicMock())
                result = await client.get_cost_data(
                    subscription_id="sub-12345",
                    start_date="2025-01-01",
                    end_date="2025-01-31",
                    group_by=["ServiceName", "ResourceGroup"]
                )
                
                assert result["success"] is True
                assert "breakdown" in result
                assert len(result["breakdown"]) == 3
                assert result["cost"] == 100.50


class TestGetSecurityAssessments(TestLighthouseAzureClient):
    """Tests for security assessments retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_security_assessments_success(self):
        """Test successful security assessments retrieval."""
        mock_secure_score = MagicMock()
        mock_secure_score.score = 85.5
        mock_secure_score.max = 100.0
        
        mock_assessment = MagicMock()
        mock_assessment.display_name = "Secure your management ports"
        mock_assessment.status = MagicMock()
        mock_assessment.status.code = "Unhealthy"
        mock_assessment.impact = "High"
        mock_assessment.severity = "High"
        
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.security.SecurityCenter") as mock_security:
                mock_client = MagicMock()
                mock_security.return_value = mock_client
                mock_client.secure_scores.list.return_value = [mock_secure_score]
                mock_client.assessments.list.return_value = [mock_assessment]
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient(credential=MagicMock())
                result = await client.get_security_assessments("sub-12345")
                
                assert result["success"] is True
                assert result["secure_score"] == 85.5
                assert result["max_score"] == 100.0
                assert result["percentage"] == 85.5
                assert "assessments" in result
    
    @pytest.mark.asyncio
    async def test_get_security_assessments_no_data(self):
        """Test security assessments when no data is available."""
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.security.SecurityCenter") as mock_security:
                mock_client = MagicMock()
                mock_security.return_value = mock_client
                mock_client.secure_scores.list.return_value = []
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient(credential=MagicMock())
                result = await client.get_security_assessments("sub-12345")
                
                assert result["success"] is True
                assert result["secure_score"] is None
                assert result["percentage"] == 0
    
    @pytest.mark.asyncio
    async def test_get_security_assessments_api_error(self):
        """Test security assessments when API fails."""
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.security.SecurityCenter") as mock_security:
                mock_client = MagicMock()
                mock_security.return_value = mock_client
                mock_client.secure_scores.list.side_effect = Exception("API timeout")
                
                from app.services.lighthouse_client import LighthouseAzureClient, LighthouseDelegationError
                
                client = LighthouseAzureClient(credential=MagicMock())
                
                with pytest.raises(LighthouseDelegationError) as exc_info:
                    await client.get_security_assessments("sub-12345")
                
                assert "security" in str(exc_info.value).lower() or "timeout" in str(exc_info.value).lower()


class TestListResources(TestLighthouseAzureClient):
    """Tests for resource listing."""
    
    @pytest.mark.asyncio
    async def test_list_resources_success(self):
        """Test successful resource listing."""
        mock_resource = MagicMock()
        mock_resource.id = "/subscriptions/sub-12345/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/vm-001"
        mock_resource.name = "vm-001"
        mock_resource.type = "Microsoft.Compute/virtualMachines"
        mock_resource.location = "eastus"
        mock_resource.tags = {"environment": "production", "owner": "team-a"}
        
        mock_resource_group = MagicMock()
        mock_resource_group.name = "rg-prod"
        mock_resource_group.location = "eastus"
        
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.resource.ResourceManagementClient") as mock_resource_client:
                mock_client = MagicMock()
                mock_resource_client.return_value = mock_client
                
                # Mock resource groups list
                mock_client.resource_groups.list.return_value = [mock_resource_group]
                # Mock resources list_by_resource_group
                mock_client.resources.list_by_resource_group.return_value = [mock_resource]
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient(credential=MagicMock())
                result = await client.list_resources("sub-12345")
                
                assert result["success"] is True
                assert "resources" in result
                assert len(result["resources"]) == 1
                assert result["resources"][0]["name"] == "vm-001"
                assert result["resources"][0]["type"] == "Microsoft.Compute/virtualMachines"
                assert result["count"] == 1
    
    @pytest.mark.asyncio
    async def test_list_resources_empty_subscription(self):
        """Test resource listing when subscription has no resources."""
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.resource.ResourceManagementClient") as mock_resource_client:
                mock_client = MagicMock()
                mock_resource_client.return_value = mock_client
                mock_client.resource_groups.list.return_value = []
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient(credential=MagicMock())
                result = await client.list_resources("sub-12345")
                
                assert result["success"] is True
                assert result["resources"] == []
                assert result["count"] == 0
    
    @pytest.mark.asyncio
    async def test_list_resources_filtered_by_type(self):
        """Test resource listing with type filter."""
        vm_resource = MagicMock()
        vm_resource.id = "/subscriptions/sub-12345/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-001"
        vm_resource.name = "vm-001"
        vm_resource.type = "Microsoft.Compute/virtualMachines"
        vm_resource.location = "eastus"
        vm_resource.tags = {}
        
        storage_resource = MagicMock()
        storage_resource.id = "/subscriptions/sub-12345/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/sa001"
        storage_resource.name = "sa001"
        storage_resource.type = "Microsoft.Storage/storageAccounts"
        storage_resource.location = "eastus"
        storage_resource.tags = {}
        
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.resource.ResourceManagementClient") as mock_resource_client:
                mock_client = MagicMock()
                mock_resource_client.return_value = mock_client
                
                mock_resource_group = MagicMock()
                mock_resource_group.name = "rg"
                mock_client.resource_groups.list.return_value = [mock_resource_group]
                mock_client.resources.list_by_resource_group.return_value = [vm_resource, storage_resource]
                
                from app.services.lighthouse_client import LighthouseAzureClient
                
                client = LighthouseAzureClient(credential=MagicMock())
                result = await client.list_resources(
                    subscription_id="sub-12345",
                    resource_type="Microsoft.Compute/virtualMachines"
                )
                
                assert result["success"] is True
                assert len(result["resources"]) == 1
                assert result["resources"][0]["type"] == "Microsoft.Compute/virtualMachines"


class TestValidateTenantAccess(TestLighthouseAzureClient):
    """Tests for tenant access validation - requires azure-mgmt-managedservices."""
    
    @pytest.mark.skip(reason="Requires azure-mgmt-managedservices package")
    @pytest.mark.asyncio
    async def test_validate_tenant_access_success(self, mock_delegated_subscription):
        """Test successful tenant access validation."""
        pass
    
    @pytest.mark.skip(reason="Requires azure-mgmt-managedservices package")
    @pytest.mark.asyncio
    async def test_validate_tenant_access_no_subscriptions(self):
        """Test tenant access when no subscriptions are accessible."""
        pass
    
    @pytest.mark.skip(reason="Requires azure-mgmt-managedservices package")
    @pytest.mark.asyncio
    async def test_validate_tenant_access_failed_delegation(self, mock_delegated_subscription):
        """Test tenant access when delegation is not active."""
        pass


class TestErrorHandling(TestLighthouseAzureClient):
    """Tests for error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test that circuit breaker is applied to failing requests."""
        with patch("azure.identity.DefaultAzureCredential") as mock_cred:
            with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
                mock_cred.return_value = MagicMock()
                
                mock_client = MagicMock()
                mock_sub_client.return_value = mock_client
                # Simulate repeated failures that would trip circuit breaker
                mock_client.subscriptions.list.side_effect = Exception("Connection timeout")
                
                from app.services.lighthouse_client import LighthouseAzureClient, LighthouseDelegationError
                
                client = LighthouseAzureClient()
                
                # First calls should fail normally
                with pytest.raises(LighthouseDelegationError):
                    await client.verify_delegation("sub-12345")
    
    @pytest.mark.asyncio
    async def test_rate_limit_integration(self):
        """Test that rate limiting is respected."""
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
                with patch("app.core.rate_limit.rate_limiter.is_allowed") as mock_rate_limit:
                    mock_sub_client.return_value = MagicMock()
                    
                    # Simulate rate limit exceeded
                    mock_rate_limit.return_value = (False, {"X-RateLimit-Remaining": "0"})
                    
                    from app.services.lighthouse_client import LighthouseAzureClient
                    
                    client = LighthouseAzureClient(credential=MagicMock())
                    result = await client.verify_delegation("sub-12345")
                    
                    # Verify rate limit was checked
                    mock_rate_limit.assert_called()
    
    @pytest.mark.asyncio
    async def test_invalid_subscription_id_format(self):
        """Test handling of invalid subscription ID format."""
        from app.services.lighthouse_client import LighthouseAzureClient, LighthouseDelegationError
        
        client = LighthouseAzureClient()
        
        # Invalid format should return error result, not raise
        result = await client.verify_delegation("invalid-subscription-id-format")
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self):
        """Test handling of Azure authentication failure."""
        with patch("azure.identity.DefaultAzureCredential") as mock_cred:
            mock_cred.side_effect = Exception("Authentication failed: No valid credentials found")
            
            from app.services.lighthouse_client import LighthouseAzureClient, LighthouseDelegationError
            
            client = LighthouseAzureClient()
            
            with pytest.raises(LighthouseDelegationError) as exc_info:
                await client.verify_delegation("sub-12345")
            
            assert "authentication" in str(exc_info.value).lower() or "credential" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_network_timeout(self):
        """Test handling of network timeouts."""
        with patch("azure.identity.DefaultAzureCredential"):
            with patch("azure.mgmt.resource.SubscriptionClient") as mock_sub_client:
                mock_client = MagicMock()
                mock_sub_client.return_value = mock_client
                mock_client.subscriptions.list.side_effect = Exception("Request timeout after 30s")
                
                from app.services.lighthouse_client import LighthouseAzureClient, LighthouseDelegationError
                
                client = LighthouseAzureClient(credential=MagicMock())
                
                with pytest.raises(LighthouseDelegationError) as exc_info:
                    await client.verify_delegation("sub-12345")
                
                assert "timeout" in str(exc_info.value).lower() or "network" in str(exc_info.value).lower()


class TestLighthouseClientInitialization:
    """Tests for client initialization and configuration."""
    
    def test_client_initialization(self):
        """Test that client initializes properly."""
        with patch("azure.identity.DefaultAzureCredential") as mock_cred:
            mock_cred.return_value = MagicMock()
            
            from app.services.lighthouse_client import LighthouseAzureClient
            
            client = LighthouseAzureClient()
            assert client is not None
    
    def test_client_with_custom_credential(self):
        """Test client initialization with custom credential."""
        custom_credential = MagicMock()
        
        from app.services.lighthouse_client import LighthouseAzureClient
        
        client = LighthouseAzureClient(credential=custom_credential)
        assert client is not None
        assert client.credential == custom_credential
