"""Tests for cost synchronization module."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from sqlalchemy.exc import SQLAlchemyError

from app.core.sync.costs import sync_costs


class TestCostSync:
    """Test suite for cost synchronization."""

    @pytest.mark.asyncio
    async def test_sync_costs_success(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_subscription,
    ):
        """Test successful cost synchronization."""
        # Setup
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [mock_subscription]
        
        # Mock cost query result
        mock_result = MagicMock()
        mock_result.properties = MagicMock()
        mock_result.properties.rows = [
            [10.50, 20240115, "USD", "rg-test", "Storage"],
            [25.00, 20240115, "USD", "rg-test", "Compute"],
        ]
        
        mock_cost_client = MagicMock()
        mock_cost_client.query = MagicMock()
        mock_cost_client.query.usage = MagicMock(return_value=mock_result)
        mock_azure_client_manager["costs"].get_cost_client.return_value = mock_cost_client
        
        # Execute
        await sync_costs()
        
        # Verify
        mock_azure_client_manager["costs"].list_subscriptions.assert_called_once_with(
            mock_tenant.tenant_id
        )
        mock_cost_client.query.usage.assert_called_once()
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_sync_costs_empty_data(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_subscription,
    ):
        """Test cost sync with empty data."""
        # Setup - no rows returned
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [mock_subscription]
        
        mock_result = MagicMock()
        mock_result.properties = MagicMock()
        mock_result.properties.rows = []
        
        mock_cost_client = MagicMock()
        mock_cost_client.query = MagicMock()
        mock_cost_client.query.usage = MagicMock(return_value=mock_result)
        mock_azure_client_manager["costs"].get_cost_client.return_value = mock_cost_client
        
        # Execute - should not raise
        await sync_costs()
        
        # Verify - should complete without errors
        mock_cost_client.query.usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_costs_no_subscriptions(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
    ):
        """Test cost sync with no subscriptions."""
        # Setup
        mock_azure_client_manager["costs"].list_subscriptions.return_value = []
        
        # Execute - should not raise
        await sync_costs()
        
        # Verify - no cost client should be created
        mock_azure_client_manager["costs"].get_cost_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_costs_disabled_subscription(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_disabled_subscription,
    ):
        """Test cost sync skips disabled subscriptions."""
        # Setup
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [
            mock_disabled_subscription
        ]
        
        # Execute
        await sync_costs()
        
        # Verify - should skip disabled subscriptions
        mock_azure_client_manager["costs"].get_cost_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_costs_http_error(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_subscription,
    ):
        """Test cost sync handles HTTP errors gracefully."""
        # Setup
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [mock_subscription]
        
        mock_cost_client = MagicMock()
        error = MagicMock()
        error.status_code = 403
        error.message = "Access denied"
        mock_cost_client.query = MagicMock()
        mock_cost_client.query.usage = MagicMock(side_effect=Exception("HTTP 403"))
        mock_azure_client_manager["costs"].get_cost_client.return_value = mock_cost_client
        
        # Execute - should not raise, just log error
        await sync_costs()
        
        # Verify - error handled gracefully
        mock_cost_client.query.usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_costs_auth_error(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_subscription,
    ):
        """Test cost sync handles authentication errors."""
        # Setup
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [mock_subscription]
        
        mock_cost_client = MagicMock()
        mock_cost_client.query = MagicMock()
        mock_cost_client.query.usage = MagicMock(side_effect=Exception("Auth failed"))
        mock_azure_client_manager["costs"].get_cost_client.return_value = mock_cost_client
        
        # Execute - should not raise
        await sync_costs()
        
        # Verify - error handled
        mock_cost_client.query.usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_costs_db_error(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_subscription,
    ):
        """Test cost sync handles database errors."""
        # Setup
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [mock_subscription]
        
        mock_result = MagicMock()
        mock_result.properties = MagicMock()
        mock_result.properties.rows = [[10.50, 20240115, "USD", "rg-test", "Storage"]]
        
        mock_cost_client = MagicMock()
        mock_cost_client.query = MagicMock()
        mock_cost_client.query.usage = MagicMock(return_value=mock_result)
        mock_azure_client_manager["costs"].get_cost_client.return_value = mock_cost_client
        
        # Make db.commit raise an error
        mock_db_session.commit.side_effect = SQLAlchemyError("Database error")
        
        # Execute - should not raise
        await sync_costs()

    @pytest.mark.asyncio
    async def test_sync_costs_zero_cost_skipped(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_subscription,
    ):
        """Test that zero cost entries are skipped."""
        # Setup
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [mock_subscription]
        
        mock_result = MagicMock()
        mock_result.properties = MagicMock()
        mock_result.properties.rows = [
            [10.50, 20240115, "USD", "rg-test", "Storage"],
            [0.0, 20240115, "USD", "rg-test", "Network"],  # Should be skipped
            [0.00, 20240115, "USD", "rg-test", "DNS"],  # Should be skipped
        ]
        
        mock_cost_client = MagicMock()
        mock_cost_client.query = MagicMock()
        mock_cost_client.query.usage = MagicMock(return_value=mock_result)
        mock_azure_client_manager["costs"].get_cost_client.return_value = mock_cost_client
        
        # Execute
        await sync_costs()
        
        # Verify - only 1 record added (zero costs skipped)
        assert mock_db_session.add.call_count == 1

    @pytest.mark.asyncio
    async def test_sync_costs_malformed_row(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_subscription,
    ):
        """Test handling of malformed cost rows."""
        # Setup
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [mock_subscription]
        
        mock_result = MagicMock()
        mock_result.properties = MagicMock()
        mock_result.properties.rows = [
            [10.50, 20240115, "USD", "rg-test", "Storage"],
            [],  # Malformed row
            [25.00, 20240115],  # Missing columns
        ]
        
        mock_cost_client = MagicMock()
        mock_cost_client.query = MagicMock()
        mock_cost_client.query.usage = MagicMock(return_value=mock_result)
        mock_azure_client_manager["costs"].get_cost_client.return_value = mock_cost_client
        
        # Execute - should not raise
        await sync_costs()
        
        # Verify - valid row processed
        assert mock_db_session.add.call_count >= 1

    @pytest.mark.asyncio
    async def test_sync_costs_multiple_tenants(
        self,
        mock_azure_client_manager,
        mock_db_session,
        mock_get_db_context,
        mock_tenant,
        mock_subscription,
    ):
        """Test syncing costs from multiple tenants."""
        # Create second tenant
        tenant2 = MagicMock()
        tenant2.id = "tenant-2-uuid"
        tenant2.tenant_id = "test-tenant-id-456"
        tenant2.name = "Test Tenant 2"
        tenant2.is_active = True
        
        # Setup to return two tenants
        mock_db_query = MagicMock()
        mock_db_query.filter.return_value = mock_db_query
        mock_db_query.all.return_value = [mock_tenant, tenant2]
        mock_db_session.query.return_value = mock_db_query
        
        mock_azure_client_manager["costs"].list_subscriptions.return_value = [mock_subscription]
        
        mock_result = MagicMock()
        mock_result.properties = MagicMock()
        mock_result.properties.rows = [[10.50, 20240115, "USD", "rg-test", "Storage"]]
        
        mock_cost_client = MagicMock()
        mock_cost_client.query = MagicMock()
        mock_cost_client.query.usage = MagicMock(return_value=mock_result)
        mock_azure_client_manager["costs"].get_cost_client.return_value = mock_cost_client
        
        # Execute
        await sync_costs()
        
        # Verify - called for each tenant
        assert mock_azure_client_manager["costs"].list_subscriptions.call_count == 2
