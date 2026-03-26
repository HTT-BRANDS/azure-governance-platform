"""Riverside Tenant Configuration for DMARC/DKIM Insights.

Loads tenant configuration from ``config/tenants.yaml`` (gitignored) with
automatic fallback to ``config/tenants.yaml.example`` for CI/testing.

Security Notes (LOW-1 remediation):
- Real tenant IDs, app IDs, and admin emails live in a gitignored YAML file.
- The committed example file contains placeholder UUIDs only.
- Override the path via the ``TENANTS_CONFIG_PATH`` environment variable.
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root — two levels up from app/core/tenants_config.py
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Data classes (unchanged public API)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TenantConfig:
    """Configuration for a single Azure tenant.

    Attributes:
        tenant_id: Azure AD tenant ID (GUID)
        name: Human-readable tenant name
        code: Short tenant code (e.g., HTT, BCC)
        admin_email: Global admin email address
        app_id: Azure AD app registration client ID
        key_vault_secret_name: Name of client secret in Key Vault
        domains: List of custom domains managed in this tenant
        is_active: Whether this tenant is currently monitored
        is_riverside: Whether this is a Riverside-managed tenant
        priority: Tenant priority for sync operations (1=highest)
        oidc_enabled: Whether OIDC workload identity federation is active
    """

    tenant_id: str
    name: str
    code: str
    admin_email: str
    app_id: str
    key_vault_secret_name: str | None = None
    domains: list[str] = field(default_factory=list)
    is_active: bool = True
    is_riverside: bool = True
    priority: int = 5
    oidc_enabled: bool = True


@dataclass(frozen=True)
class GraphPermissions:
    """Required Microsoft Graph API permissions for DMARC/DKIM monitoring.

    These permissions follow the principle of least privilege.
    All are Application permissions requiring admin consent.
    """

    REPORTS_READ_ALL: str = "Reports.Read.All"
    SECURITY_EVENTS_READ_ALL: str = "SecurityEvents.Read.All"
    DOMAIN_READ_ALL: str = "Domain.Read.All"
    DIRECTORY_READ_ALL: str = "Directory.Read.All"

    @classmethod
    def all_permissions(cls) -> list[str]:
        """Return all required permissions as a list."""
        return [
            cls.REPORTS_READ_ALL,
            cls.SECURITY_EVENTS_READ_ALL,
            cls.DOMAIN_READ_ALL,
            cls.DIRECTORY_READ_ALL,
        ]

    @classmethod
    def permission_descriptions(cls) -> dict[str, str]:
        """Return human-readable descriptions of each permission."""
        return {
            cls.REPORTS_READ_ALL: "Read all usage reports including email security reports",
            cls.SECURITY_EVENTS_READ_ALL: "Read security events and alerts",
            cls.DOMAIN_READ_ALL: "Read all domain properties including verification status",
            cls.DIRECTORY_READ_ALL: "Read directory data (users, groups, applications)",
        }


# ---------------------------------------------------------------------------
# YAML config loader
# ---------------------------------------------------------------------------


def _find_config_path() -> Path:
    """Locate the tenant configuration YAML file.

    Search order:
        1. ``TENANTS_CONFIG_PATH`` environment variable (explicit override)
        2. ``config/tenants.yaml`` (gitignored, real values)
        3. ``config/tenants.yaml.example`` (committed, placeholder values)

    Returns:
        Resolved ``Path`` to the chosen file.

    Raises:
        FileNotFoundError: If none of the candidate paths exist.
    """
    env_path = os.environ.get("TENANTS_CONFIG_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
        logger.warning("TENANTS_CONFIG_PATH=%s does not exist — trying defaults", env_path)

    real = _PROJECT_ROOT / "config" / "tenants.yaml"
    if real.is_file():
        return real

    example = _PROJECT_ROOT / "config" / "tenants.yaml.example"
    if example.is_file():
        logger.info(
            "Using config/tenants.yaml.example (placeholder values). "
            "Copy to config/tenants.yaml with real IDs for production."
        )
        return example

    raise FileNotFoundError(
        "Tenant config not found. Expected config/tenants.yaml or set TENANTS_CONFIG_PATH. "
        "See config/tenants.yaml.example for the template."
    )


def _load_tenants(path: Path) -> dict[str, TenantConfig]:
    """Parse the YAML file at *path* into a dict of ``TenantConfig``."""
    with open(path) as fh:
        data = yaml.safe_load(fh)

    tenants: dict[str, TenantConfig] = {}
    for code, cfg in data["tenants"].items():
        code_upper = code.upper()
        tenants[code_upper] = TenantConfig(
            tenant_id=cfg["tenant_id"],
            name=cfg["name"],
            code=cfg.get("code", code_upper),
            admin_email=cfg["admin_email"],
            app_id=cfg["app_id"],
            key_vault_secret_name=cfg.get("key_vault_secret_name"),
            domains=cfg.get("domains", []),
            is_active=cfg.get("is_active", True),
            is_riverside=cfg.get("is_riverside", True),
            priority=cfg.get("priority", 5),
            oidc_enabled=cfg.get("oidc_enabled", True),
        )
    return tenants


def _load() -> dict[str, TenantConfig]:
    """Find and load the tenant configuration (cached at module level)."""
    path = _find_config_path()
    logger.debug("Loading tenant config from %s", path)
    return _load_tenants(path)


# ---------------------------------------------------------------------------
# Module-level singleton — loaded once on first import
# ---------------------------------------------------------------------------
RIVERSIDE_TENANTS: dict[str, TenantConfig] = _load()


# ---------------------------------------------------------------------------
# DMARC/DKIM monitoring configuration (unchanged)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DmarcDkimConfig:
    """Configuration for DMARC/DKIM monitoring across all tenants."""

    GRAPH_BASE_URL: str = "https://graph.microsoft.com/v1.0"
    EMAIL_AUTHENTICATION_REPORTS_ENDPOINT: str = "/reports/getEmailActivityUserDetail"
    SECURITY_ALERTS_ENDPOINT: str = "/security/alerts"
    DMARC_SYNC_INTERVAL_MINUTES: int = 60
    DKIM_SYNC_INTERVAL_MINUTES: int = 60
    DMARC_FAILURE_THRESHOLD_PERCENT: float = 5.0
    DKIM_FAILURE_THRESHOLD_PERCENT: float = 5.0
    DMARC_DATA_RETENTION_DAYS: int = 90

    @classmethod
    def get_graph_endpoints(cls) -> dict[str, str]:
        """Return all relevant Graph API endpoints for DMARC/DKIM."""
        base = cls.GRAPH_BASE_URL
        return {
            "email_activity": f"{base}{cls.EMAIL_AUTHENTICATION_REPORTS_ENDPOINT}",
            "security_alerts": f"{base}{cls.SECURITY_ALERTS_ENDPOINT}",
            "domains": f"{base}/domains",
            "organization": f"{base}/organization",
        }


# ---------------------------------------------------------------------------
# Key Vault configuration (unchanged)
# ---------------------------------------------------------------------------

KEY_VAULT_CONFIG = {
    "vault_url_env_var": "KEY_VAULT_URL",
    "secret_name_template": "{tenant_code.lower()}-client-secret",
    "use_certificate_auth": False,
    "certificate_env_var": "AZURE_CLIENT_CERTIFICATE_PATH",
}


# ---------------------------------------------------------------------------
# Helper functions (unchanged public API)
# ---------------------------------------------------------------------------


def get_active_tenants() -> dict[str, TenantConfig]:
    """Return only active tenant configurations."""
    return {code: config for code, config in RIVERSIDE_TENANTS.items() if config.is_active}


def get_tenant_by_id(tenant_id: str) -> TenantConfig | None:
    """Get tenant configuration by tenant ID."""
    for config in RIVERSIDE_TENANTS.values():
        if config.tenant_id == tenant_id:
            return config
    return None


def get_tenant_by_code(code: str) -> TenantConfig | None:
    """Get tenant configuration by short code (e.g., 'HTT')."""
    return RIVERSIDE_TENANTS.get(code.upper())


def get_all_tenant_ids() -> list[str]:
    """Return list of all tenant IDs."""
    return [config.tenant_id for config in RIVERSIDE_TENANTS.values()]


def get_all_active_tenant_ids() -> list[str]:
    """Return list of active tenant IDs."""
    return [config.tenant_id for config in RIVERSIDE_TENANTS.values() if config.is_active]


def get_key_vault_secret_name(tenant_code: str) -> str | None:
    """Return the Key Vault secret name for a tenant's client secret.

    Returns None when the tenant is configured for OIDC federation (no secret needed).

    Raises:
        ValueError: If the tenant code is not recognised.
    """
    config = get_tenant_by_code(tenant_code)
    if not config:
        raise ValueError(f"Unknown tenant code: {tenant_code}")
    if config.oidc_enabled:
        return None
    return config.key_vault_secret_name


def get_app_id_for_tenant(tenant_id: str) -> str | None:
    """Get the app registration client ID for a tenant by tenant ID.

    Args:
        tenant_id: The Azure AD tenant GUID.

    Returns:
        The app registration client ID, or None if the tenant is not found.
    """
    config = get_tenant_by_id(tenant_id)
    return config.app_id if config else None


def validate_tenant_config() -> list[str]:
    """Validate all tenant configurations and return list of issues."""
    issues: list[str] = []

    for code, config in RIVERSIDE_TENANTS.items():
        if config.tenant_id in ("TBD", "", None):
            issues.append(f"{code}: Tenant ID is not set")

        if config.app_id in ("TBD", "", None):
            issues.append(f"{code}: App ID is not set")

        if not config.oidc_enabled and config.key_vault_secret_name in ("TBD", "", None):
            issues.append(
                f"{code}: key_vault_secret_name is not set (required when oidc_enabled=False)"
            )

        try:
            if config.tenant_id not in ("TBD", "", None):
                uuid.UUID(config.tenant_id)
        except ValueError:
            issues.append(f"{code}: Tenant ID is not a valid UUID")

        try:
            if config.app_id not in ("TBD", "", None):
                uuid.UUID(config.app_id)
        except ValueError:
            issues.append(f"{code}: App ID is not a valid UUID")

        if "@" not in config.admin_email:
            issues.append(f"{code}: Admin email is invalid")

    return issues


# ---------------------------------------------------------------------------
# Default settings for new tenants (unchanged)
# ---------------------------------------------------------------------------

DEFAULT_TENANT_SETTINGS = {
    "graph_api_version": "v1.0",
    "sync_intervals": {
        "dmarc_dkim": 1,
        "security_alerts": 1,
        "domain_status": 24,
    },
    "monitoring": {
        "enable_dmarc_monitoring": True,
        "enable_dkim_monitoring": True,
        "enable_spf_monitoring": True,
        "alert_on_failure": True,
    },
    "retry": {
        "max_retries": 3,
        "backoff_factor": 2.0,
        "initial_delay_seconds": 1,
    },
}
