"""Tests for sync tenant eligibility helpers."""

from unittest.mock import MagicMock, patch

from app.core.sync.utils import get_sync_eligible_tenants, tenant_is_sync_eligible


def _tenant(**overrides):
    tenant = MagicMock()
    tenant.is_active = True
    tenant.tenant_id = "tenant-123"
    tenant.client_id = None
    tenant.client_secret_ref = None
    tenant.use_lighthouse = False
    for key, value in overrides.items():
        setattr(tenant, key, value)
    return tenant


class TestTenantIsSyncEligible:
    def test_inactive_tenant_is_not_eligible(self):
        with patch("app.core.sync.utils.settings") as settings:
            settings.use_uami_auth = False
            settings.use_oidc_federation = False
            settings.key_vault_url = None
            settings.azure_client_id = "shared-client"
            settings.azure_client_secret = (
                "shared-credential-placeholder"  # pragma: allowlist secret
            )

            assert tenant_is_sync_eligible(_tenant(is_active=False)) is False

    def test_secret_mode_without_keyvault_uses_shared_credentials(self):
        with patch("app.core.sync.utils.settings") as settings:
            settings.use_uami_auth = False
            settings.use_oidc_federation = False
            settings.key_vault_url = None
            settings.azure_client_id = "shared-client"
            settings.azure_client_secret = (
                "shared-credential-placeholder"  # pragma: allowlist secret
            )

            assert tenant_is_sync_eligible(_tenant()) is True

    def test_keyvault_mode_rejects_unknown_unconfigured_tenant(self):
        with patch("app.core.sync.utils.settings") as settings:
            settings.use_uami_auth = False
            settings.use_oidc_federation = False
            settings.key_vault_url = "https://vault.example"
            settings.azure_client_id = "shared-client"
            settings.azure_client_secret = (
                "shared-credential-placeholder"  # pragma: allowlist secret
            )
            with patch("app.core.sync.utils.get_tenant_by_id", return_value=None):
                assert tenant_is_sync_eligible(_tenant()) is False

    def test_keyvault_mode_allows_lighthouse_tenant(self):
        with patch("app.core.sync.utils.settings") as settings:
            settings.use_uami_auth = False
            settings.use_oidc_federation = False
            settings.key_vault_url = "https://vault.example"
            settings.azure_client_id = "shared-client"
            settings.azure_client_secret = (
                "shared-credential-placeholder"  # pragma: allowlist secret
            )

            assert tenant_is_sync_eligible(_tenant(use_lighthouse=True)) is True

    def test_oidc_mode_requires_resolvable_app_id(self):
        with patch("app.core.sync.utils.settings") as settings:
            settings.use_uami_auth = False
            settings.use_oidc_federation = True
            settings.key_vault_url = None
            settings.azure_client_id = None
            settings.azure_client_secret = None
            with patch("app.core.sync.utils.get_app_id_for_tenant", return_value=None):
                assert tenant_is_sync_eligible(_tenant()) is False
            with patch("app.core.sync.utils.get_app_id_for_tenant", return_value="app-123"):
                assert tenant_is_sync_eligible(_tenant()) is True


class TestGetSyncEligibleTenants:
    def test_filters_ineligible_tenants(self):
        tenants = [_tenant(tenant_id="good-1"), _tenant(tenant_id="bad-1")]
        with patch("app.core.sync.utils.settings") as settings:
            settings.use_uami_auth = False
            settings.use_oidc_federation = False
            settings.key_vault_url = "https://vault.example"
            settings.azure_client_id = "shared-client"
            settings.azure_client_secret = (
                "shared-credential-placeholder"  # pragma: allowlist secret
            )
            with patch(
                "app.core.sync.utils.get_tenant_by_id",
                side_effect=lambda tenant_id: MagicMock() if tenant_id == "good-1" else None,
            ):
                eligible = get_sync_eligible_tenants(tenants)

        assert [tenant.tenant_id for tenant in eligible] == ["good-1"]
