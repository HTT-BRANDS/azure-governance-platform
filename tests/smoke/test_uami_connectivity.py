"""Smoke tests for Phase C UAMI (User-Assigned Managed Identity) connectivity.

These tests validate the UAMI authentication flow in real Azure environments.
They require actual Azure infrastructure to be deployed and configured.

Required Environment:
- Azure App Service with User-Assigned Managed Identity assigned
- UAMI created with name 'mi-governance-platform'
- Federated Identity Credential on multi-tenant app
- Key Vault with RBAC access for UAMI

Skip Conditions:
- Not running in Azure App Service
- USE_UAMI_AUTH not set to 'true'
- UAMI_CLIENT_ID not configured
"""

import os

import pytest

# Skip all tests if not in appropriate environment
pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        os.environ.get("USE_UAMI_AUTH") != "true",
        reason="USE_UAMI_AUTH not enabled",
    ),
    pytest.mark.skipif(
        not os.environ.get("UAMI_CLIENT_ID"),
        reason="UAMI_CLIENT_ID not configured",
    ),
]


def is_running_in_azure() -> bool:
    """Check if running in Azure environment."""
    return bool(
        os.environ.get("WEBSITE_SITE_NAME")  # App Service
        or os.environ.get("AZURE_FEDERATED_TOKEN_FILE")  # GitHub Actions OIDC
    )


# ============================================================================
# Smoke Tests
# ============================================================================


@pytest.mark.skipif(not is_running_in_azure(), reason="Not running in Azure environment")
class TestUAMIAvailability:
    """Test UAMI is available and configured correctly."""

    def test_uami_environment_variables_set(self):
        """Required environment variables should be set."""
        assert os.environ.get("UAMI_CLIENT_ID"), "UAMI_CLIENT_ID not set"
        assert os.environ.get("USE_UAMI_AUTH") == "true", "USE_UAMI_AUTH not true"

    def test_uami_client_id_is_valid_uuid(self):
        """UAMI_CLIENT_ID should be a valid UUID."""
        import uuid

        uami_client_id = os.environ.get("UAMI_CLIENT_ID")
        try:
            uuid.UUID(uami_client_id)
        except ValueError:
            pytest.fail(f"UAMI_CLIENT_ID is not a valid UUID: {uami_client_id}")

    def test_uami_provider_is_available(self):
        """UAMI provider should report as available."""
        from app.core.uami_credential import get_uami_provider

        provider = get_uami_provider()
        assert provider.is_available(), "UAMI provider reports as not available"

    def test_uami_environment_detection(self):
        """Environment detection should correctly identify Azure."""
        from app.core.uami_credential import get_uami_provider

        provider = get_uami_provider()
        env_info = provider.get_environment_info()

        assert env_info["uami_configured"] is True, "UAMI not configured"
        assert env_info["can_use_uami"] is True, "Cannot use UAMI"

        # Should be in App Service or GitHub Actions
        assert env_info["is_app_service"] or env_info["is_github_actions"], (
            "Not in supported Azure environment"
        )


@pytest.mark.skipif(not is_running_in_azure(), reason="Not running in Azure environment")
class TestUAMICredentialCreation:
    """Test UAMI credential can be created for tenants."""

    def test_credential_created_for_tenant(self):
        """Should successfully create credential for a tenant."""
        # Get first active tenant
        from app.core.tenants_config import get_active_tenants
        from app.core.uami_credential import get_uami_provider

        active_tenants = get_active_tenants()
        if not active_tenants:
            pytest.skip("No active tenants configured")

        tenant_code = list(active_tenants.keys())[0]
        tenant_config = active_tenants[tenant_code]

        # Get UAMI provider
        provider = get_uami_provider()

        # Create credential
        credential = provider.get_credential_for_tenant(
            tenant_id=tenant_config.tenant_id,
            client_id=tenant_config.app_id,
        )

        assert credential is not None, "Credential creation failed"

    def test_credential_is_client_assertion_type(self):
        """Created credential should be ClientAssertionCredential."""
        from azure.identity import ClientAssertionCredential

        from app.core.tenants_config import get_active_tenants
        from app.core.uami_credential import get_uami_provider

        active_tenants = get_active_tenants()
        if not active_tenants:
            pytest.skip("No active tenants configured")

        tenant_code = list(active_tenants.keys())[0]
        tenant_config = active_tenants[tenant_code]

        provider = get_uami_provider()
        credential = provider.get_credential_for_tenant(
            tenant_id=tenant_config.tenant_id,
            client_id=tenant_config.app_id,
        )

        assert isinstance(credential, ClientAssertionCredential), (
            "Credential is not ClientAssertionCredential"
        )


@pytest.mark.skipif(not is_running_in_azure(), reason="Not running in Azure environment")
class TestUAMITokenAcquisition:
    """Test actual token acquisition from Azure AD."""

    def test_can_get_token_for_graph_api(self):
        """Should successfully get token for Microsoft Graph API."""
        from app.core.tenants_config import get_active_tenants
        from app.core.uami_credential import get_uami_provider

        active_tenants = get_active_tenants()
        if not active_tenants:
            pytest.skip("No active tenants configured")

        tenant_code = list(active_tenants.keys())[0]
        tenant_config = active_tenants[tenant_code]

        provider = get_uami_provider()

        try:
            token = provider.get_token_for_tenant(
                tenant_id=tenant_config.tenant_id,
                client_id=tenant_config.app_id,
                scope="https://graph.microsoft.com/.default",
            )

            assert token is not None, "Token acquisition returned None"
            assert isinstance(token, str), "Token is not a string"
            assert len(token) > 0, "Token is empty"
            assert "." in token, "Token does not appear to be a JWT"

        except Exception as e:
            pytest.fail(f"Token acquisition failed: {e}")

    def test_token_is_valid_jwt_format(self):
        """Acquired token should be in valid JWT format."""
        import base64
        import json

        from app.core.tenants_config import get_active_tenants
        from app.core.uami_credential import get_uami_provider

        active_tenants = get_active_tenants()
        if not active_tenants:
            pytest.skip("No active tenants configured")

        tenant_code = list(active_tenants.keys())[0]
        tenant_config = active_tenants[tenant_code]

        provider = get_uami_provider()

        try:
            token = provider.get_token_for_tenant(
                tenant_id=tenant_config.tenant_id,
                client_id=tenant_config.app_id,
                scope="https://graph.microsoft.com/.default",
            )

            # Parse JWT structure (header.payload.signature)
            parts = token.split(".")
            assert len(parts) == 3, "Token is not in JWT format (expected 3 parts)"

            # Try to decode header
            header_b64 = parts[0]
            # Add padding if needed
            padding = 4 - len(header_b64) % 4
            if padding != 4:
                header_b64 += "=" * padding

            header_json = base64.urlsafe_b64decode(header_b64)
            header = json.loads(header_json)

            assert "typ" in header, "JWT header missing 'typ'"
            assert header["typ"] == "JWT", "JWT type is not 'JWT'"

        except Exception as e:
            pytest.fail(f"Token validation failed: {e}")


@pytest.mark.skipif(not is_running_in_azure(), reason="Not running in Azure environment")
class TestUAMICaching:
    """Test UAMI token caching behavior."""

    def test_token_is_cached(self):
        """Token should be cached after first acquisition."""
        from app.core.tenants_config import get_active_tenants
        from app.core.uami_credential import get_uami_provider

        active_tenants = get_active_tenants()
        if not active_tenants:
            pytest.skip("No active tenants configured")

        tenant_code = list(active_tenants.keys())[0]
        tenant_config = active_tenants[tenant_code]

        provider = get_uami_provider()

        # Clear cache first
        provider.clear_cache(tenant_id=tenant_config.tenant_id)

        # Get initial cache stats
        initial_stats = provider.get_cache_stats()
        initial_size = initial_stats["token_cache_size"]

        # Acquire token
        provider.get_token_for_tenant(
            tenant_id=tenant_config.tenant_id,
            client_id=tenant_config.app_id,
            scope="https://graph.microsoft.com/.default",
        )

        # Check cache grew
        final_stats = provider.get_cache_stats()
        assert final_stats["token_cache_size"] > initial_size, "Token was not cached"

    def test_cache_can_be_cleared(self):
        """Cache should be clearable."""
        from app.core.tenants_config import get_active_tenants
        from app.core.uami_credential import get_uami_provider

        active_tenants = get_active_tenants()
        if not active_tenants:
            pytest.skip("No active tenants configured")

        tenant_code = list(active_tenants.keys())[0]
        tenant_config = active_tenants[tenant_code]

        provider = get_uami_provider()

        # Acquire and cache token
        provider.get_token_for_tenant(
            tenant_id=tenant_config.tenant_id,
            client_id=tenant_config.app_id,
            scope="https://graph.microsoft.com/.default",
        )

        # Verify cache has entries
        stats_before = provider.get_cache_stats()
        assert stats_before["token_cache_size"] > 0, "Cache should have entries"

        # Clear cache
        provider.clear_cache()

        # Verify cache is empty
        stats_after = provider.get_cache_stats()
        assert stats_after["token_cache_size"] == 0, "Cache should be empty after clear"


@pytest.mark.skipif(not is_running_in_azure(), reason="Not running in Azure environment")
class TestKeyVaultAccess:
    """Test UAMI can access Key Vault."""

    def test_key_vault_url_configured(self):
        """Key Vault URL should be configured."""
        from app.core.config import get_settings

        settings = get_settings()
        assert settings.key_vault_url, "Key Vault URL not configured"

    def test_can_list_key_vault_secrets(self):
        """UAMI should be able to list secrets in Key Vault."""
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        from app.core.config import get_settings

        settings = get_settings()
        if not settings.key_vault_url:
            pytest.skip("Key Vault URL not configured")

        try:
            # Use DefaultAzureCredential which will use the UAMI
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=settings.key_vault_url, credential=credential)

            # Try to list secrets (should not raise)
            secrets = list(client.list_properties_of_secrets())

            # We should be able to list, even if empty
            assert isinstance(secrets, list), "Secrets listing did not return a list"

        except Exception as e:
            # Check if it's an auth error
            error_msg = str(e).lower()
            if "forbidden" in error_msg or "unauthorized" in error_msg:
                pytest.fail(f"UAMI cannot access Key Vault (RBAC issue): {e}")
            elif "not found" in error_msg:
                pytest.skip(f"Key Vault not found: {e}")
            else:
                pytest.fail(f"Key Vault access failed: {e}")


@pytest.mark.skipif(not is_running_in_azure(), reason="Not running in Azure environment")
class TestMultiTenantSupport:
    """Test UAMI works with all configured tenants."""

    def test_all_tenants_can_get_credentials(self):
        """All active tenants should be able to get UAMI credentials."""
        from app.core.tenants_config import get_active_tenants
        from app.core.uami_credential import get_uami_provider

        active_tenants = get_active_tenants()
        if not active_tenants:
            pytest.skip("No active tenants configured")

        provider = get_uami_provider()
        failures = []

        for code, config in active_tenants.items():
            try:
                credential = provider.get_credential_for_tenant(
                    tenant_id=config.tenant_id,
                    client_id=config.app_id,
                )

                if credential is None:
                    failures.append(f"{code}: credential is None")

            except Exception as e:
                failures.append(f"{code}: {e}")

        if failures:
            pytest.fail(f"Some tenants failed credential creation: {failures}")


# ============================================================================
# Configuration Validation Tests
# ============================================================================


class TestConfigurationValidation:
    """Validate UAMI configuration without requiring Azure connection."""

    def test_uami_settings_in_config(self):
        """Config should have UAMI-related settings defined."""
        from app.core.config import get_settings

        settings = get_settings()

        # These settings should exist
        assert hasattr(settings, "use_uami_auth"), "use_uami_auth setting missing"
        assert hasattr(settings, "uami_client_id"), "uami_client_id setting missing"
        assert hasattr(settings, "federated_identity_credential_id"), (
            "federated_identity_credential_id setting missing"
        )

    def test_uami_credential_module_imports(self):
        """UAMI credential module should import successfully."""
        try:
            from app.core.uami_credential import (
                UAMICredentialError,  # noqa: F401
                UAMICredentialProvider,  # noqa: F401
                get_uami_provider,  # noqa: F401
            )
        except ImportError as e:
            pytest.fail(f"Failed to import UAMI credential module: {e}")

    def test_uami_provider_singleton(self):
        """UAMI provider should work as singleton."""
        from app.core.uami_credential import get_uami_provider, reset_provider

        reset_provider()

        provider1 = get_uami_provider()
        provider2 = get_uami_provider()

        assert provider1 is provider2, "UAMI provider is not a singleton"


# ============================================================================
# Fallback Tests (when not in Azure)
# ============================================================================


class TestFallbackBehavior:
    """Test behavior when not in Azure environment."""

    @pytest.mark.skipif(is_running_in_azure(), reason="Running in Azure")
    def test_uami_not_available_locally(self):
        """UAMI should report as not available when running locally."""
        from app.core.uami_credential import UAMICredentialProvider

        provider = UAMICredentialProvider()
        assert not provider.is_available(), "UAMI should not be available locally"

    @pytest.mark.skipif(is_running_in_azure(), reason="Running in Azure")
    def test_credential_raises_when_uami_unavailable(self):
        """Should raise error when trying to get credential locally."""
        from app.core.uami_credential import (
            UAMICredentialError,
            UAMICredentialProvider,
        )

        provider = UAMICredentialProvider()

        with pytest.raises(UAMICredentialError):
            provider.get_credential_for_tenant(
                tenant_id="00000000-0000-0000-0000-000000000000",
                client_id="00000000-0000-0000-0000-000000000001",
            )


# ============================================================================
# Health Check Test
# ============================================================================


def test_uami_health_check():
    """Comprehensive health check for UAMI configuration."""
    from app.core.config import get_settings
    from app.core.uami_credential import get_uami_provider

    settings = get_settings()
    provider = get_uami_provider()

    health = {
        "use_uami_auth": settings.use_uami_auth,
        "uami_client_id_configured": bool(settings.uami_client_id),
        "uami_client_id_valid": False,
        "uami_available": provider.is_available(),
        "environment": provider.get_environment_info(),
    }

    # Validate UAMI client ID is UUID
    if settings.uami_client_id:
        try:
            import uuid

            uuid.UUID(str(settings.uami_client_id))
            health["uami_client_id_valid"] = True
        except ValueError:
            pass

    # In Azure, UAMI should be available
    if is_running_in_azure():
        assert health["uami_available"], "UAMI should be available in Azure"
        assert health["uami_client_id_configured"], "UAMI_CLIENT_ID should be configured"
        assert health["uami_client_id_valid"], "UAMI_CLIENT_ID should be valid UUID"

    return health
