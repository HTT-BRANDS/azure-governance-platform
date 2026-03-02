# GitHub Container Registry Setup Guide

## Why This is Needed

Azure App Service cannot pull private container images from GitHub Container Registry (GHCR) without authentication. This guide walks through creating the necessary credentials.

## Quick Setup (Interactive)

```bash
./scripts/setup-ghcr-credentials.sh
```

This interactive script will:
1. Get your GitHub username
2. Guide you to create a PAT with 'read:packages' scope
3. Configure Azure App Service with the credentials
4. Restart the app and verify it's online

## Manual Setup

### Step 1: Create GitHub PAT

1. Go to https://github.com/settings/tokens/new
2. Fill in:
   - **Token name**: `Azure-Governance-Dev-Container-Access`
   - **Expiration**: 90 days (or custom)
   - **Scopes**: ☑ `read:packages`
3. Click **Generate token**
4. **Copy the token immediately** (you won't see it again!)

### Step 2: Configure Azure

Replace `YOUR_GITHUB_USERNAME` and `YOUR_PAT`:

```bash
az webapp config appsettings set \
  --name app-governance-dev-001 \
  --resource-group rg-governance-dev \
  --settings \
    DOCKER_REGISTRY_SERVER_USERNAME="YOUR_GITHUB_USERNAME" \
    DOCKER_REGISTRY_SERVER_PASSWORD="YOUR_PAT"
```

### Step 3: Restart App Service

```bash
az webapp restart \
  --name app-governance-dev-001 \
  --resource-group rg-governance-dev
```

### Step 4: Verify

```bash
# Wait 2-3 minutes
curl https://app-governance-dev-001.azurewebsites.net/health
```

## Security Best Practices

### Token Rotation
Set a calendar reminder 7 days before expiration to rotate the token.

### Azure Key Vault (Recommended)
Store the PAT in Azure Key Vault instead of App Settings:

```bash
# Create Key Vault
az keyvault create --name kv-governance-dev --resource-group rg-governance-dev

# Store PAT
az keyvault secret set \
  --name ghcr-pat \
  --vault-name kv-governance-dev \
  --value "YOUR_PAT"

# Configure App Service to use Key Vault reference
az webapp config appsettings set \
  --name app-governance-dev-001 \
  --resource-group rg-governance-dev \
  --settings \
    DOCKER_REGISTRY_SERVER_PASSWORD="@Microsoft.KeyVault(SecretUri=https://kv-governance-dev.vault.azure.net/secrets/ghcr-pat/)"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to pull image" | Check PAT has 'read:packages' scope |
| "401 Unauthorized" | PAT may be expired, create new one |
| "403 Forbidden" | PAT lacks packages scope, regenerate |
| Container not updating | Check DOCKER_ENABLE_CI is set to true |

## FAQ

**Q: Why can't this be automated?**
A: GitHub does not allow programmatic creation of Personal Access Tokens for security reasons. The user must manually create it through the GitHub web UI.

**Q: What permissions does the PAT need?**
A: Only `read:packages` scope is required. This allows Azure to pull the private container image.

**Q: How long does setup take?**
A: About 5-10 minutes total: 2 minutes to create the PAT, 1 minute to run the script, and 2-3 minutes for the container to start.

**Q: What happens when the PAT expires?**
A: The container will fail to pull on next deployment. Run `./scripts/setup-ghcr-credentials.sh` again to update the credentials.
