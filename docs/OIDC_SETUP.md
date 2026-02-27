# OIDC Federation Setup for Azure Governance Platform

🔐 **Secure, Modern, Secret-Free Azure Deployments**

This guide walks you through setting up OpenID Connect (OIDC) federation between GitHub Actions and Azure AD. This modern authentication method eliminates the need for storing long-lived Azure credentials in GitHub secrets.

---

## 📋 Table of Contents

1. [What is OIDC Federation?](#what-is-oidc-federation)
2. [Why Use OIDC?](#why-use-oidc)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Detailed Setup](#detailed-setup)
6. [GitHub Environments](#github-environments)
7. [Migration from Legacy Auth](#migration-from-legacy-auth)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

---

## What is OIDC Federation?

OpenID Connect (OIDC) federation allows GitHub Actions to authenticate to Azure **without storing any secrets** in GitHub. Here's how it works:

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  GitHub Actions │ ──────► │  GitHub OIDC     │ ──────► │   Azure AD      │
│    (Workflow)   │         │  Token Provider  │         │ (Token Exchange)│
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                                                          │
        │                    Short-lived token                     │
        └──────────────────────────────────────────────────────────┘
```

**The Flow:**
1. GitHub Actions generates a short-lived OIDC token
2. Token is presented to Azure AD
3. Azure AD validates the token against configured federated credentials
4. Azure AD issues an Azure access token
5. Workflow uses the token to deploy resources

**Key Point:** No client secrets are ever stored in GitHub!

---

## Why Use OIDC?

### 🔒 Security Benefits

| Feature | Legacy (Client Secret) | OIDC Federation |
|---------|----------------------|-----------------|
| **Secret Storage** | Long-lived secret in GitHub | No secrets stored |
| **Token Lifetime** | Months/years (until rotated) | 5-10 minutes |
| **Rotation** | Manual, easy to forget | Automatic, every run |
| **Audit Trail** | Limited | Full OIDC token claims |
| **Branch Control** | ❌ No built-in control | ✅ Branch-based auth |
| **Environment Control** | ❌ Manual enforcement | ✅ Environment-based auth |

### 🚀 Operational Benefits

- **No secret rotation headaches** - Tokens expire automatically
- **No credential leakage risk** - Nothing to leak from GitHub
- **Fine-grained access control** - Branch and environment-based permissions
- **Compliance friendly** - Meets security compliance requirements
- **Free** - No additional Azure cost

---

## Prerequisites

Before you begin, ensure you have:

### Tools
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) (v2.40.0+)
- [jq](https://stedolan.github.io/jq/download/) (JSON processor)
- [Git](https://git-scm.com/downloads)

### Azure Permissions
You need one of these roles:
- **Owner** on the subscription
- **User Access Administrator** + **Contributor** on the resource group
- **Application Developer** + **Role Based Access Control Administrator**

### GitHub Access
- Admin access to the repository
- Ability to configure repository secrets
- Ability to create environments (for production protection)

---

## Quick Start

Run the setup script to automatically configure OIDC:

```bash
# Navigate to the infrastructure directory
cd infrastructure

# Make the script executable
chmod +x setup-oidc.sh

# Run the setup for development environment
./setup-oidc.sh -e dev -g rg-governance-dev

# Or for production
./setup-oidc.sh -e prod -g rg-governance-prod -r yourorg/azure-governance-platform
```

The script will:
1. ✅ Create an Azure AD App Registration
2. ✅ Create a Service Principal
3. ✅ Configure federated credentials for GitHub OIDC
4. ✅ Assign Azure RBAC roles
5. ✅ Output the GitHub secrets to configure

---

## Detailed Setup

### Step 1: Run the Setup Script

```bash
./setup-oidc.sh -e <environment> -g <resource-group> [-r <github-repo>]
```

**Parameters:**
- `-e, --environment`: Environment name (`dev`, `staging`, `prod`)
- `-g, --resource-group`: Azure resource group name
- `-r, --repo`: GitHub repo in format `owner/repo` (auto-detected if not provided)

**Example:**
```bash
./setup-oidc.sh -e prod -g rg-governance-prod -r mycompany/azure-governance-platform
```

### Step 2: Configure GitHub Secrets

The script will output the secrets you need to add. Go to:

**GitHub Repo → Settings → Secrets and variables → Actions → New repository secret**

Add these **Repository Secrets**:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AZURE_CLIENT_ID` | `<output from script>` | Azure AD App ID |
| `AZURE_TENANT_ID` | `<output from script>` | Azure AD Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | `<output from script>` | Azure Subscription ID |
| `AZURE_RESOURCE_GROUP` | `rg-governance-prod` | Resource group name |
| `AZURE_APP_SERVICE_NAME` | `app-governance-prod-xxx` | App Service name |

⚠️ **Important:** These are **NOT** secrets in the traditional sense - they're just identifiers. The actual authentication happens via OIDC tokens.

### Step 3: Configure GitHub Environments

Create environments for deployment protection:

**GitHub Repo → Settings → Environments → New environment**

#### Development Environment
- **Name:** `development`
- **Deployment branches:** `dev` only
- **Required reviewers:** None

#### Staging Environment
- **Name:** `staging`
- **Deployment branches:** `main` only
- **Required reviewers:** 1 reviewer (optional)

#### Production Environment
- **Name:** `production`
- **Deployment branches:** Only tags starting with `v`
- **Required reviewers:** 2 reviewers recommended
- **Wait timer:** 5 minutes (optional, for safety)

### Step 4: Test the Setup

Trigger a test deployment:

```bash
# Using GitHub CLI
gh workflow run deploy-oidc.yml --ref dev

# Or push to dev branch
git checkout -b dev
git push origin dev
```

Check the workflow run in GitHub Actions. You should see:
1. ✅ Azure Login (OIDC) - Successfully exchanged token
2. ✅ Deploy to Azure Web App
3. ✅ Smoke tests pass

---

## GitHub Environments

### Branch-to-Environment Mapping

| Branch/Trigger | Environment | Protection |
|----------------|-------------|------------|
| `dev` push | `development` | Auto-deploy |
| `main` push | `staging` | Auto-deploy |
| `v*` tag | `production` | Approval required |
| Pull Request | None (validation only) | N/A |

### Federated Credential Configuration

The setup script configures these federated credentials in Azure AD:

```
┌─────────────────────────┬─────────────────────────────────────────────────────┐
│ Credential Name         │ Subject (GitHub OIDC Token Claim)                   │
├─────────────────────────┼─────────────────────────────────────────────────────┤
│ main-branch             │ repo:owner/repo:ref:refs/heads/main                 │
│ dev-branch              │ repo:owner/repo:ref:refs/heads/dev                  │
│ tag-deploy              │ repo:owner/repo:ref:refs/tags/v*                    │
│ environment-production  │ repo:owner/repo:environment:production              │
│ environment-staging     │ repo:owner/repo:environment:staging                 │
│ environment-development │ repo:owner/repo:environment:development             │
│ pull-request            │ repo:owner/repo:pull_request                        │
└─────────────────────────┴─────────────────────────────────────────────────────┘
```

Each credential maps to a specific GitHub Actions context, ensuring:
- **Main branch** can only deploy to staging/production
- **Dev branch** can only deploy to development
- **Pull requests** get read-only or validation access
- **Tags** trigger production deployments

---

## Migration from Legacy Auth

### Current State (deploy.yml)

Your existing workflow uses:

```yaml
- name: Azure Login
  uses: azure/login@v2
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}  # Contains client_secret! 😱
```

Where `AZURE_CREDENTIALS` is a JSON containing:
```json
{
  "clientId": "...",
  "clientSecret": "...",  // ⚠️ Long-lived secret!
  "subscriptionId": "...",
  "tenantId": "..."
}
```

### Migration Steps

1. **Set up OIDC** (this doesn't break existing deployments)
   ```bash
   ./setup-oidc.sh -e prod -g rg-governance-prod
   ```

2. **Add new secrets** (alongside existing ones)
   - Add `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
   - Keep `AZURE_CREDENTIALS` for now (migration period)

3. **Test new workflow**
   ```bash
   gh workflow run deploy-oidc.yml --ref dev
   ```

4. **Update branch protection rules**
   - Require OIDC workflow for PRs
   - Set up environment protection rules

5. **Remove legacy secrets** (after successful migration)
   - Delete `AZURE_CREDENTIALS`
   - Delete old App Registration if desired

### Rollback Plan

If issues occur, you can immediately switch back:

```bash
# Re-enable legacy workflow
git checkout deploy.yml

# Or update deploy-oidc.yml to use credentials fallback
# (Not recommended for long-term, but works for emergencies)
```

---

## Troubleshooting

### Common Issues

#### ❌ "AADSTS70021: No matching federated identity record found"

**Cause:** The federated credential subject doesn't match the GitHub Actions token.

**Solution:**
```bash
# Verify federated credentials
az ad app federated-credential list --id <AZURE_CLIENT_ID>

# Check if the subject matches your repo
# Should be: repo:owner/repo:ref:refs/heads/main

# If missing, add it:
az ad app federated-credential create \
  --id <AZURE_CLIENT_ID> \
  --parameters '{
    "name": "main-branch",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:<owner>/<repo>:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

#### ❌ "The client_id does not match the audience"

**Cause:** The Azure App Registration audience is misconfigured.

**Solution:**
```bash
# Check the App Registration manifest
az ad app show --id <AZURE_CLIENT_ID> --query "signInAudience"

# Should be "AzureADMyOrg" or "AzureADMultipleOrgs"
# Update if needed:
az ad app update --id <AZURE_CLIENT_ID> --sign-in-audience AzureADMyOrg
```

#### ❌ "Insufficient permissions to deploy"

**Cause:** Service principal doesn't have required Azure RBAC roles.

**Solution:**
```bash
# List current role assignments
az role assignment list --assignee <AZURE_CLIENT_ID>

# Add missing roles
az role assignment create \
  --role "Website Contributor" \
  --assignee <AZURE_CLIENT_ID> \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg-name>
```

#### ❌ "id-token: write permission is required"

**Cause:** Workflow permissions not configured.

**Solution:**
Add to your workflow:
```yaml
permissions:
  id-token: write  # Required for OIDC
  contents: read   # Required for checkout
```

### Debugging OIDC Tokens

Add this step to your workflow for debugging:

```yaml
- name: Debug OIDC Token
  run: |
    # Get the OIDC token
    TOKEN=$(curl -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
      "$ACTIONS_ID_TOKEN_REQUEST_URL" | jq -r '.value')
    
    # Decode the token (first two parts)
    echo "$TOKEN" | cut -d'.' -f1 | base64 -d 2>/dev/null | jq .  # Header
    echo "$TOKEN" | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .  # Payload
  env:
    ACTIONS_ID_TOKEN_REQUEST_TOKEN: ${{ env.ACTIONS_ID_TOKEN_REQUEST_TOKEN }}
    ACTIONS_ID_TOKEN_REQUEST_URL: ${{ env.ACTIONS_ID_TOKEN_REQUEST_URL }}
```

### Verification Commands

```bash
# Check App Registration
az ad app show --id <AZURE_CLIENT_ID>

# Check Service Principal
az ad sp show --id <AZURE_CLIENT_ID>

# List Federated Credentials
az ad app federated-credential list --id <AZURE_CLIENT_ID>

# Check Role Assignments
az role assignment list --assignee <AZURE_CLIENT_ID>

# Test login (simulates what GitHub Actions does)
az login --service-principal \
  --username <AZURE_CLIENT_ID> \
  --tenant <AZURE_TENANT_ID> \
  --federated-token <oidc-token>
```

---

## Security Best Practices

### 1. Principle of Least Privilege

Only assign necessary roles:

```bash
# For dev deployments (minimal permissions)
az role assignment create --role "Website Contributor" --assignee <APP_ID>

# For production (additional monitoring/secret access)
az role assignment create --role "Monitoring Contributor" --assignee <APP_ID>
az role assignment create --role "Key Vault Secrets User" --assignee <APP_ID>
```

### 2. Environment Protection Rules

**Production should ALWAYS require:**
- ✅ Required reviewers (minimum 1, recommend 2)
- ✅ Deployment branches (only tags starting with `v`)
- ✅ Optional: Wait timer for safety

### 3. Separate App Registrations per Environment

Consider creating separate app registrations:

```bash
# Dev
./setup-oidc.sh -e dev -g rg-governance-dev

# Staging  
./setup-oidc.sh -e staging -g rg-governance-staging

# Production (isolated)
./setup-oidc.sh -e prod -g rg-governance-prod
```

This provides maximum isolation between environments.

### 4. Regular Audits

```bash
# Monthly audit script
echo "OIDC Federated Credentials Audit - $(date)"
echo "=========================================="

APP_ID=$(cat infrastructure/.oidc-config-prod.json | jq -r '.appRegistration.clientId')

echo "App Registration: $APP_ID"
echo ""
echo "Federated Credentials:"
az ad app federated-credential list --id "$APP_ID" --query "[].{Name:name, Subject:subject}"

echo ""
echo "Role Assignments:"
az role assignment list --assignee "$APP_ID" --query "[].{Role:roleDefinitionName, Scope:scope}"
```

### 5. Monitoring and Alerting

Set up alerts for:
- Failed OIDC token exchanges
- Unusual deployment patterns
- Role assignment changes

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GITHUB ACTIONS                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Build      │───►│  Push Image  │───►│ OIDC Login   │                   │
│  │   & Test     │    │  to GHCR     │    │ (No secrets!)│                   │
│  └──────────────┘    └──────────────┘    └──────┬───────┘                   │
└───────────────────────────────────────────────────┼─────────────────────────┘
                                                    │
                       GitHub OIDC Token            │
                       (short-lived, branch-scoped) │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AZURE AD                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Federated Credentials                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │ │
│  │  │ main-branch │  │ dev-branch  │  │    tags     │  │ environments │  │ │
│  │  │  (staging)  │  │    (dev)    │  │  (production)│  │ (protected)  │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│                    ┌───────────────────┐                                    │
│                    │  Token Exchange   │                                    │
│                    │ Azure Access Token│                                    │
│                    └─────────┬─────────┘                                    │
└──────────────────────────────┼──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AZURE RESOURCES                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  App Service │◄───│  Deploy      │◄───│  Azure       │                   │
│  │  (Container) │    │  Container   │    │  ARM API     │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
│  RBAC: Website Contributor, Web Plan Contributor                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## References

- [Azure AD OIDC with GitHub Actions](https://docs.microsoft.com/en-us/azure/developer/github/connect-from-azure?tabs=azure-portal%2Clinux)
- [GitHub OIDC Token Reference](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Azure Federated Identity Credentials](https://docs.microsoft.com/en-us/azure/active-directory/develop/workload-identity-federation)
- [Security Hardening for GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review [GitHub Actions OIDC documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-azure)
3. Open an issue in the repository with:
   - Error message
   - Workflow run URL
   - Output of verification commands

---

**🎉 You're now set up for secure, secret-free Azure deployments!**
