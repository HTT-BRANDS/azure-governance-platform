"""Public API for the graph_client package.

This module re-exports every name that was previously importable from the
old monolithic app.api.services.graph_client module, so all 15+ existing
callers keep working without a code change::

    from app.api.services.graph_client import GraphClient       # still works
    from app.api.services.graph_client import ADMIN_ROLE_TEMPLATE_IDS  # still works
    from app.api.services.graph_client import UserMFAStatus     # still works

The internal structure (split into _base/_admin_roles/_mfa/_models/_constants)
is an implementation detail.
"""

from __future__ import annotations

from app.api.services.graph_client._client import GraphClient
from app.api.services.graph_client._constants import (
    ADMIN_ROLE_TEMPLATE_IDS,
    GRAPH_API_BASE,
    GRAPH_BETA_API_BASE,
    GRAPH_SCOPES,
)
from app.api.services.graph_client._models import (
    AdminRoleSummary,
    DirectoryRole,
    MFAError,
    MFAMethodDetails,
    PrivilegedAccessAssignment,
    RoleAssignment,
    TenantMFASummary,
    UserMFAStatus,
)

__all__ = [
    "ADMIN_ROLE_TEMPLATE_IDS",
    "AdminRoleSummary",
    "DirectoryRole",
    "GRAPH_API_BASE",
    "GRAPH_BETA_API_BASE",
    "GRAPH_SCOPES",
    "GraphClient",
    "MFAError",
    "MFAMethodDetails",
    "PrivilegedAccessAssignment",
    "RoleAssignment",
    "TenantMFASummary",
    "UserMFAStatus",
]
