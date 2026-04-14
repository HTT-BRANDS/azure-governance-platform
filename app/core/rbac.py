"""RBAC FastAPI dependencies for granular permission checks.

Implements ADR-0011: ``require_permissions()`` and ``require_any_permission()``
dependencies that resolve permissions server-side from ``user.roles``.

Architecture layer::

    Request → Auth (JWT) → Tenant Isolation → **Permission Check** → Handler

Usage::

    from app.core.rbac import require_permissions, require_any_permission

    @router.get("/costs")
    async def get_costs(
        user: User = Depends(require_permissions("costs:read")),
    ):
        ...

    @router.get("/reports")
    async def get_report(
        user: User = Depends(
            require_any_permission("costs:read", "resources:read"),
        ),
    ):
        ...

Both patterns coexist with the existing ``require_roles()`` in ``auth.py``
during the incremental migration (ADR-0011 Phase 2).

See also:
    - ``app/core/permissions.py`` — permission constants and role definitions.
    - ``app/core/auth.py`` — ``require_roles()`` (still valid, backward compatible).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, status

from app.core.auth import User, get_current_user
from app.core.permissions import (
    ALL_PERMISSIONS,
    WILDCARD_PERMISSION,
    get_all_permissions,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Internal Helpers
# ============================================================================


def _validate_permission_strings(*permissions: str) -> None:
    """Validate permission strings at definition time (fail-fast on typos).

    Called immediately when ``require_permissions()`` /
    ``require_any_permission()`` is invoked — before the route is ever hit.
    This ensures misspelled permission strings are caught during import /
    application startup, not at runtime.

    Raises:
        ValueError: If any permission string is not in the registry.
    """
    for perm in permissions:
        if perm not in ALL_PERMISSIONS:
            raise ValueError(
                f"Unknown permission '{perm}'. Valid permissions: {sorted(ALL_PERMISSIONS)}"
            )


# ============================================================================
# Public FastAPI Dependencies
# ============================================================================


def require_permissions(
    *permissions: str,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """FastAPI dependency factory: require **ALL** specified permissions.

    Users with the ``admin`` role get wildcard access (all permissions
    granted).  Returns the authenticated ``User`` on success, raises
    ``403 Forbidden`` on denial.

    Permission strings are validated at call time (when the route is
    defined), not when the request arrives — so typos are caught early.

    Args:
        *permissions: Permission strings the user must **all** have.

    Returns:
        An async FastAPI dependency function.

    Raises:
        ValueError: If any permission string is invalid (caught at startup).

    Example::

        @router.post("/sync/trigger")
        async def trigger_sync(
            user: User = Depends(require_permissions("sync:trigger")),
        ):
            ...
    """
    _validate_permission_strings(*permissions)

    async def _check_permissions(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_perms = get_all_permissions(current_user.roles)

        # Wildcard — admin bypass
        if WILDCARD_PERMISSION in user_perms:
            return current_user

        # Check ALL required permissions
        missing = {p for p in permissions if p not in user_perms}
        if missing:
            logger.warning(
                "Permission denied: user=%s, required=%s, missing=%s, roles=%s",
                current_user.id,
                permissions,
                sorted(missing),
                current_user.roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return _check_permissions


def require_any_permission(
    *permissions: str,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """FastAPI dependency factory: require **ANY** of the specified permissions.

    Users with the ``admin`` role get wildcard access.  Returns the
    authenticated ``User`` on success, raises ``403 Forbidden`` on denial.

    Args:
        *permissions: Permission strings — user must have **at least one**.

    Returns:
        An async FastAPI dependency function.

    Raises:
        ValueError: If any permission string is invalid (caught at startup).

    Example::

        @router.get("/data")
        async def get_data(
            user: User = Depends(
                require_any_permission("costs:read", "resources:read"),
            ),
        ):
            ...
    """
    _validate_permission_strings(*permissions)

    async def _check_any_permission(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_perms = get_all_permissions(current_user.roles)

        # Wildcard — admin bypass
        if WILDCARD_PERMISSION in user_perms:
            return current_user

        # Check ANY required permission
        if not any(p in user_perms for p in permissions):
            logger.warning(
                "Permission denied (any): user=%s, required_any=%s, roles=%s",
                current_user.id,
                permissions,
                current_user.roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return _check_any_permission
