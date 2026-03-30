# Enable Client-Secret Fallback — Get Real Data Flowing NOW

**Created:** 2026-03-31
**Priority:** 🔴 P0 CRITICAL — Unblocks all real data flow
**Time Required:** 30-60 minutes
**Prerequisite:** Azure portal access + Global Admin in each tenant

---

## Why This Runbook Exists

The OIDC Workload Identity Federation approach (`USE_OIDC_FEDERATION=true`)
is **architecturally broken** for cross-tenant scenarios. Microsoft explicitly
prohibits using Entra ID-issued tokens (from Managed Identity) as assertions
in federated identity credential flows → error `AADSTS700236`.

**This will never work with the current per-tenant FIC pattern.**

The platform already has a fully working client-secret fallback path. This
runbook flips the switch to get real data flowing immediately.

---

## Step 0: Verify Current State

```bash
# Check production health
curl -s https://app-governance-prod.azurewebsites.net/health/detailed | python3 -m json.tool

# Verify the current OIDC setting
az webapp config appsettings list \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --query "[?name=='USE_OIDC_FEDERATION'].value" -o tsv
# Expected: "true" (the broken setting)
```

---

## Step 1: Ensure Client Secrets Exist

For each tenant, you need a valid client secret on the existing app registration.
Check `config/tenants.yaml` for the `app_id` values.

### Option A: Store Secrets in Key Vault (Recommended for Production)

```bash
KV_NAME="kv-gov-prod-001"  # Your production Key Vault name

# For each tenant — create a client secret and store it
# Replace placeholders with real values from config/tenants.yaml

# HTT
az ad app credential reset --id <HTT_APP_OBJECT_ID> --display-name "governance-platform" --years 2 --query password -o tsv
# Copy the output, then:
az keyvault secret set --vault-name $KV_NAME --name "htt-client-secret" --value "<SECRET_VALUE>"

# BCC
az ad app credential reset --id <BCC_APP_OBJECT_ID> --display-name "governance-platform" --years 2 --query password -o tsv
az keyvault secret set --vault-name $KV_NAME --name "bcc-client-secret" --value "<SECRET_VALUE>"

# FN
az ad app credential reset --id <FN_APP_OBJECT_ID> --display-name "governance-platform" --years 2 --query password -o tsv
az keyvault secret set --vault-name $KV_NAME --name "fn-client-secret" --value "<SECRET_VALUE>"

# TLL
az ad app credential reset --id <TLL_APP_OBJECT_ID> --display-name "governance-platform" --years 2 --query password -o tsv
az keyvault secret set --vault-name $KV_NAME --name "tll-client-secret" --value "<SECRET_VALUE>"

# DCE
az ad app credential reset --id <DCE_APP_OBJECT_ID> --display-name "governance-platform" --years 2 --query password -o tsv
az keyvault secret set --vault-name $KV_NAME --name "dce-client-secret" --value "<SECRET_VALUE>"
```

### Option B: Store Secrets as App Service Env Vars (Quick & Dirty)

```bash
# Set secrets directly as App Service config (less secure, but faster)
az webapp config appsettings set \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --settings \
    RIVERSIDE_HTT_CLIENT_SECRET="<secret>" \
    RIVERSIDE_BCC_CLIENT_SECRET="<secret>" \
    RIVERSIDE_FN_CLIENT_SECRET="<secret>" \
    RIVERSIDE_TLL_CLIENT_SECRET="<secret>" \
    RIVERSIDE_DCE_CLIENT_SECRET="<secret>"
```

> **How the env var resolution works:** The `AzureClientManager._fetch_key_vault_secret()`
> method checks for env vars matching the pattern `RIVERSIDE_{SECRET_NAME_UPPER}` before
> querying Key Vault. So `htt-client-secret` → `RIVERSIDE_HTT_CLIENT_SECRET`.

---

## Step 2: Ensure Tenant DB Records Have Credentials

Each tenant in the `tenants` DB table needs `client_id` and `client_secret_ref` set.
The `client_secret_ref` is the Key Vault secret name (e.g., `htt-client-secret`).

If you seeded tenants from `config/tenants.yaml`, the `client_id` (same as `app_id`)
should already be there. The `client_secret_ref` needs to match the KV secret name.

```sql
-- Check current state (run against Azure SQL)
SELECT id, name, tenant_id, client_id, client_secret_ref, use_lighthouse, use_oidc
FROM tenants;

-- Update each tenant with the secret reference
UPDATE tenants SET
  client_secret_ref = 'htt-client-secret',  -- pragma: allowlist secret
  use_oidc = 0
WHERE tenant_id = '<HTT_TENANT_GUID>';

UPDATE tenants SET
  client_secret_ref = 'bcc-client-secret',  -- pragma: allowlist secret
  use_oidc = 0
WHERE tenant_id = '<BCC_TENANT_GUID>';

-- Repeat for FN, TLL, DCE...
```

---

## Step 3: Flip the Switch

```bash
# Disable OIDC federation — enable secret-based auth
az webapp config appsettings set \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --settings USE_OIDC_FEDERATION=false
```

---

## Step 4: Restart and Verify

```bash
# Restart to reset circuit breakers and pick up new config
az webapp restart \
  --name app-governance-prod \
  --resource-group rg-governance-production

# Wait 2-3 minutes for startup, then verify
curl -s https://app-governance-prod.azurewebsites.net/health/detailed | python3 -m json.tool

# Check logs for successful credential resolution
az webapp log tail \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --filter "credential" 2>&1 | head -50
```

---

## Step 5: Trigger Data Sync

Either wait for the hourly scheduler, or trigger manually:

```bash
# Trigger manual sync via API (requires auth token)
# Or just wait for the next scheduled sync cycle

# After sync runs, verify data:
# 1. Check riverside_mfa table has rows
# 2. Check cost_snapshots table has rows
# 3. Check identity_snapshots table has rows
# 4. Check /riverside dashboard shows real metrics
```

---

## Step 6: Verify and Close Issues

Once data is flowing:

```bash
# In the project directory
bd close azure-governance-platform-oim   # Verify live data flow
bd close azure-governance-platform-70l   # AADSTS700236 — worked around
```

---

## How the Credential Flow Works (Reference)

```
USE_OIDC_FEDERATION=false
    │
    ▼
AzureClientManager.get_credential(tenant_id)
    │
    ▼
_resolve_credentials(tenant_id)
    │
    ├─ 1. DB tenant record: client_id + client_secret_ref
    │     └─ _fetch_key_vault_secret(client_secret_ref)
    │         ├─ Env var: RIVERSIDE_{CODE}_CLIENT_SECRET
    │         ├─ In-memory cache (5min TTL)
    │         └─ Azure Key Vault lookup
    │
    ├─ 2. tenant.use_lighthouse = True → settings.azure_* (ARM only)
    │
    ├─ 3. Key Vault: {tenant_id}-client-id + {tenant_id}-client-secret
    │
    └─ 4. Fallback: settings.azure_client_id + settings.azure_client_secret
    │
    ▼
ClientSecretCredential(tenant_id, client_id, client_secret)
    │
    ▼
Graph API / ARM API calls succeed ✅
```

---

## Rollback

If something goes wrong, revert to OIDC mode (which will fail gracefully):

```bash
az webapp config appsettings set \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --settings USE_OIDC_FEDERATION=true

az webapp restart \
  --name app-governance-prod \
  --resource-group rg-governance-production
```

---

## Next Steps

After this immediate fix, see `docs/AUTH_TRANSITION_ROADMAP.md` for the
long-term plan to move to a zero-secrets authentication pattern.
