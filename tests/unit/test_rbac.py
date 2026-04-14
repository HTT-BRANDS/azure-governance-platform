"""Tests for app.core.rbac module.

Validates FastAPI permission dependencies: ``require_permissions()``
and ``require_any_permission()``.

Run: ``pytest tests/unit/test_rbac.py -v``
"""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import User, get_current_user
from app.core.rbac import require_any_permission, require_permissions

# ============================================================================
# Test Helpers
# ============================================================================


def _create_test_app() -> FastAPI:
    """Create a minimal FastAPI app with permission-protected routes."""
    app = FastAPI()

    @app.get("/costs")
    async def get_costs(
        user: User = Depends(require_permissions("costs:read")),
    ) -> dict[str, str]:
        return {"status": "ok", "user": user.id}

    @app.post("/costs")
    async def update_costs(
        user: User = Depends(require_permissions("costs:manage")),
    ) -> dict[str, str]:
        return {"status": "ok", "user": user.id}

    @app.get("/multi")
    async def multi_perms(
        user: User = Depends(
            require_permissions("costs:read", "resources:read"),
        ),
    ) -> dict[str, str]:
        return {"status": "ok", "user": user.id}

    @app.get("/any-data")
    async def any_data(
        user: User = Depends(
            require_any_permission("costs:read", "resources:read"),
        ),
    ) -> dict[str, str]:
        return {"status": "ok", "user": user.id}

    @app.get("/sync-trigger")
    async def trigger_sync(
        user: User = Depends(require_permissions("sync:trigger")),
    ) -> dict[str, str]:
        return {"status": "ok", "user": user.id}

    @app.get("/system-admin")
    async def system_admin(
        user: User = Depends(require_permissions("system:admin")),
    ) -> dict[str, str]:
        return {"status": "ok", "user": user.id}

    return app


def _make_user(
    roles: list[str],
    user_id: str = "test-user",
) -> User:
    """Create a test ``User`` with the specified roles."""
    return User(
        id=user_id,
        email="test@example.com",
        name="Test User",
        roles=roles,
        tenant_ids=["test-tenant"],
        is_active=True,
        auth_provider="internal",
    )


def _get_client(app: FastAPI, user: User) -> TestClient:
    """Create a ``TestClient`` with ``get_current_user`` overridden."""
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


# ============================================================================
# Admin — Wildcard Access
# ============================================================================


class TestAdminWildcard:
    """Admin users bypass ALL permission checks via wildcard."""

    def setup_method(self) -> None:
        self.app = _create_test_app()
        self.user = _make_user(["admin"])
        self.client = _get_client(self.app, self.user)

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_can_read_costs(self) -> None:
        assert self.client.get("/costs").status_code == 200

    def test_can_manage_costs(self) -> None:
        assert self.client.post("/costs").status_code == 200

    def test_can_access_multi_perms(self) -> None:
        assert self.client.get("/multi").status_code == 200

    def test_can_trigger_sync(self) -> None:
        assert self.client.get("/sync-trigger").status_code == 200

    def test_can_access_system_admin(self) -> None:
        assert self.client.get("/system-admin").status_code == 200

    def test_can_access_any_data(self) -> None:
        assert self.client.get("/any-data").status_code == 200


# ============================================================================
# Viewer — Read-Only
# ============================================================================


class TestViewerAccess:
    """Viewer: read-only — denied on write/manage/trigger endpoints."""

    def setup_method(self) -> None:
        self.app = _create_test_app()
        self.user = _make_user(["viewer"])
        self.client = _get_client(self.app, self.user)

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_can_read_costs(self) -> None:
        assert self.client.get("/costs").status_code == 200

    def test_cannot_manage_costs(self) -> None:
        assert self.client.post("/costs").status_code == 403

    def test_cannot_trigger_sync(self) -> None:
        assert self.client.get("/sync-trigger").status_code == 403

    def test_cannot_access_system_admin(self) -> None:
        assert self.client.get("/system-admin").status_code == 403

    def test_can_access_any_with_read(self) -> None:
        """Viewer has costs:read, which satisfies require_any_permission."""
        assert self.client.get("/any-data").status_code == 200

    def test_can_access_multi_read(self) -> None:
        """Viewer has both costs:read and resources:read."""
        assert self.client.get("/multi").status_code == 200


# ============================================================================
# Analyst — Read + Export, No Write
# ============================================================================


class TestAnalystAccess:
    """Analyst: read + export — denied on manage/trigger endpoints."""

    def setup_method(self) -> None:
        self.app = _create_test_app()
        self.user = _make_user(["analyst"])
        self.client = _get_client(self.app, self.user)

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_can_read_costs(self) -> None:
        assert self.client.get("/costs").status_code == 200

    def test_cannot_manage_costs(self) -> None:
        assert self.client.post("/costs").status_code == 403

    def test_cannot_trigger_sync(self) -> None:
        assert self.client.get("/sync-trigger").status_code == 403

    def test_cannot_access_system_admin(self) -> None:
        assert self.client.get("/system-admin").status_code == 403


# ============================================================================
# Tenant Admin — Full Module Access (minus system:admin)
# ============================================================================


class TestTenantAdminAccess:
    """TenantAdmin: full module access except system:admin and tenants:manage."""

    def setup_method(self) -> None:
        self.app = _create_test_app()
        self.user = _make_user(["tenant_admin"])
        self.client = _get_client(self.app, self.user)

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_can_read_costs(self) -> None:
        assert self.client.get("/costs").status_code == 200

    def test_can_manage_costs(self) -> None:
        assert self.client.post("/costs").status_code == 200

    def test_can_trigger_sync(self) -> None:
        assert self.client.get("/sync-trigger").status_code == 200

    def test_cannot_access_system_admin(self) -> None:
        assert self.client.get("/system-admin").status_code == 403


# ============================================================================
# Multiple Roles — Accumulated Permissions
# ============================================================================


class TestMultipleRoles:
    """Users with multiple roles accumulate all permissions."""

    def setup_method(self) -> None:
        self.app = _create_test_app()

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_viewer_plus_analyst_accumulates(self) -> None:
        user = _make_user(["viewer", "analyst"])
        client = _get_client(self.app, user)
        # Both roles have costs:read
        assert client.get("/costs").status_code == 200
        # Neither has costs:manage
        assert client.post("/costs").status_code == 403

    def test_viewer_plus_tenant_admin_gets_manage(self) -> None:
        user = _make_user(["viewer", "tenant_admin"])
        client = _get_client(self.app, user)
        assert client.get("/costs").status_code == 200
        assert client.post("/costs").status_code == 200
        assert client.get("/sync-trigger").status_code == 200


# ============================================================================
# Unknown / Empty Roles — Fail-Closed
# ============================================================================


class TestFailClosed:
    """Unknown roles and empty role lists get zero permissions."""

    def setup_method(self) -> None:
        self.app = _create_test_app()

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_unknown_role_denied(self) -> None:
        user = _make_user(["unknown_role"])
        client = _get_client(self.app, user)
        assert client.get("/costs").status_code == 403

    def test_empty_roles_denied(self) -> None:
        user = _make_user([])
        client = _get_client(self.app, user)
        assert client.get("/costs").status_code == 403

    def test_multiple_unknown_roles_denied(self) -> None:
        user = _make_user(["ghost", "phantom", "specter"])
        client = _get_client(self.app, user)
        assert client.get("/costs").status_code == 403


# ============================================================================
# Legacy Role Strings — Backward Compatibility
# ============================================================================


class TestLegacyRoles:
    """Legacy role strings (operator, reader, user) work via LEGACY_ROLE_MAP."""

    def setup_method(self) -> None:
        self.app = _create_test_app()

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_operator_maps_to_tenant_admin(self) -> None:
        user = _make_user(["operator"])
        client = _get_client(self.app, user)
        assert client.get("/costs").status_code == 200
        assert client.post("/costs").status_code == 200
        assert client.get("/sync-trigger").status_code == 200
        assert client.get("/system-admin").status_code == 403

    def test_reader_maps_to_viewer(self) -> None:
        user = _make_user(["reader"])
        client = _get_client(self.app, user)
        assert client.get("/costs").status_code == 200
        assert client.post("/costs").status_code == 403

    def test_user_maps_to_viewer(self) -> None:
        user = _make_user(["user"])
        client = _get_client(self.app, user)
        assert client.get("/costs").status_code == 200
        assert client.post("/costs").status_code == 403


# ============================================================================
# require_any_permission — OR Logic
# ============================================================================


class TestRequireAnyPermission:
    """require_any_permission: user needs at least one of the listed perms."""

    def setup_method(self) -> None:
        self.app = _create_test_app()

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_viewer_passes_with_read(self) -> None:
        user = _make_user(["viewer"])
        client = _get_client(self.app, user)
        assert client.get("/any-data").status_code == 200

    def test_unknown_role_fails(self) -> None:
        user = _make_user(["unknown"])
        client = _get_client(self.app, user)
        assert client.get("/any-data").status_code == 403

    def test_admin_passes(self) -> None:
        user = _make_user(["admin"])
        client = _get_client(self.app, user)
        assert client.get("/any-data").status_code == 200


# ============================================================================
# require_permissions with Multiple Perms — AND Logic
# ============================================================================


class TestRequireAllPermissions:
    """require_permissions with multiple args requires ALL permissions."""

    def setup_method(self) -> None:
        self.app = _create_test_app()

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_viewer_has_both_reads(self) -> None:
        user = _make_user(["viewer"])
        client = _get_client(self.app, user)
        # Viewer has both costs:read and resources:read
        assert client.get("/multi").status_code == 200

    def test_admin_passes_multi(self) -> None:
        user = _make_user(["admin"])
        client = _get_client(self.app, user)
        assert client.get("/multi").status_code == 200


# ============================================================================
# Permission String Validation — Fail-Fast on Typos
# ============================================================================


class TestPermissionValidation:
    """Invalid permission strings raise ValueError at definition time."""

    def test_invalid_permission_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown permission"):
            require_permissions("nonexistent:permission")

    def test_invalid_permission_in_any_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown permission"):
            require_any_permission("nonexistent:permission")

    def test_valid_permissions_do_not_raise(self) -> None:
        # Should NOT raise — these are valid permission strings
        dep = require_permissions("costs:read")
        assert callable(dep)

    def test_valid_any_permissions_do_not_raise(self) -> None:
        dep = require_any_permission("costs:read", "resources:read")
        assert callable(dep)


# ============================================================================
# 403 Error Response Details
# ============================================================================


class TestErrorDetails:
    """403 responses include helpful error messages."""

    def setup_method(self) -> None:
        self.app = _create_test_app()

    def teardown_method(self) -> None:
        self.app.dependency_overrides.clear()

    def test_missing_permission_returns_generic_detail(self) -> None:
        """F-06: 403 detail must NOT leak permission names."""
        user = _make_user(["viewer"])
        client = _get_client(self.app, user)
        resp = client.post("/costs")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Insufficient permissions"

    def test_any_permission_returns_generic_detail(self) -> None:
        """F-06: 403 detail must NOT leak permission names."""
        user = _make_user(["unknown"])
        client = _get_client(self.app, user)
        resp = client.get("/any-data")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Insufficient permissions"

    def test_response_returns_user_on_success(self) -> None:
        user = _make_user(["admin"], user_id="admin-42")
        client = _get_client(self.app, user)
        resp = client.get("/costs")
        assert resp.status_code == 200
        assert resp.json()["user"] == "admin-42"
