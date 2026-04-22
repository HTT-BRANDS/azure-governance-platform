"""GraphClient: composes the three mixins from this package.

Split from the monolithic graph_client.py (issue 6oj7, 2026-04-22). The
class is a pure composition so all public methods resolve via MRO:

    GraphClient -> _GraphClientCore -> _AdminRolesMixin -> _MFAMixin

Public API is preserved: external callers keep using
``from app.api.services.graph_client import GraphClient`` unchanged.
"""

from __future__ import annotations

from app.api.services.graph_client._admin_roles import _AdminRolesMixin
from app.api.services.graph_client._base import _GraphClientCore
from app.api.services.graph_client._mfa import _MFAMixin


class GraphClient(_GraphClientCore, _AdminRolesMixin, _MFAMixin):
    """Microsoft Graph API client.

    Composed from three cohesive mixins (see module docstring). _GraphClientCore
    provides __init__ and the HTTP/auth primitives; the other two mixins supply
    domain-specific methods that share self.tenant_id / self._request.
    """
