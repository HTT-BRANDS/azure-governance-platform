# 🔧 Fix Production 503 Error - GHCR Authentication

**Runbook ID:** `RB-GHCR-503-01`  
**Severity:** P1 - Production Outage  
**Estimated Fix Time:** 5 minutes  
**Last Updated:** 2025-01-XX

---

## 🚨 Problem Summary

The Azure App Service returns **HTTP 503 Service Unavailable** because it cannot authenticate to GitHub Container Registry (GHCR) to pull the container image.

**Common Symptoms:**
- Site returns 503 errors
- App Service logs show "Image pull failed" or "authentication required"
- Container doesn't start or restarts continuously

---

## 🎯 Quick Fix (Automated Script)

For the fastest resolution, use the interactive fix script:

```bash
./scripts/apply-production-fix.sh
```

This script will:
1. Prompt for your GitHub username and PAT
2. Apply the fix automatically
3. Verify the health endpoint
4. Report success/failure

---

## 📋 Manual Fix Steps

If you prefer to fix manually, follow these exact steps:

### Step 1: Create GitHub Personal Access Token (PAT)

1. **Navigate to GitHub token creation:**
   - Visit: https://github.com/settings/tokens/new

2. **Configure the token:**
   - **Token type:** Select **"Classic token"** (not fine-grained)
   - **Note:** `Azure App Service GHCR Pull`
   - **Expiration:** 90 days (recommended)
   - **Scopes:** ✅ **Only** check `read:packages`
     - ❌ Do NOT select other scopes - they aren't needed

3. **Generate and copy:**
   - Click **"Generate token"**
   - ⚠️ **COPY the token immediately** - you cannot see it again!
   - The token starts with `ghp_`

---

### Step 2: Apply to Azure App Service

Run the Azure CLI command to update the container registry credentials:

```bash
# Set the GitHub PAT as container registry password
az webapp config container set \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --docker-registry-server-url https://ghcr.io \
  --docker-registry-server-username YOUR_GITHUB_USERNAME \
  --docker-registry-server-password ghp_XXXXXXXXXX
```

**Replace:**
- `YOUR_GITHUB_USERNAME` with your actual GitHub username
- `ghp_XXXXXXXXXX` with the PAT you copied in Step 1

**Expected output:**
```json
{
  "dockerRegistryServerUrl": "https://ghcr.io",
  "dockerRegistryServerUsername": "your-username",
  "dockerRegistryServerPassword": null  // (hidden for security)
}
```

---

### Step 3: Restart and Verify

1. **Restart the App Service** (triggers container pull):
   ```bash
   az webapp restart \
     --name app-governance-prod \
     --resource-group rg-governance-production
   ```

2. **Wait 2 minutes** for container startup

3. **Verify health endpoint:**
   ```bash
   curl -s https://app-governance-prod.azurewebsites.net/health
   ```

**Expected response:**
```json
{"status":"healthy","timestamp":"2025-01-XX..."}
```

---

## 🔄 Alternative Fix: Make GHCR Image Public

If managing PATs is problematic, you can make the GHCR image public:

1. **Navigate to package settings:**
   - Visit: https://github.com/HTT-BRANDS/control-tower/pkgs/container/control-tower

2. **Change visibility:**
   - Click **"Package settings"** (gear icon)
   - Find **"Change package visibility"**
   - Select **"Public"**
   - Confirm with your GitHub password

3. **Clear registry credentials** (no auth needed):
   ```bash
   az webapp config appsettings delete \
     --name app-governance-prod \
     --resource-group rg-governance-production \
     --setting-names DOCKER_REGISTRY_SERVER_USERNAME DOCKER_REGISTRY_SERVER_PASSWORD
   ```

**Pros:** No authentication needed, simpler deployment  
**Cons:** Anyone can pull your image (may be acceptable for open source)

---

## 🔍 Troubleshooting

### "Authentication failed" or 401 errors
- Verify PAT has **only** `read:packages` scope
- Ensure PAT hasn't expired
- Check that your GitHub user has access to the `HTT-BRANDS` organization

### Container still won't start after fix
```bash
# Check detailed logs
az webapp log tail --name app-governance-prod --resource-group rg-governance-production

# View container logs in portal
open "https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-governance-production/providers/Microsoft.Web/sites/app-governance-prod/containerLogs"
```

### PAT expired (90 days later)
1. Create a new PAT (repeat Step 1)
2. Update the App Service (repeat Step 2)
3. Consider using the public image alternative to avoid future PAT rotation

---

## 📞 Escalation

If the fix fails after 2 attempts:
1. Check Azure Service Health: https://status.azure.com
2. Verify GitHub Status: https://www.githubstatus.com
3. Contact: `#incident-response` Slack channel
4. Page on-call engineer if outage persists >30 minutes

---

## 📝 Post-Fix Checklist

- [ ] Health endpoint returns 200
- [ ] Main site loads without 503 errors
- [ ] PAT noted in team password manager (1Password/Bitwarden)
- [ ] Calendar reminder set for PAT expiration (90 days)
- [ ] Incident documented in PagerDuty/Opsgenie

---

## 💡 Prevention

To avoid future 503 errors:

1. **Use public image** (if security allows) - no auth needed
2. **Set PAT rotation reminder** 7 days before expiration
3. **Enable deployment slots** - deploy to staging first
4. **Monitor container startup** with Application Insights

---

*This runbook is part of the Azure Governance Platform operations documentation.*
