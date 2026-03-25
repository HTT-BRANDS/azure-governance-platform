# SESSION HANDOFF — Azure Governance Platform

**Last session:** code-puppy-0e02df — Version: **1.6.0** — OIDC Workload Identity Federation
**Status:** 🟢 ALL ENVIRONMENTS LIVE — v1.6.0 tagged, OIDC code complete, pending Azure-side activation

---

## Current State

```
2935 unit/integration tests passed, 0 failed
74 staging E2E tests passed, 31 skipped (auth-gated)
9 smoke tests: SKIPPED gracefully (no MI env — correct)
ruff check: All checks passed (0 errors)
Version: 1.6.0 (released, tagged v1.6.0)
Requirements: 57/57 implemented (100%)
```

---

## Environment Status

| Environment | URL | Version | Health | Routes |
|-------------|-----|---------|--------|--------|
| **Dev** | https://app-governance-dev-001.azurewebsites.net | 0.2.0 | ✅ | Legacy |
| **Staging** | https://app-governance-staging-xnczpwyv.azurewebsites.net | **1.5.7** | ✅ | 167 |
| **Production** | https://app-governance-prod.azurewebsites.net | **1.5.7** | ✅ | 167 |

> Staging/Prod are still running 1.5.7 image — v1.6.0 deploy is the next operator step
> once Azure-side OIDC setup is complete.

---

## What Was Done (OIDC Implementation — Full History)

### Wave 1: Core Implementation
| File | Change |
|------|--------|
| `app/core/oidc_credential.py` | NEW — `OIDCCredentialProvider`, 3-tier resolution, `get_oidc_provider()` singleton |
| `app/core/config.py` | `use_oidc_federation`, `azure_managed_identity_client_id`, `oidc_allow_dev_fallback` |
| `app/core/tenants_config.py` | `key_vault_secret_name` optional; `oidc_enabled=True`; `get_app_id_for_tenant()` |
| `app/models/tenant.py` | `use_oidc: bool` column |
| `app/api/services/azure_client.py` | OIDC path; composite `tenant_id:client_id` cache key; prefix `clear_cache()` |
| `app/api/services/graph_client.py` | OIDC routes through `azure_client_manager` singleton |
| `app/preflight/azure_checks.py` | OIDC bypass; `_sanitize_error()` fixed; `logger.exception` → structured `logger.error` |
| `alembic/versions/007_add_oidc_federation.py` | `use_oidc` column migration |
| `.env.example` | OIDC section + `OIDC_ALLOW_DEV_FALLBACK=true` |

### Wave 2: Scripts
| Script | Purpose |
|--------|---------|
| `scripts/setup-federated-creds.sh` | Configures federated creds on all 5 app registrations; UUID validation |
| `scripts/verify-federated-creds.sh` | Read-only verification |
| `scripts/seed_riverside_tenants.py` | Upserts 5 tenants with `use_oidc=True`, no secrets |

### Wave 3: Tests
| File | Tests |
|------|-------|
| `tests/unit/test_oidc_credential.py` | 41 tests (kill switch, 3 resolution paths, singleton, manager, graph, preflight, tenants_config) |
| `tests/smoke/test_oidc_connectivity.py` | 9 tests (skip gracefully without Azure env) |
| `tests/unit/test_config.py` | +6 OIDC config field tests |

### Wave 4: Security Audit Remediation
| Finding | Fix |
|---------|-----|
| HIGH-1: Silent DefaultAzureCredential fallback | `OIDC_ALLOW_DEV_FALLBACK` kill switch; `RuntimeError` if not set |
| HIGH-2: Dead `_sanitize_error()` + traceback leak | Return value used; `logger.exception` → `logger.error` |
| HIGH-3: GraphClient bypasses singleton | Now calls `azure_client_manager.get_credential()` |
| MEDIUM-1: Cache key only `tenant_id` | Composite `tenant_id:client_id`; prefix clear |
| MEDIUM-2: No UUID validation in setup script | `validate_uuid()` added; called for both args |

### Wave 5: Docs + Release
| File | Change |
|------|--------|
| `docs/OIDC_TENANT_AUTH.md` | Complete operational guide with kill-switch docs |
| `CHANGELOG.md` | `[1.6.0] - 2026-03-21` with Added/Changed/Security/Pending sections |
| `pyproject.toml` | `1.5.7` → `1.6.0` |
| `app/__init__.py` | `1.5.7` → `1.6.0` |

---

## Azure-Side Activation (Operator Steps — Code Complete)

| # | Step | Command | Status |
|---|------|---------|--------|
| 1 | Get MI Object ID | `az webapp identity show --name app-governance-prod --resource-group rg-governance-production --query principalId -o tsv` | ⏳ Run first |
| 2 | Configure federated creds (5 tenants) | `./scripts/setup-federated-creds.sh --managing-tenant-id 0c0e35dc-188a-4eb3-b8ba-61752154b407 --mi-object-id <MI_OBJECT_ID>` | ⏳ Admin required |
| 3 | Enable OIDC on App Service | `az webapp config appsettings set --name app-governance-prod --resource-group rg-governance-production --settings USE_OIDC_FEDERATION=true` | ⏳ Pending |
| 4 | Set MI client ID (user-assigned only) | `az webapp config appsettings set ... AZURE_MANAGED_IDENTITY_CLIENT_ID=<id>` | ⏳ If applicable |
| 5 | Apply DB migration | `uv run alembic upgrade head` | ⏳ Pending |
| 6 | Seed tenant records | `uv run python scripts/seed_riverside_tenants.py` | ⏳ Pending |
| 7 | Verify federated creds | `./scripts/verify-federated-creds.sh --managing-tenant-id 0c0e35dc-... --mi-object-id <id>` | ⏳ Pending |
| 8 | Deploy v1.6.0 image | Update App Service container tag to `v1.6.0` | ⏳ Pending |
| 9 | Run smoke tests | `uv run pytest tests/smoke/test_oidc_connectivity.py -v` | ⏳ Needs MI env |

---

## Other Open Items

| Item | Status | Blocker |
|------|--------|---------|
| Sui Generis full integration | Placeholder endpoints live | API credentials from MSP |
| DCE tenant billing | Skipped | No subscription/billing account |
| Dev environment update | At v0.2.0 | Low priority |

---

## Quick Resume Commands

```bash
cd /Users/tygranlund/dev/azure-governance-platform
git status && git log --oneline -5
uv run pytest -q --ignore=tests/e2e --ignore=tests/smoke --ignore=tests/staging --ignore=tests/load
uv run ruff check .

# Azure-side OIDC activation sequence:
MI_OBJECT_ID=$(az webapp identity show \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --query principalId -o tsv)

./scripts/setup-federated-creds.sh \
  --managing-tenant-id 0c0e35dc-188a-4eb3-b8ba-61752154b407 \
  --mi-object-id "$MI_OBJECT_ID"

az webapp config appsettings set \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --settings USE_OIDC_FEDERATION=true

uv run alembic upgrade head
uv run python scripts/seed_riverside_tenants.py

./scripts/verify-federated-creds.sh \
  --managing-tenant-id 0c0e35dc-188a-4eb3-b8ba-61752154b407 \
  --mi-object-id "$MI_OBJECT_ID"
```

**Plane Status: 🛬 LANDED — v1.6.0 released and tagged. Azure-side activation is the only remaining step.**
