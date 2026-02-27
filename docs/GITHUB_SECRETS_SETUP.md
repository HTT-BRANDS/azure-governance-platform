# GitHub Secrets Setup Guide

> **Version:** 1.0  
> **Last Updated:** February 2025  
> **Estimated Setup Time:** 20-30 minutes

---

## 📋 Overview

This guide explains how to configure GitHub secrets for the Azure Governance Platform deployment using **OIDC (OpenID Connect) federation**.

### Why OIDC?

Traditional approaches store long-lived Azure credentials in GitHub secrets, which creates security risks:
- ❌ Secrets can be leaked
- ❌ No expiration on credentials
- ❌ Manual rotation required

**OIDC federation solves these problems:**
- ✅ No long-lived secrets in GitHub
- ✅ Short-lived tokens (auto-expire)
- ✅ Automatic credential exchange
- ✅ Reduced attack surface
- ✅ No manual rotation needed

---

## 🔐 Required GitHub Secrets

Configure these in your GitHub repository: **Settings → Secrets and variables → Actions**

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AZURE_CLIENT_ID` | Azure AD App Registration ID | `12345678-1234-1234-1234-123456789012` |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | `abcdef12-3456-7890-abcd-ef1234567890` |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID | `11111111-2222-3333-4444-555555555555` |
| `AZURE_RESOURCE_GROUP` | Resource group name | `rg-governance-dev` |
| `AZURE_APP_SERVICE_NAME` | App Service base name | `app-governance-dev-001` |

> **Note:** Unlike traditional approaches, you do **NOT** need `AZURE_CLIENT_SECRET` or `AZURE_CREDENTIALS` JSON with OIDC!

---

## 🚀 Setup Instructions

### Step 1: Get Your Azure AD Tenant ID

```bash
# Login to Azure
az login

# Get your tenant ID
az account show --query tenantId -o tsv
```

**Add to GitHub Secrets:**
- Name: `AZURE_TENANT_ID`
- Value: The tenant ID from above

---

### Step 2: Get Your Azure Subscription ID

```bash
# Get your subscription ID
az account show --query id -o tsv
```

**Add to GitHub Secrets:**
- Name: `AZURE_SUBSCRIPTION_ID`
- Value: The subscription ID from above

---

### Step 3: Create Azure AD App Registration

#### Option A: Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory
2. Click **App registrations** → **New registration**
3. Configure:
   - **Name:** `github-actions-governance-platform`
   - **Supported account types:** Accounts in this organizational directory only
   - **Redirect URI:** Leave blank (we'll use it for OIDC, not OAuth)
4. Click **Register**
5. Copy the **Application (client) ID**

#### Option B: Using Azure CLI

```bash
# Create app registration
APP_NAME="github-actions-governance-platform"

APP_ID=$(az ad app create \
  --display-name "$APP_NAME" \
  --query appId -o tsv)

echo "App ID: $APP_ID"
```

**Add to GitHub Secrets:**
- Name: `AZURE_CLIENT_ID`
- Value: The Application (client) ID

---

### Step 4: Configure OIDC Federation

This step allows GitHub Actions to authenticate to Azure without storing secrets.

#### Using Azure Portal

1. Go to your App Registration → **Certificates & secrets**
2. Click **Federated credentials** tab
3. Click **Add credential**
4. Select **GitHub Actions deploying Azure resources**
5. Configure:
   - **Organization:** Your GitHub org/username (e.g., `tygranlund`)
   - **Repository:** Repository name (e.g., `azure-governance-platform`)
   - **Entity type:** Select appropriate option:
     - **Environment** → For environment-specific deployments (dev/staging/prod)
     - **Branch** → For branch-based deployments (main, dev)
     - **Pull request** → For PR validation
     - **Tag** → For release deployments
6. For **dev** deployment, select **Branch** and enter `dev`
7. Click **Add**

8. Repeat for **staging** (branch: `main` or `master`)
9. Repeat for **production** (branch: `main` or use tag-based)

#### Using Azure CLI

```bash
# Variables
APP_ID="your-app-id-here"  # From Step 3
ORG_NAME="tygranlund"
REPO_NAME="azure-governance-platform"

# Create federated credential for dev branch
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters '{
    "name": "github-actions-dev",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'"$ORG_NAME"'/'"$REPO_NAME"':ref:refs/heads/dev",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Create federated credential for main branch (staging)
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters '{
    "name": "github-actions-staging",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'"$ORG_NAME"'/'"$REPO_NAME"':ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Create federated credential for production tags
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters '{
    "name": "github-actions-production",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'"$ORG_NAME"'/'"$REPO_NAME"':ref:refs/tags/v*",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

---

### Step 5: Grant Azure Permissions

Your app needs permissions to deploy resources. Grant it access to your subscription or resource group.

#### Option A: Subscription Level (Recommended for Dev)

```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Assign Contributor role at subscription level
az role assignment create \
  --assignee "$APP_ID" \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"
```

> **Note:** Contributor role allows the app to create/modify/delete resources in the subscription.

#### Option B: Resource Group Level (More Secure)

```bash
# Create resource group first
az group create \
  --name "rg-governance-dev" \
  --location "eastus"

# Assign Contributor role at resource group level
az role assignment create \
  --assignee "$APP_ID" \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-governance-dev"
```

---

### Step 6: Configure GitHub Secrets

Now add all the secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

| Secret | Value |
|--------|-------|
| `AZURE_CLIENT_ID` | Application (client) ID from Step 3 |
| `AZURE_TENANT_ID` | Tenant ID from Step 1 |
| `AZURE_SUBSCRIPTION_ID` | Subscription ID from Step 2 |
| `AZURE_RESOURCE_GROUP` | `rg-governance-dev` (or your RG name) |
| `AZURE_APP_SERVICE_NAME` | `app-governance-dev-001` (or your app name) |

---

### Step 7: Verify OIDC Setup

Test the OIDC configuration by pushing to the dev branch:

```bash
# Create and switch to dev branch
git checkout -b dev

# Make a small change and commit
echo "# Dev branch" >> README.md
git add README.md
git commit -m "Test dev deployment"

# Push to trigger deployment
git push origin dev
```

Check GitHub Actions to see if the deployment succeeds.

---

## 🛡️ Environment Protection Rules

Configure environment protection to require approval for production deployments.

### Step 1: Create Environments

1. Go to repository **Settings** → **Environments**
2. Click **New environment**
3. Create environments: `development`, `staging`, `production`

### Step 2: Configure Production Protection

For the `production` environment:

1. Select **production** environment
2. Under **Protection rules**, check:
   - ☑️ **Required reviewers** (add yourself or team)
   - ☑️ **Wait timer** (optional: 5-15 minutes for safety)
   - ☑️ **Deployment branches** → `Protected branches` or `Selected branches`
3. Click **Save protection rules**

### Step 3: Configure Staging Protection (Optional)

For `staging`:
- ☑️ **Required reviewers** (optional for staging)
- ☑️ **Wait timer** (optional: 1-2 minutes)

### Step 4: Configure Development

For `development`:
- No required reviewers (auto-deploy on push)
- Fast feedback for developers

---

## 🔍 Troubleshooting

### Issue: "AADSTS70021: No matching federated identity record found"

**Cause:** OIDC federation not configured correctly.

**Solution:**
1. Verify federated credentials in Azure AD
2. Check that the subject matches exactly:
   - Format: `repo:ORG/REPO:ref:refs/heads/BRANCH`
   - Case-sensitive!
3. Re-create the federated credential

### Issue: "Insufficient permissions to complete the operation"

**Cause:** App doesn't have enough permissions.

**Solution:**
```bash
# Check role assignments
az role assignment list --assignee "$APP_ID"

# Re-add Contributor role
az role assignment create \
  --assignee "$APP_ID" \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"
```

### Issue: "Subscription not found"

**Cause:** Wrong subscription ID in secrets.

**Solution:**
```bash
# Verify subscription ID
az account show --query id -o tsv

# Update GitHub secret with correct value
```

### Issue: Deployment fails with "Resource group not found"

**Cause:** Resource group doesn't exist yet.

**Solution:**
1. Deploy infrastructure first using Bicep
2. Or create resource group manually:
```bash
az group create --name rg-governance-dev --location eastus
```

---

## 📊 Verification Checklist

After setup, verify everything works:

```bash
# 1. Verify app registration
az ad app show --id "$APP_ID" --query "displayName"

# 2. Verify federated credentials
az ad app federated-credential list --id "$APP_ID"

# 3. Verify role assignment
az role assignment list --assignee "$APP_ID" --query "[].roleDefinitionName"

# 4. Verify resource group exists
az group show --name "rg-governance-dev"

# 5. Test deployment (via GitHub Actions)
git push origin dev
```

---

## 🔗 Related Documentation

| Document | Description |
|----------|-------------|
| [OIDC_SETUP.md](./OIDC_SETUP.md) | Detailed OIDC setup with screenshots |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Full deployment guide |
| [DEV_DEPLOYMENT_STATUS.md](./DEV_DEPLOYMENT_STATUS.md) | Current dev deployment status |

---

## 📚 Additional Resources

- [GitHub Docs: Configure OIDC in Azure](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-azure)
- [Microsoft Docs: Workload identity federation](https://learn.microsoft.com/en-us/azure/active-directory/develop/workload-identity-federation)
- [Azure RBAC Documentation](https://docs.microsoft.com/en-us/azure/role-based-access-control/)

---

## 🔄 Rotation (Not Needed!)

With OIDC federation, you **don't need to rotate secrets**! 🎉

The authentication flow:
1. GitHub Actions generates a short-lived OIDC token
2. Token is exchanged for Azure access token
3. Access token expires in ~1 hour
4. No persistent credentials to rotate

---

*Last updated: February 2025*
