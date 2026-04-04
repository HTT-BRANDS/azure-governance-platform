"""Tests for app/preflight/azure/network.py — subscription & Graph checks.

Covers:
- AzureSubscriptionsCheck / AzureGraphCheck class init
- check_azure_subscriptions: pass, no subs, disabled subs, auth error,
  403 forbidden, generic error
- check_graph_api_access: pass, 403 admin consent, auth error, 401, generic error

Phase B.6 of the test coverage sprint.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.preflight.models import CheckCategory, CheckStatus

# ---------------------------------------------------------------------------
# AzureSubscriptionsCheck class
# ---------------------------------------------------------------------------


class TestAzureSubscriptionsCheckClass:
    def test_init(self):
        from app.preflight.azure.network import AzureSubscriptionsCheck

        check = AzureSubscriptionsCheck()
        assert check.check_id == "azure_subscriptions"
        assert check.category == CheckCategory.AZURE_SUBSCRIPTIONS


class TestAzureGraphCheckClass:
    def test_init(self):
        from app.preflight.azure.network import AzureGraphCheck

        check = AzureGraphCheck()
        assert check.check_id == "graph_api"
        assert check.category == CheckCategory.AZURE_GRAPH


# ---------------------------------------------------------------------------
# check_azure_subscriptions
# ---------------------------------------------------------------------------


def _mock_subscription(sub_id="sub-1", name="My Sub", state_value="Enabled"):
    sub = MagicMock()
    sub.subscription_id = sub_id
    sub.display_name = name
    sub.state.value = state_value
    sub.tenant_id = "tid-1"
    return sub


class TestCheckAzureSubscriptions:
    @patch("app.preflight.azure.network.azure_client_manager")
    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_pass_with_subscriptions(self, mock_cred, mock_mgr):
        client = MagicMock()
        client.subscriptions.list.return_value = [
            _mock_subscription("s1", "Sub 1"),
            _mock_subscription("s2", "Sub 2"),
        ]
        mock_mgr.get_subscription_client.return_value = client

        from app.preflight.azure.network import check_azure_subscriptions

        result = await check_azure_subscriptions("tid-1")

        assert result.status == CheckStatus.PASS
        assert "2 subscription" in result.message

    @patch("app.preflight.azure.network.azure_client_manager")
    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_warning_no_subscriptions(self, mock_cred, mock_mgr):
        client = MagicMock()
        client.subscriptions.list.return_value = []
        mock_mgr.get_subscription_client.return_value = client

        from app.preflight.azure.network import check_azure_subscriptions

        result = await check_azure_subscriptions("tid-1")

        assert result.status == CheckStatus.WARNING
        assert "No subscriptions" in result.message

    @patch("app.preflight.azure.network.azure_client_manager")
    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_warning_disabled_subscriptions(self, mock_cred, mock_mgr):
        client = MagicMock()
        client.subscriptions.list.return_value = [
            _mock_subscription("s1", "Active", "Enabled"),
            _mock_subscription("s2", "Dead", "Disabled"),
        ]
        mock_mgr.get_subscription_client.return_value = client

        from app.preflight.azure.network import check_azure_subscriptions

        result = await check_azure_subscriptions("tid-1")

        assert result.status == CheckStatus.WARNING
        assert "disabled" in result.message.lower()

    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_fail_auth_error(self, mock_cred):
        from azure.core.exceptions import ClientAuthenticationError

        mock_cred.side_effect = ClientAuthenticationError("bad creds")

        from app.preflight.azure.network import check_azure_subscriptions

        result = await check_azure_subscriptions("tid-1")

        assert result.status == CheckStatus.FAIL
        assert "Authentication failed" in result.message

    @patch("app.preflight.azure.network.azure_client_manager")
    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_fail_403_forbidden(self, mock_cred, mock_mgr):
        from azure.core.exceptions import HttpResponseError

        client = MagicMock()
        err = HttpResponseError(message="forbidden")
        err.status_code = 403
        client.subscriptions.list.side_effect = err
        mock_mgr.get_subscription_client.return_value = client

        from app.preflight.azure.network import check_azure_subscriptions

        result = await check_azure_subscriptions("tid-1")

        assert result.status == CheckStatus.FAIL
        assert "403" in result.message

    @patch("app.preflight.azure.network.azure_client_manager")
    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_fail_generic_error(self, mock_cred, mock_mgr):
        mock_mgr.get_subscription_client.side_effect = RuntimeError("boom")

        from app.preflight.azure.network import check_azure_subscriptions

        result = await check_azure_subscriptions("tid-1")

        assert result.status == CheckStatus.FAIL
        assert "RuntimeError" in result.message


# ---------------------------------------------------------------------------
# check_graph_api_access
# ---------------------------------------------------------------------------


class TestCheckGraphApiAccess:
    @patch("app.preflight.azure.network.httpx.AsyncClient")
    @patch("app.preflight.azure.network.asyncio.to_thread")
    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_pass(self, mock_cred, mock_to_thread, mock_httpx_cls):
        token = MagicMock()
        token.token = "fake-token"
        mock_to_thread.return_value = token

        # Mock the async context manager and responses
        mock_client = AsyncMock()
        mock_httpx_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_httpx_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        user_resp = MagicMock()
        user_resp.status_code = 200
        user_resp.json.return_value = {"value": [{"id": "u1", "displayName": "Test"}]}
        user_resp.raise_for_status = MagicMock()

        org_resp = MagicMock()
        org_resp.status_code = 200
        org_resp.json.return_value = {
            "value": [{"displayName": "Acme", "tenantType": "AAD", "createdDateTime": "2024-01-01"}]
        }

        mock_client.get = AsyncMock(side_effect=[user_resp, org_resp])

        from app.preflight.azure.network import check_graph_api_access

        result = await check_graph_api_access("tid-1")

        assert result.status == CheckStatus.PASS
        assert "verified" in result.message

    @patch("app.preflight.azure.network.httpx.AsyncClient")
    @patch("app.preflight.azure.network.asyncio.to_thread")
    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_403_admin_consent_required(self, mock_cred, mock_to_thread, mock_httpx_cls):
        token = MagicMock()
        token.token = "fake-token"
        mock_to_thread.return_value = token

        mock_client = AsyncMock()
        mock_httpx_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_httpx_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = MagicMock()
        resp.status_code = 403
        mock_client.get = AsyncMock(return_value=resp)

        from app.preflight.azure.network import check_graph_api_access

        result = await check_graph_api_access("tid-1")

        assert result.status == CheckStatus.FAIL
        assert "admin consent" in result.message.lower()

    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_fail_auth_error(self, mock_cred):
        from azure.core.exceptions import ClientAuthenticationError

        mock_cred.side_effect = ClientAuthenticationError("bad token")

        from app.preflight.azure.network import check_graph_api_access

        result = await check_graph_api_access("tid-1")

        assert result.status == CheckStatus.FAIL
        assert "authentication failed" in result.message.lower()

    @patch("app.preflight.azure.network._get_credential")
    @pytest.mark.asyncio
    async def test_fail_generic_error(self, mock_cred):
        mock_cred.side_effect = RuntimeError("network down")

        from app.preflight.azure.network import check_graph_api_access

        result = await check_graph_api_access("tid-1")

        assert result.status == CheckStatus.FAIL
        assert "RuntimeError" in result.message
