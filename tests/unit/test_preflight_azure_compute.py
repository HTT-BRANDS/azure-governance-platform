"""Tests for app/preflight/azure/compute.py — Resource Manager checks.

Covers:
- AzureResourcesCheck class init & skip path
- check_resource_manager_access: pass, 403, generic error

Phase B.8 of the test coverage sprint.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.preflight.models import CheckCategory, CheckResult, CheckStatus

# ---------------------------------------------------------------------------
# AzureResourcesCheck class
# ---------------------------------------------------------------------------


class TestAzureResourcesCheckClass:
    def test_init(self):
        from app.preflight.azure.compute import AzureResourcesCheck

        check = AzureResourcesCheck()
        assert check.check_id == "azure_resources"
        assert check.category == CheckCategory.AZURE_RESOURCES

    @patch("app.preflight.azure.network.check_azure_subscriptions")
    @pytest.mark.asyncio
    async def test_execute_skips_when_no_subs(self, mock_sub_check):
        mock_sub_check.return_value = CheckResult(
            check_id="azure_subscriptions",
            name="test",
            category=CheckCategory.AZURE_SUBSCRIPTIONS,
            status=CheckStatus.FAIL,
            message="no subs",
        )
        from app.preflight.azure.compute import AzureResourcesCheck

        check = AzureResourcesCheck()
        result = await check._execute_check(tenant_id="tid-1")

        assert result.status == CheckStatus.SKIPPED


# ---------------------------------------------------------------------------
# check_resource_manager_access
# ---------------------------------------------------------------------------


def _mock_rg(name="rg-1", location="eastus", state="Succeeded"):
    rg = MagicMock()
    rg.name = name
    rg.location = location
    rg.properties.provisioning_state = state
    return rg


class TestCheckResourceManagerAccess:
    @patch("app.preflight.azure.compute.azure_client_manager")
    @pytest.mark.asyncio
    async def test_pass_with_resource_groups(self, mock_mgr):
        client = MagicMock()
        client.resource_groups.list.return_value = [
            _mock_rg("rg-1"),
            _mock_rg("rg-2"),
        ]
        # Resources in first RG
        client.resources.list_by_resource_group.return_value = [MagicMock()] * 5
        mock_mgr.get_resource_client.return_value = client

        from app.preflight.azure.compute import check_resource_manager_access

        result = await check_resource_manager_access("tid-1", "sub-1")

        assert result.status == CheckStatus.PASS
        assert "2 resource groups" in result.message

    @patch("app.preflight.azure.compute.azure_client_manager")
    @pytest.mark.asyncio
    async def test_pass_no_resource_groups(self, mock_mgr):
        client = MagicMock()
        client.resource_groups.list.return_value = []
        mock_mgr.get_resource_client.return_value = client

        from app.preflight.azure.compute import check_resource_manager_access

        result = await check_resource_manager_access("tid-1", "sub-1")

        assert result.status == CheckStatus.PASS
        assert "0 resource groups" in result.message

    @patch("app.preflight.azure.compute.azure_client_manager")
    @pytest.mark.asyncio
    async def test_fail_403(self, mock_mgr):
        from azure.core.exceptions import HttpResponseError

        err = HttpResponseError(message="forbidden")
        err.status_code = 403
        client = MagicMock()
        client.resource_groups.list.side_effect = err
        mock_mgr.get_resource_client.return_value = client

        from app.preflight.azure.compute import check_resource_manager_access

        result = await check_resource_manager_access("tid-1", "sub-1")

        assert result.status == CheckStatus.FAIL
        assert "403" in result.message

    @patch("app.preflight.azure.compute.azure_client_manager")
    @pytest.mark.asyncio
    async def test_fail_generic(self, mock_mgr):
        mock_mgr.get_resource_client.side_effect = RuntimeError("kaboom")

        from app.preflight.azure.compute import check_resource_manager_access

        result = await check_resource_manager_access("tid-1", "sub-1")

        assert result.status == CheckStatus.FAIL
        assert "RuntimeError" in result.message

    @patch("app.preflight.azure.compute.azure_client_manager")
    @pytest.mark.asyncio
    async def test_reraises_non_403_http_error(self, mock_mgr):
        from azure.core.exceptions import HttpResponseError

        err = HttpResponseError(message="server error")
        err.status_code = 500
        client = MagicMock()
        client.resource_groups.list.side_effect = err
        mock_mgr.get_resource_client.return_value = client

        from app.preflight.azure.compute import check_resource_manager_access

        with pytest.raises(HttpResponseError):
            await check_resource_manager_access("tid-1", "sub-1")
