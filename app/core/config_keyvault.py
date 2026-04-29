"""Azure Key Vault secret caching and health helpers."""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Azure Key Vault caching configuration
KEY_VAULT_CACHE_TTL_SECONDS = int(
    os.environ.get("KEY_VAULT_CACHE_TTL_SECONDS", "300")
)  # 5 min default
KEY_VAULT_REFRESH_BUFFER_SECONDS = int(
    os.environ.get("KEY_VAULT_REFRESH_BUFFER", "60")
)  # Refresh 1 min before expiry
KEY_VAULT_SOFT_DELETE_ENABLED = (
    os.environ.get("KEY_VAULT_SOFT_DELETE_ENABLED", "true").lower() == "true"
)


@dataclass
class KeyVaultSecretCache:
    """Cache entry for a Key Vault secret with TTL."""

    value: str
    fetched_at: float
    ttl_seconds: int
    secret_name: str
    version: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the cached secret has expired."""
        return time.time() > self.fetched_at + self.ttl_seconds

    @property
    def expires_in_seconds(self) -> float:
        """Seconds until cache entry expires."""
        expiry = self.fetched_at + self.ttl_seconds
        remaining = expiry - time.time()
        return max(0, remaining)

    @property
    def needs_refresh(self) -> bool:
        """Check if cache needs refresh (with buffer time)."""
        return self.expires_in_seconds < KEY_VAULT_REFRESH_BUFFER_SECONDS


@dataclass
class KeyVaultMetadata:
    """Azure Key Vault metadata and configuration status."""

    vault_url: str | None = None
    is_configured: bool = False
    soft_delete_enabled: bool = True
    purge_protection_enabled: bool = False
    last_access_time: float = field(default_factory=time.time)
    access_policy_count: int = 0
    secret_count: int = 0
    cached_secrets: list[str] = field(default_factory=list)
    failed_secrets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for diagnostics."""
        return {
            "vault_url": self.vault_url,
            "is_configured": self.is_configured,
            "soft_delete_enabled": self.soft_delete_enabled,
            "purge_protection_enabled": self.purge_protection_enabled,
            "last_access_time": self.last_access_time,
            "access_policy_count": self.access_policy_count,
            "secret_count": self.secret_count,
            "cached_secrets": self.cached_secrets,
            "failed_secrets": self.failed_secrets,
        }


class KeyVaultSecretManager:
    """Manages Azure Key Vault secrets with caching and auto-refresh.

    Features:
    - TTL-based secret caching to reduce API calls
    - Auto-refresh before expiry with configurable buffer
    - Soft-delete protection awareness
    - Thread-safe concurrent access
    - Detailed metadata tracking
    """

    def __init__(self):
        self._cache: dict[str, KeyVaultSecretCache] = {}
        self._lock = threading.RLock()
        self._metadata = KeyVaultMetadata()
        self._client: Any = None

    def _get_client(self, vault_url: str | None = None) -> Any:
        """Get or create Azure Key Vault client."""
        if self._client is None:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient

                credential = DefaultAzureCredential()
                url = vault_url or os.environ.get("KEY_VAULT_URL", "")

                if not url:
                    raise ValueError("Key Vault URL not configured")

                self._client = SecretClient(vault_url=url, credential=credential)
                self._metadata.vault_url = url
                self._metadata.is_configured = True

            except ImportError:
                logger.warning("Azure Key Vault SDK not available")
                raise

        return self._client

    def get_secret(
        self, secret_name: str, vault_url: str | None = None, force_refresh: bool = False
    ) -> str | None:
        """Get secret from cache or Key Vault with auto-refresh.

        Args:
            secret_name: Name of the secret to retrieve
            vault_url: Optional Key Vault URL (uses env var if not provided)
            force_refresh: Force refresh from Key Vault even if cached

        Returns:
            Secret value or None if not found/error
        """
        cache_key = f"{vault_url or 'default'}:{secret_name}"

        with self._lock:
            # Check cache first
            cached = self._cache.get(cache_key)

            if not force_refresh and cached and not cached.needs_refresh:
                logger.debug(f"Key Vault cache hit for {secret_name}")
                self._metadata.last_access_time = time.time()
                return cached.value

            # Need to fetch from Key Vault
            try:
                client = self._get_client(vault_url)
                secret = client.get_secret(secret_name)

                # Cache the secret
                self._cache[cache_key] = KeyVaultSecretCache(
                    value=secret.value,
                    fetched_at=time.time(),
                    ttl_seconds=KEY_VAULT_CACHE_TTL_SECONDS,
                    secret_name=secret_name,
                    version=secret.properties.version,
                )

                # Update metadata
                if secret_name not in self._metadata.cached_secrets:
                    self._metadata.cached_secrets.append(secret_name)
                if secret_name in self._metadata.failed_secrets:
                    self._metadata.failed_secrets.remove(secret_name)

                logger.debug(f"Key Vault secret fetched and cached: {secret_name}")
                return secret.value

            except Exception as e:
                logger.warning(f"Failed to fetch Key Vault secret {secret_name}: {e}")

                # Return stale cache if available (graceful degradation)
                if cached:
                    logger.info(f"Returning stale cached value for {secret_name}")
                    if secret_name not in self._metadata.failed_secrets:
                        self._metadata.failed_secrets.append(secret_name)
                    return cached.value

                if secret_name not in self._metadata.failed_secrets:
                    self._metadata.failed_secrets.append(secret_name)
                return None

    def get_secret_with_version(
        self, secret_name: str, version: str, vault_url: str | None = None
    ) -> str | None:
        """Get specific version of a secret."""
        try:
            client = self._get_client(vault_url)
            secret = client.get_secret(secret_name, version)
            return secret.value
        except Exception as e:
            logger.warning(f"Failed to fetch secret version {secret_name}/{version}: {e}")
            return None

    def invalidate_secret(self, secret_name: str, vault_url: str | None = None) -> bool:
        """Invalidate cached secret to force refresh on next access."""
        cache_key = f"{vault_url or 'default'}:{secret_name}"

        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                if secret_name in self._metadata.cached_secrets:
                    self._metadata.cached_secrets.remove(secret_name)
                logger.debug(f"Invalidated Key Vault cache for {secret_name}")
                return True
            return False

    def invalidate_all(self) -> int:
        """Clear all cached secrets."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._metadata.cached_secrets.clear()
            logger.info(f"Cleared all {count} Key Vault cached secrets")
            return count

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            time.time()
            active = sum(1 for c in self._cache.values() if not c.is_expired)
            expired = len(self._cache) - active

            return {
                "total_cached": len(self._cache),
                "active": active,
                "expired": expired,
                "cache_ttl_seconds": KEY_VAULT_CACHE_TTL_SECONDS,
                "refresh_buffer_seconds": KEY_VAULT_REFRESH_BUFFER_SECONDS,
            }

    def get_metadata(self) -> KeyVaultMetadata:
        """Get Key Vault metadata."""
        return self._metadata

    def verify_soft_delete(self, vault_url: str | None = None) -> bool:
        """Verify soft-delete is enabled on the Key Vault."""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.keyvault import KeyVaultManagementClient

            credential = DefaultAzureCredential()
            subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

            if not subscription_id:
                logger.warning("AZURE_SUBSCRIPTION_ID not set, cannot verify soft-delete")
                return True  # Assume enabled for safety

            kv_client = KeyVaultManagementClient(credential, subscription_id)

            # Extract vault name from URL
            url = vault_url or self._metadata.vault_url or os.environ.get("KEY_VAULT_URL", "")
            if not url:
                return True

            vault_name = url.split(".")[0].replace("https://", "")
            resource_group = os.environ.get("AZURE_RESOURCE_GROUP", "")

            if not resource_group:
                logger.warning("AZURE_RESOURCE_GROUP not set, cannot verify soft-delete")
                return True

            vault = kv_client.vaults.get(resource_group, vault_name)

            self._metadata.soft_delete_enabled = vault.properties.enable_soft_delete or False
            self._metadata.purge_protection_enabled = (
                vault.properties.enable_purge_protection or False
            )

            if not self._metadata.soft_delete_enabled and KEY_VAULT_SOFT_DELETE_ENABLED:
                logger.warning(
                    f"Key Vault {vault_name} does not have soft-delete enabled! "
                    "This is a security risk for secret recovery."
                )

            return self._metadata.soft_delete_enabled

        except Exception as e:
            logger.warning(f"Could not verify Key Vault soft-delete status: {e}")
            return True  # Assume enabled for safety


# Global Key Vault secret manager instance
key_vault_manager = KeyVaultSecretManager()
