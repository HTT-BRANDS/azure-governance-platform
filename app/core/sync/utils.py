"""Sync utility functions for data safety and audit trail.

Provides helpers to prevent column overflow errors that can poison
SQLAlchemy sessions and cascade to kill ALL sync jobs (ADR-0010).
"""

import logging
from collections.abc import Iterable

from app.core.config import get_settings
from app.core.tenants_config import get_app_id_for_tenant
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)
settings = get_settings()


def safe_truncate(
    value: str | None,
    max_len: int,
    field_name: str,
    context: dict | None = None,
) -> str | None:
    """Safely truncate a string value to fit a database column.

    Returns the value unchanged if it fits, or truncates with a structured
    warning log for audit trail (STRIDE T-1, R-1).

    Args:
        value: The string value to check/truncate.
        max_len: Maximum allowed length.
        field_name: Name of the field (for logging).
        context: Optional context dict (e.g. tenant, subscription).

    Returns:
        The original value, truncated value, or None.
    """
    if value is None:
        return None
    if len(value) <= max_len:
        return value

    logger.warning(
        "Truncating oversized field",
        extra={
            "field_name": field_name,
            "original_length": len(value),
            "max_length": max_len,
            "context": context or {},
        },
    )
    return value[:max_len]


def tenant_is_sync_eligible(tenant: Tenant) -> bool:
    """Return whether a tenant is configured for scheduled Azure sync.

    Eligibility is intentionally stricter than ``tenant.is_active`` so
    background jobs do not hammer Azure with obviously incomplete or fake
    tenant records.

    Rules:
    - inactive tenants are never eligible
    - secret mode without Key Vault keeps legacy Lighthouse behavior
    - OIDC/UAMI modes require a resolvable app/client ID
    - Key Vault secret mode requires one of:
      * ``use_lighthouse=True``
      * explicit ``client_id`` + ``client_secret_ref``

    A tenant merely existing in ``tenants_config`` is NOT sufficient in
    secret mode. Scheduled jobs must only run when the tenant has an actual
    credential path available; otherwise the scheduler will repeatedly invoke
    syncs that can never authenticate and will spam alerts/logs.
    """
    if not tenant.is_active:
        return False

    if settings.use_uami_auth or settings.use_oidc_federation:
        return bool(get_app_id_for_tenant(tenant.tenant_id) or tenant.client_id)

    if not settings.key_vault_url:
        return bool(settings.azure_client_id and settings.azure_client_secret)

    if tenant.use_lighthouse:
        return bool(settings.azure_client_id and settings.azure_client_secret)

    if tenant.client_id and tenant.client_secret_ref:
        return True

    return False


def get_sync_eligible_tenants(tenants: Iterable[Tenant]) -> list[Tenant]:
    """Filter a tenant iterable down to scheduled-sync eligible tenants."""
    return [tenant for tenant in tenants if tenant_is_sync_eligible(tenant)]
