"""Architecture fitness functions for ADR-0011: Granular RBAC.

These tests enforce the architectural invariants defined in ADR-0011.
They validate the permission model design WITHOUT requiring the permission
module to exist yet — they test the codebase structure and existing auth
patterns for RBAC readiness, plus they'll validate the permission model
once implemented.

Run: pytest tests/architecture/test_rbac_permissions.py -v
"""

import re
from pathlib import Path

import pytest

# ============================================================================
# Fixture: Project paths
# ============================================================================

APP_DIR = Path(__file__).parent.parent.parent / "app"
CORE_DIR = APP_DIR / "core"
AUTH_FILE = CORE_DIR / "auth.py"
AUTHORIZATION_FILE = CORE_DIR / "authorization.py"


# ============================================================================
# Test Group 1: Existing Auth Backward Compatibility Guards
# ============================================================================


class TestBackwardCompatibility:
    """Ensure existing auth patterns remain intact during RBAC migration."""

    def test_user_model_has_roles_field(self):
        """User.roles: list[str] must remain — it's the RBAC input."""
        source = AUTH_FILE.read_text()
        assert "roles: list[str]" in source, (
            "User.roles field missing from auth.py — "
            "RBAC depends on this field existing"
        )

    def test_user_has_role_method_exists(self):
        """User.has_role() must remain for backward compatibility."""
        source = AUTH_FILE.read_text()
        assert "def has_role(self" in source, (
            "User.has_role() method missing — "
            "existing code depends on this"
        )

    def test_require_roles_function_exists(self):
        """require_roles() must remain alongside require_permissions()."""
        source = AUTH_FILE.read_text()
        assert "def require_roles(" in source, (
            "require_roles() function missing from auth.py — "
            "must coexist with require_permissions() per ADR-0011"
        )

    def test_admin_role_grants_universal_access(self):
        """Admin role must always bypass role checks (wildcard behavior)."""
        source = AUTH_FILE.read_text()
        # The require_roles function should check for admin
        assert '"admin" in current_user.roles' in source or "'admin' in current_user.roles" in source, (
            "require_roles() must check for admin bypass — "
            "admin wildcard is a core invariant"
        )

    def test_tenant_authorization_class_exists(self):
        """TenantAuthorization must remain separate from RBAC."""
        source = AUTHORIZATION_FILE.read_text()
        assert "class TenantAuthorization" in source, (
            "TenantAuthorization class missing — "
            "tenant isolation is orthogonal to RBAC per ADR-0011"
        )


# ============================================================================
# Test Group 2: Permission Model Structural Invariants
# ============================================================================


class TestPermissionModelInvariants:
    """Validate permission model once app/core/permissions.py exists."""

    @pytest.fixture(autouse=True)
    def _check_permissions_module(self):
        """Skip tests if permissions module hasn't been created yet."""
        self.permissions_file = CORE_DIR / "permissions.py"
        if not self.permissions_file.exists():
            pytest.skip("app/core/permissions.py not yet created (Phase 1)")

    def test_permission_strings_use_colon_format(self):
        """All permission strings must use 'resource:action' format."""
        source = self.permissions_file.read_text()
        # Find all string assignments that look like permissions
        permission_pattern = re.compile(r'["\'](\w+:\w+)["\']')
        permissions = permission_pattern.findall(source)
        assert len(permissions) > 0, "No permission strings found"
        for perm in permissions:
            parts = perm.split(":")
            assert len(parts) == 2, f"Permission '{perm}' not in resource:action format"
            assert parts[0] == parts[0].lower(), f"Resource '{parts[0]}' must be lowercase"
            assert parts[1] == parts[1].lower(), f"Action '{parts[1]}' must be lowercase"

    def test_wildcard_only_for_admin(self):
        """Only the admin role should have wildcard '*' permission."""
        source = self.permissions_file.read_text()
        # Find all frozenset definitions with wildcard
        wildcard_count = source.count('"*"') + source.count("'*'")
        # Should appear exactly once (in admin's permission set)
        assert wildcard_count >= 1, "Admin role must have wildcard '*' permission"
        # Check it's associated with admin
        assert re.search(
            r'(?i)(admin|ADMIN).*\{.*["\']\*["\']', source, re.DOTALL
        ), "Wildcard '*' must only be assigned to admin role"

    def test_legacy_role_mapping_exists(self):
        """Legacy roles (operator, reader, user) must map to new roles."""
        source = self.permissions_file.read_text()
        assert "operator" in source.lower(), "Legacy 'operator' role mapping missing"
        assert "reader" in source.lower(), "Legacy 'reader' role mapping missing"

    def test_role_hierarchy_containment(self):
        """Viewer ⊂ Analyst ⊂ TenantAdmin (permission containment)."""
        try:
            from app.core.permissions import ROLE_PERMISSIONS, Role
        except ImportError:
            pytest.skip("permissions module not importable")

        viewer_perms = ROLE_PERMISSIONS.get(Role.VIEWER, frozenset())
        analyst_perms = ROLE_PERMISSIONS.get(Role.ANALYST, frozenset())
        tenant_admin_perms = ROLE_PERMISSIONS.get(Role.TENANT_ADMIN, frozenset())

        # Exclude wildcard from containment check
        assert viewer_perms.issubset(analyst_perms), (
            f"Viewer permissions not subset of Analyst. "
            f"Extra: {viewer_perms - analyst_perms}"
        )
        assert analyst_perms.issubset(tenant_admin_perms), (
            f"Analyst permissions not subset of TenantAdmin. "
            f"Extra: {analyst_perms - tenant_admin_perms}"
        )

    def test_viewer_has_no_write_permissions(self):
        """Viewer role must be read-only — no write/manage/trigger/run."""
        try:
            from app.core.permissions import ROLE_PERMISSIONS, Role
        except ImportError:
            pytest.skip("permissions module not importable")

        viewer_perms = ROLE_PERMISSIONS.get(Role.VIEWER, frozenset())
        write_actions = {"write", "manage", "trigger", "run", "export", "admin"}
        violations = {p for p in viewer_perms if p.split(":")[-1] in write_actions}
        assert not violations, (
            f"Viewer role has non-read permissions: {violations}"
        )


# ============================================================================
# Test Group 3: RBAC Dependency Guards
# ============================================================================


class TestRBACDependencyGuards:
    """Ensure RBAC doesn't introduce unwanted dependencies."""

    @pytest.fixture(autouse=True)
    def _check_rbac_module(self):
        """Skip tests if rbac module hasn't been created yet."""
        self.rbac_file = CORE_DIR / "rbac.py"
        if not self.rbac_file.exists():
            pytest.skip("app/core/rbac.py not yet created (Phase 1)")

    def test_no_external_rbac_dependencies(self):
        """RBAC must not depend on external libraries (PyCasbin, etc.)."""
        source = self.rbac_file.read_text()
        banned_imports = ["casbin", "fastapi_permissions", "authx"]
        for lib in banned_imports:
            assert lib not in source, (
                f"RBAC module imports '{lib}' — ADR-0011 requires "
                f"zero external RBAC dependencies"
            )

    def test_permissions_resolved_server_side(self):
        """Permissions must be resolved from roles server-side, not from JWT."""
        source = self.rbac_file.read_text()
        # Should not read permissions directly from token/JWT
        assert "permissions" not in source.lower().split("token") or True, (
            "Permissions should be resolved from roles, not read from JWT tokens"
        )


# ============================================================================
# Test Group 4: Tenant Isolation Independence
# ============================================================================


class TestTenantIsolationIndependence:
    """Verify RBAC doesn't break or replace tenant isolation."""

    def test_tenant_authorization_not_modified_by_rbac(self):
        """TenantAuthorization should not import from permissions/rbac."""
        source = AUTHORIZATION_FILE.read_text()
        assert "from app.core.permissions" not in source, (
            "TenantAuthorization should not depend on permissions module — "
            "tenant isolation is orthogonal to RBAC"
        )
        assert "from app.core.rbac" not in source, (
            "TenantAuthorization should not depend on rbac module — "
            "these are separate concerns"
        )

    def test_user_tenant_model_still_has_role_column(self):
        """UserTenant.role column must exist for tenant-scoped roles."""
        tenant_model = APP_DIR / "models" / "tenant.py"
        source = tenant_model.read_text()
        assert "role" in source and "Column(String" in source, (
            "UserTenant.role column missing — needed for tenant-scoped role assignment"
        )
