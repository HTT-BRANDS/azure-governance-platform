# Phase C: Zero-Secrets Authentication Setup

**Status:** Implementation Ready  
**Complexity:** Medium-High  
**Estimated Time:** 3-4 hours  
**Risk Level:** Low-Medium (backward compatible with Phase B)

---

## Overview

Phase C transitions from **client secrets** to **zero-secrets authentication** using User-Assigned Managed Identity (UAMI) with Federated Identity Credentials. This eliminates all client secrets from the system, achieving the ultimate goal of the authentication roadmap.

### Before (Phase B)
```
Multi-tenant App + Client Secret
  ↓ (client secret)
ClientSecretCredential
  ↓ (access token)
Microsoft Graph API
```

### After (Phase C)
```
UAMI (User-Assigned Managed Identity)
  ↓ (federated token from Azure IMDS)
Federated Identity Credential on Multi-Tenant App
  ↓ (token exchange)
ClientAssertionCredential
  ↓ (access token)
Microsoft Graph API
```

---

## Why Phase C?

| Concern | Phase B | Phase C |
|---------|---------|---------|
| Secrets in Key Vault | ✅ 1 secret | ✅ 0 secrets |
| Secrets in App Settings | ⚠️ Reference | ✅ None |
| Secret rotation needed | ⚠️ Every 2 years | ✅ Never |
| GitHub Actions secrets | ⚠️ Required | ✅ OIDC only |
| Blast radius if leaked | ⚠️ All tenants | ✅ N/A (no secrets) |
| Security posture | Good | Excellent |

---

## Prerequisites

- [ ] Azure CLI installed (`az --version`)
- [ ] Owner or Global Admin access to HTT (home) tenant
- [ ] Existing multi-tenant app registration from Phase B
- [ ] Key Vault access for role assignments
- [ ] GitHub repository admin access (for OIDC setup)
- [ ] App Service write access (to add UAMI)

---

## Architecture

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| UAMI | Provides identity without secrets | HTT tenant, `rg-governance-production` |
| Federated Identity Credential | Links UAMI to multi-tenant app | On the multi-tenant app registration |
| Key Vault RBAC | Allows UAMI to read existing configs | Governance Key Vault |
| App Service Identity | Assigns UAMI to the app | App Service → Identity |

### Authentication Flow

1. **App Service / GitHub Actions** requests token from UAMI
2. **UAMI** provides OIDC assertion token via IMDS endpoint
3. **Azure AD** validates the assertion against Federated Identity Credential
4. **ClientAssertionCredential** exchanges for Graph API access token
5. **Application** uses token to call Microsoft Graph API

---

## Step-by-Step Setup

### Step 1: Create User-Assigned Managed Identity

Run the automated setup script:

```bash
# Make script executable and run it
chmod +x scripts/setup-uami-phase-c.sh
./scripts/setup-uami-phase-c.sh
```

Or manually via Azure Portal:

1. Navigate to **Managed Identities** → **Create**
2. Resource group: `rg-governance-production`
3. Region: `Australia East` (or your region)
4. Name: `mi-governance-platform`
5. Click **Review + Create** → **Create**

Save the **Client ID** and **Principal ID** — you'll need them later.

### Step 2: Create Federated Identity Credential

The Federated Identity Credential links the UAMI to the multi-tenant app registration.

#### For GitHub Actions:

```bash
# Get app object ID (not app ID)
APP_ID="<multi-tenant-app-id>"
APP_OBJECT_ID=$(az ad app show --id "$APP_ID" --query "id" -o tsv)

# Create FIC
az ad app federated-credential create \
    --id "$APP_OBJECT_ID" \
    --parameters '{
        "name": "github-actions-federation",
        "issuer": "https://token.actions.githubusercontent.com",
        "subject": "repo:riverside/governance-platform:ref:refs/heads/main",
        "description": "GitHub Actions OIDC federation",
        "audiences": ["api://AzureADTokenExchange"]
    }'
```

#### For Azure App Service:

App Service uses a different federation model - the UAMI is directly assigned to the App Service. No explicit FIC needed on the app registration for App Service scenarios.

### Step 3: Assign Key Vault Roles to UAMI

```bash
# Variables
UAMI_PRINCIPAL_ID="<uami-principal-id>"
KEY_VAULT_NAME="kv-gov-prod-001"
RESOURCE_GROUP="rg-governance-production"

# Get Key Vault resource ID
KEY_VAULT_ID=$(az keyvault show --name "$KEY_VAULT_NAME" --query "id" -o tsv)

# Assign Key Vault Secrets User role
az role assignment create \
    --assignee-object-id "$UAMI_PRINCIPAL_ID" \
    --assignee-principal-type ServicePrincipal \
    --role "Key Vault Secrets User" \
    --scope "$KEY_VAULT_ID"

# Assign Key Vault Reader role
az role assignment create \
    --assignee-object-id "$UAMI_PRINCIPAL_ID" \
    --assignee-principal-type ServicePrincipal \
    --role "Key Vault Reader" \
    --scope "$KEY_VAULT_ID"
```

### Step 4: Configure GitHub Actions OIDC

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:

| Secret Name | Value |
|-------------|-------|
| `AZURE_CLIENT_ID` | UAMI Client ID |
| `AZURE_TENANT_ID` | HTT Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID |

**Note:** Do NOT add `AZURE_CLIENT_SECRET` — it's not needed with OIDC!

3. Update your GitHub Actions workflow:

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    permissions:
      id-token: write  # Required for OIDC
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      # Continue with deployment...
```

### Step 5: Update Application Configuration

#### Option A: Environment Variables

```bash
# Add to .env or App Service Configuration
UAMI_CLIENT_ID="<uami-client-id>"
UAMI_PRINCIPAL_ID="<uami-principal-id>"
FEDERATED_IDENTITY_CREDENTIAL_ID="github-actions-federation"
USE_UAMI_AUTH="true"

# Keep Phase B settings for rollback
AZURE_MULTI_TENANT_APP_ID="<app-id>"
# AZURE_MULTI_TENANT_CLIENT_SECRET="..."  # No longer needed!
```

#### Option B: Run Migration Script

```bash
# Automated migration from Phase B to C
./scripts/migrate-to-phase-c.sh \
    --uami-client-id "<uami-client-id>" \
    --uami-principal-id "<uami-principal-id>"
```

### Step 6: Assign UAMI to App Service

1. Navigate to **App Service** → **Identity**
2. Click **User assigned** tab
3. Click **Add**
4. Select the UAMI: `mi-governance-platform`
5. Click **Add**

Verify the assignment:

```bash
az webapp identity show \
    --name app-gov-prod-001 \
    --resource-group rg-governance-production \
    --query "userAssignedIdentities"
```

### Step 7: Deploy and Verify

```bash
# Deploy to staging first
./scripts/gh-deploy-dev.sh

# Or for production
./scripts/deploy.sh production
```

---

## Testing Procedure

### Automated Tests

```bash
# Run UAMI credential tests
python -m pytest tests/unit/test_uami_credential.py -v

# Expected output:
# test_uami_provider_singleton ... PASSED
# test_environment_detection ... PASSED
# test_credential_creation ... PASSED
# test_token_caching ... PASSED

# Run connectivity tests
python -m pytest tests/smoke/test_uami_connectivity.py -v
```

### Manual Verification

```bash
# 1. Verify UAMI exists and is accessible
az identity show \
    --name mi-governance-platform \
    --resource-group rg-governance-production

# 2. Verify FIC is attached to multi-tenant app
APP_OBJECT_ID=$(az ad app show --id <app-id> --query "id" -o tsv)
az ad app federated-credential list --id "$APP_OBJECT_ID"

# 3. Test authentication from App Service
# (SSH into App Service or use Kudu console)
python << 'EOF'
import os
os.environ['USE_UAMI_AUTH'] = 'true'

from app.core.uami_credential import get_uami_provider
from app.core.config import get_settings

provider = get_uami_provider()
settings = get_settings()

print(f"UAMI Available: {provider.is_available()}")
print(f"Environment: {provider.get_environment_info()}")
print(f"USE_UAMI_AUTH: {settings.use_uami_auth}")
EOF
```

### Log Verification

Check Application Insights for successful UAMI authentication:

```kusto
traces
| where message contains "UAMI" or message contains "ClientAssertionCredential"
| where timestamp > ago(1h)
| project timestamp, message, severityLevel
```

---

## Rollback Plan

If issues occur, rollback to Phase B is immediate:

### Option 1: Configuration Rollback (Fastest - 2 minutes)

```bash
# Run rollback script
./scripts/migrate-to-phase-c.sh --rollback

# Or manually edit .env
USE_UAMI_AUTH="false"
```

### Option 2: App Service Configuration

```bash
# Disable UAMI in App Service configuration
az webapp config appsettings set \
    --name app-gov-prod-001 \
    --resource-group rg-governance-production \
    --settings USE_UAMI_AUTH=false
```

### Verification After Rollback

```bash
# Ensure Phase B secret is still in Key Vault
az keyvault secret show \
    --vault-name kv-gov-prod-001 \
    --name multi-tenant-client-secret

# Test connectivity
python scripts/smoke_test.py
```

---

## Post-Migration: Cleanup (After 2-Week Soak Period)

Once Phase C is stable for 2+ weeks:

### Remove Client Secret from Key Vault

```bash
# The multi-tenant client secret is no longer needed
az keyvault secret delete \
    --vault-name kv-gov-prod-001 \
    --name multi-tenant-client-secret

# Optionally purge (irreversible)
az keyvault secret purge \
    --vault-name kv-gov-prod-001 \
    --name multi-tenant-client-secret
```

### Update Documentation

- Update `docs/AUTH_TRANSITION_ROADMAP.md` — mark Phase C complete
- Update `SESSION_HANDOFF.md` with new auth configuration
- Update CI/CD documentation to remove secret references

---

## Troubleshooting

### Issue: AADSTS70021 (Invalid client assertion)

**Cause:** The UAMI OIDC assertion is not being accepted by the Federated Identity Credential.

**Fix:**
```bash
# Verify FIC configuration
APP_OBJECT_ID=$(az ad app show --id <app-id> --query "id" -o tsv)
az ad app federated-credential show \
    --id "$APP_OBJECT_ID" \
    --federated-credential-id "github-actions-federation"

# Check subject matches exactly (case-sensitive!)
# Should be: repo:org/repo:ref:refs/heads/main
```

### Issue: AADSTS700022 (Invalid issuer)

**Cause:** The issuer URL in FIC doesn't match the actual token issuer.

**Fix:**
- For GitHub Actions: Issuer must be `https://token.actions.githubusercontent.com`
- For App Service: No FIC needed, uses direct UAMI assignment

### Issue: Key Vault access denied

**Cause:** UAMI doesn't have the required RBAC role on Key Vault.

**Fix:**
```bash
# Verify role assignment
az role assignment list \
    --assignee <uami-principal-id> \
    --scope <key-vault-id>

# Re-assign if missing
az role assignment create \
    --assignee-object-id <uami-principal-id> \
    --assignee-principal-type ServicePrincipal \
    --role "Key Vault Secrets User" \
    --scope <key-vault-id>
```

### Issue: UAMI not available in App Service

**Cause:** UAMI not assigned to App Service or identity not propagated.

**Fix:**
```bash
# Verify UAMI is assigned
az webapp identity show \
    --name app-gov-prod-001 \
    --resource-group rg-governance-production

# If not present, add it
az webapp identity assign \
    --name app-gov-prod-001 \
    --resource-group rg-governance-production \
    --identities /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mi-governance-platform

# Restart App Service to pick up identity
az webapp restart \
    --name app-gov-prod-001 \
    --resource-group rg-governance-production
```

### Issue: Token cache not refreshing

**Cause:** Cached token expired but not cleared.

**Fix:**
```python
# Clear token cache programmatically
from app.core.uami_credential import get_uami_provider

provider = get_uami_provider()
provider.clear_cache()

# Or for specific tenant
provider.clear_cache(tenant_id="<tenant-id>")
```

---

## Security Considerations

### Pros
- ✅ Zero secrets in configuration or code
- ✅ No secret rotation required ever
- ✅ Automatic credential lifecycle management by Azure
- ✅ Fine-grained RBAC via UAMI role assignments
- ✅ Short-lived tokens (1 hour default)
- ✅ Works with both App Service and GitHub Actions

### Cons
- ⚠️ UAMI is a single point of identity (but no secret to leak)
- ⚠️ Requires Azure infrastructure (not portable to other clouds)
- ⚠️ Slightly more complex initial setup
- ⚠️ FIC subject must be updated if GitHub repo/branch changes

### Mitigations
- UAMI can be recreated easily if compromised (no secrets to rotate)
- Multiple FICs can be created for different scenarios (branches, environments)
- Role assignments follow least privilege principle
- All authentication is logged to Azure AD Sign-in logs

---

## Environment-Specific Notes

### Local Development

UAMI authentication doesn't work locally (no IMDS endpoint). Use one of:

1. **Azure CLI login** (for testing):
```bash
az login
export USE_UAMI_AUTH=false
export AZURE_MULTI_TENANT_CLIENT_SECRET="<from-key-vault>"
```

2. **VS Code Azure extension** (for debugging)

3. **Keep Phase B enabled** for local development:
```bash
# .env.local
USE_UAMI_AUTH=false
USE_MULTI_TENANT_APP=true
```

### GitHub Actions

OIDC federation works automatically in GitHub Actions with `azure/login@v2`:

```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

The `actions/checkout` must precede `azure/login` for OIDC to work correctly.

### Staging vs Production

Use separate UAMIs for staging and production:

| Environment | UAMI Name | FIC Subject |
|-------------|-----------|-------------|
| Staging | `mi-governance-staging` | `repo:org/repo:ref:refs/heads/staging` |
| Production | `mi-governance-platform` | `repo:org/repo:ref:refs/heads/main` |

---

## References

- [Authentication Transition Roadmap](../AUTH_TRANSITION_ROADMAP.md)
- [Phase B Runbook](./phase-b-multi-tenant-app.md)
- [Azure AD Workload Identity Federation](https://learn.microsoft.com/en-us/azure/active-directory/develop/workload-identity-federation)
- [GitHub Actions OIDC with Azure](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-azure)
- [Federated Identity Credentials](https://learn.microsoft.com/en-us/azure/active-directory/develop/federated-identity-credentials)

---

## Success Criteria

Phase C implementation is complete when:

- [ ] UAMI `mi-governance-platform` exists in `rg-governance-production`
- [ ] Federated Identity Credential attached to multi-tenant app
- [ ] Key Vault RBAC roles assigned to UAMI
- [ ] GitHub Actions configured with OIDC (no secrets)
- [ ] App Service has UAMI assigned
- [ ] `USE_UAMI_AUTH=true` in configuration
- [ ] All tests pass:
  - `tests/unit/test_uami_credential.py`
  - `tests/smoke/test_uami_connectivity.py`
- [ ] Application authenticates successfully without client secrets
- [ ] Rollback to Phase B tested and documented
- [ ] Documentation updated (`AUTH_TRANSITION_ROADMAP.md`)

---

## Quick Reference

```bash
# Setup
./scripts/setup-uami-phase-c.sh

# Migrate
./scripts/migrate-to-phase-c.sh --uami-client-id <id>

# Rollback
./scripts/migrate-to-phase-c.sh --rollback

# Test
python -m pytest tests/unit/test_uami_credential.py -v
python -m pytest tests/smoke/test_uami_connectivity.py -v

# Verify
az identity show -n mi-governance-platform -g rg-governance-production
az ad app federated-credential list --id <app-object-id>
```
