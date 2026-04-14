---
status: proposed
date: 2025-07-11
decision-makers: Solutions Architect 🏛️, Security Auditor 🛡️
consulted: Pack Leader 🐺 (delivery tracking), Experience Architect 🎨 (UI persona interaction)
informed: All engineering, MSP tenant administrators
relates-to: ADR-0007 (Auth Evolution)
---

# ADR-0011: Granular RBAC with Permission Strings

## Context and Problem Statement

The Azure Governance Platform currently uses a flat `User.roles: list[str]` model where `"admin"` is the only meaningful elevated role. All authorization checks follow the pattern `"admin" in user.roles` — effectively binary (admin or not-admin). Meanwhile, the `UserTenant` model has ad-hoc boolean flags (`can_manage_resources`, `can_view_costs`, `can_manage_compliance`) that duplicate authorization logic in the data layer.

As we onboard 5 MSP tenants (HTT, BCC, FN, TLL, DCE) with different staff accessing different modules, we need roles between "god mode admin" and "default user." A customer's finance analyst should see cost data but not trigger sync jobs. A tenant admin should manage their tenant's compliance rules but not create new tenants.

How do we add granular, module-level authorization without breaking the existing auth stack?

## Decision Drivers

- **Backward compatibility (K.O.)**: Existing `"admin" in user.roles` checks must keep working with zero changes
- **Tenant isolation preserved**: Must layer on top of `TenantAuthorization`, not replace it
- **Minimal complexity**: 4 roles × 5 tenants — this is not an enterprise ABAC engine
- **Azure AD alignment**: Roles should map cleanly to Entra ID App Roles (JWT `roles` claim)
- **Testability**: Permission sets must be unit-testable without database or HTTP calls
- **Incremental migration**: Routes migrate one-at-a-time, not big-bang

## Considered Options

1. **Code-defined roles with `resource:action` permission strings** — Permission enum + frozen set mappings, custom FastAPI dependency
2. **PyCasbin policy engine** — Externalized RBAC/ABAC policies with Casbin DSL
3. **Database-driven role/permission tables** — Full DB schema for roles, permissions, and role-permission join table

## Decision Outcome

Chosen option: **"Code-defined roles with permission strings"**, because it's the only option that requires zero new dependencies, zero database migrations, and can be shipped incrementally alongside existing `require_roles()` checks. For 4 predefined roles serving 5 tenants, code-defined permission sets are simpler, safer, and more testable than a policy engine or database-driven system.

### Architecture: How It Layers

```
Request → Authentication (JWT/Azure AD) → unchanged
        → Tenant Isolation (TenantAuthorization) → unchanged  
        → Permission Check (NEW: require_permissions) → this ADR
        → Persona UI Gating (personas.py) → unchanged
```

The four authorization concerns remain orthogonal:

| Concern | Question Answered | Mechanism |
|---------|-------------------|-----------|
| **Authentication** | Who are you? | JWT token validation |
| **Tenant access** | Which tenants' data can you see? | `TenantAuthorization` + `UserTenant` |
| **Permissions** | What actions can you perform? | Role → permission set resolution (this ADR) |
| **Personas** | Which UI sections do you see? | Entra ID groups → `personas.yaml` |

### Predefined Roles

| Role | Slug | Description | Key Permissions |
|------|------|-------------|-----------------|
| **Admin** | `admin` | Full system access. Wildcard `*`. | Everything |
| **Tenant Admin** | `tenant_admin` | Manages a tenant's config, users, compliance, and data. Cannot create tenants or access system settings. | `costs:manage`, `compliance:manage`, `resources:manage`, `identity:manage`, `users:manage`, `sync:trigger` |
| **Analyst** | `analyst` | Read and export data across accessible modules. Cannot modify configuration. | `costs:read`, `costs:export`, `compliance:read`, `resources:read`, `resources:export`, `identity:read`, `identity:export` |
| **Viewer** | `viewer` | Read-only dashboard access. No exports, no writes. | `dashboard:read`, `costs:read`, `compliance:read`, `resources:read`, `identity:read` |

### Permission String Registry

Format: `resource:action` (OAuth2 scope convention).

```
dashboard:read
costs:read        costs:export       costs:manage
compliance:read   compliance:write   compliance:manage
resources:read    resources:export   resources:manage
identity:read     identity:export    identity:manage
audit_logs:read   audit_logs:export
sync:read         sync:trigger       sync:manage
tenants:read      tenants:manage
users:read        users:manage
system:health     system:admin
riverside:read    riverside:manage
dmarc:read        dmarc:manage
preflight:read    preflight:run
budgets:read      budgets:manage
recommendations:read
monitoring:read   monitoring:manage
```

### Role → Permission Mapping (Containment Hierarchy)

```
Viewer ⊂ Analyst ⊂ TenantAdmin ⊂ Admin (wildcard)
```

- **Viewer** gets all `*:read` permissions (no exports, no writes)
- **Analyst** gets Viewer + all `*:export` permissions
- **TenantAdmin** gets Analyst + all `*:manage`, `*:write`, `*:trigger`, `*:run` permissions (except `system:admin`, `tenants:manage`)
- **Admin** gets wildcard `*` (all permissions, including `system:admin` and `tenants:manage`)

### Legacy Role Mapping

Existing role strings continue to work through a mapping table:

| Legacy Role | Maps To | Rationale |
|-------------|---------|-----------|
| `"admin"` | `admin` | Unchanged — wildcard |
| `"operator"` | `tenant_admin` | Closest equivalent |
| `"reader"` | `viewer` | Closest equivalent |
| `"user"` | `viewer` | Default role |

### Key Implementation Components

**`app/core/permissions.py`** — Permission enum, Role enum, `ROLE_PERMISSIONS` frozen set mappings, `LEGACY_ROLE_MAP`, and resolution functions (`resolve_user_permissions`, `has_permission`).

**`app/core/rbac.py`** — FastAPI dependency `require_permissions(["costs:read"])` that resolves permissions from `user.roles` and checks against required permissions. Validates permission strings at import time (fail-fast on typos).

**`User.permissions` property** — Computed property on the existing `User` model that resolves the full permission set from `user.roles`. Cached per request instance.

### Route Migration Pattern

Routes migrate incrementally from `require_roles()` to `require_permissions()`:

```python
# Before (still works — backward compatible)
@router.get("/costs")
async def get_costs(user: User = Depends(require_roles(["admin", "operator"]))):
    ...

# After (granular)
@router.get("/costs")  
async def get_costs(user: User = Depends(require_permissions(["costs:read"]))):
    ...
```

Both patterns coexist during migration. `require_roles()` is never removed — it stays as a convenience wrapper.

### Azure AD App Roles Integration

Define 4 App Roles in the Entra ID App Registration manifest:

| Display Name | Value | Allowed Member Types |
|-------------|-------|---------------------|
| Admin | `admin` | Users/Groups |
| Tenant Admin | `tenant_admin` | Users/Groups |
| Analyst | `analyst` | Users/Groups |
| Viewer | `viewer` | Users/Groups |

The JWT `roles` claim from Entra ID maps directly to the `Role` enum — replacing the brittle keyword-matching in `_map_groups_to_roles()`. Group-based mapping remains as a fallback during transition.

### Migration Strategy

| Phase | Scope | Breaking Changes | Effort |
|-------|-------|-----------------|--------|
| **1: Foundation** | Create `permissions.py`, `rbac.py`, tests. Add `permissions` property to `User`. | None | 6 hours |
| **2: Route migration** | Replace `require_roles()` calls with `require_permissions()` one route file at a time. | None — both coexist | 8 hours |
| **3: Entra ID** | Define App Roles in manifest. Update `validate_token()` to prefer `roles` claim over group matching. | None — fallback preserved | 4 hours |
| **4: Cleanup** | Deprecate `UserTenant.can_*` boolean flags. Update `UserTenant.role` values to new role slugs. | DB migration (additive) | 4 hours |

### Consequences

**Good:**
- Least-privilege enforcement — viewers can't trigger syncs, analysts can't manage compliance
- Zero new dependencies — pure Python, standard FastAPI patterns
- Fully backward compatible — existing `"admin" in user.roles` checks unchanged
- Testable — permission sets are frozen sets, role containment hierarchy is assertable
- Azure AD native — App Roles map 1:1 to our Role enum

**Bad:**
- Role changes require code deployment (acceptable for 4 predefined roles)
- Two authorization patterns coexist during migration (`require_roles` + `require_permissions`)
- No per-tenant role customization in Phase 1 (e.g., user is Analyst in tenant A but Viewer in tenant B) — requires Phase 4

**Neutral:**
- Token size unchanged — roles stay in JWT, permissions resolved server-side
- Persona system unaffected — personas gate UI visibility, permissions gate actions

### Confirmation

- `tests/architecture/test_rbac_permissions.py` — validates permission string format, role hierarchy containment, legacy mapping
- `tests/unit/test_permissions.py` — unit tests for `has_permission`, `resolve_user_permissions`
- Manual: verify `require_roles(["admin"])` still works after Phase 1

## STRIDE Security Analysis

| Threat Category | Risk Level | Mitigation |
|-----------------|-----------|------------|
| **Spoofing** | Low | Permissions resolved server-side from authenticated `user.roles`. Cannot be forged — role claim is signed in JWT by Azure AD or internal key. |
| **Tampering** | Low | Permission sets are `frozenset` in code — immutable at runtime. No database-stored permissions to tamper with. Role-permission mappings are version-controlled. |
| **Repudiation** | Medium | `require_permissions()` logs denied attempts with user ID, required permission, and granted permissions. Recommend adding audit log entries for write/manage actions in Phase 2. |
| **Information Disclosure** | Low | 403 response includes required permission name (acceptable — it's not sensitive). Permission sets themselves are in source code, not exposed via API. |
| **Denial of Service** | Low | Permission resolution is a `set` lookup — O(1). No database queries, no external calls. No cache invalidation needed. |
| **Elevation of Privilege** | Medium | Wildcard `*` only assigned to `admin` role. Legacy role mapping is explicit (`LEGACY_ROLE_MAP`). Fail-closed: unknown roles get zero permissions. Risk: if `UserTenant.role` column contains unexpected values, they'll map to zero permissions (safe default). |

**Overall Security Posture:** Improves the platform from binary (admin/not-admin) to least-privilege authorization. The code-defined approach eliminates an entire class of misconfiguration risks (database-stored permissions being modified). The main residual risk is the transition period where some routes use `require_roles()` (coarse) while others use `require_permissions()` (granular).

## Pros and Cons of the Options

### Option 1: Code-Defined Roles with Permission Strings (Chosen)

- Good, because zero new dependencies — pure Python, standard FastAPI dependency injection
- Good, because fully backward compatible — `require_roles()` untouched
- Good, because testable — frozen sets are trivially assertable in unit tests
- Good, because permission strings validated at import time (fail-fast on typos)
- Good, because maps directly to Entra ID App Roles without translation layer
- Neutral, because role changes require code deployment (acceptable for 4 roles)
- Bad, because no runtime role customization without deployment
- Bad, because no per-tenant role overrides until Phase 4

### Option 2: PyCasbin Policy Engine

- Good, because supports complex policies (RBAC, ABAC, multi-tenancy) via declarative DSL
- Good, because well-maintained open source (Apache 2.0)
- Neutral, because supports policy hot-reload without deployment
- Bad, because massive overkill for 4 roles × 5 tenants — learning curve unjustified
- Bad, because adds dependency and operational complexity (policy files, adapters)
- Bad, because team unfamiliar with Casbin DSL — higher onboarding cost
- Bad, because doesn't integrate with Entra ID App Roles without custom adapter

### Option 3: Database-Driven Role/Permission Tables

- Good, because runtime-modifiable roles via admin UI
- Good, because supports per-tenant role customization natively
- Neutral, because familiar RDBMS pattern
- Bad, because requires DB migration and new tables (Role, Permission, RolePermission)
- Bad, because cache invalidation complexity — when does a role change take effect?
- Bad, because misconfiguration risk — wrong DB entry could grant unintended access
- Bad, because harder to test — needs database fixtures, not just frozen sets
- Bad, because overkill for 4 predefined roles that rarely change

## More Information

- **Research**: `research/rbac-fastapi/` — full analysis, source evaluation, implementation guide
- **Related ADR**: ADR-0007 (Auth Evolution) — covers authentication layer this builds on
- **Personas**: `app/core/personas.py` — separate UI-gating concern, unaffected by this ADR
- **Tenant auth**: `app/core/authorization.py` — `TenantAuthorization` class, unaffected by this ADR
- **Current roles code**: `app/core/auth.py` — `User.has_role()`, `require_roles()`, `_map_groups_to_roles()`

---

**Template Version:** MADR 4.0 (September 2024) with STRIDE Security Analysis  
**Last Updated:** 2025-07-11  
**Maintained By:** Solutions Architect 🏛️
