# Manual App Registration Setup Guide

> **For:** Tyler (Riverside DevOps)  
> **Purpose:** Step-by-step manual instructions for creating app registrations in Azure Portal when automation isn't available  
> **Tenants:** HTT, BCC, FN, TLL

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Reference](#quick-reference)
3. [Detailed Instructions](#detailed-instructions)
   - Step 1: Sign in to Azure Portal
   - Step 2: Navigate to App Registrations
   - Step 3: Create New Registration
   - Step 4: Configure API Permissions
   - Step 5: Grant Admin Consent
   - Step 6: Create Client Secret
   - Step 7: Export Credentials
4. [Tenant-Specific Details](#tenant-specific-details)
5. [Verification Steps](#verification-steps)
6. [Troubleshooting](#troubleshooting)
7. [Security Checklist](#security-checklist)

---

## Prerequisites

Before you begin, ensure you have:

- [ ] **Global Administrator** role in the target tenant
- [ ] Access to [Azure Portal](https://portal.azure.com)
- [ ] A secure location to store credentials (Key Vault or password manager)
- [ ] PowerShell 7+ with Microsoft.Graph modules (for verification)

### Required Permissions

You need these permissions to complete setup:

| Permission | Purpose |
|------------|---------|
| `Application.ReadWrite.All` | Create/manage app registrations |
| `AppRoleAssignment.ReadWrite.All` | Grant admin consent |
| `Directory.ReadWrite.All` | Read/write directory data |

---

## Quick Reference

### Configuration Summary

```
App Name:     Riverside-Governance-Platform
App Type:     Single tenant (AzureADMyOrg)
Redirect URI: None required

Required API Permissions:
┌─────────────────────────────────────┬───────────────┬─────────────┐
│ API                                 │ Permission    │ Type        │
├─────────────────────────────────────┼───────────────┼─────────────┤
│ Microsoft Graph                     │ Reports.Read.All              │ Application │
│ Microsoft Graph                     │ SecurityEvents.Read.All       │ Application │
│ Microsoft Graph                     │ Domain.Read.All               │ Application │
│ Microsoft Graph                     │ Directory.Read.All            │ Application │
└─────────────────────────────────────┴───────────────┴─────────────┘
```

### Tenant IDs (Keep Handy!)

| Tenant | Name | Tenant ID |
|--------|------|-----------|
| HTT | Huntington Technology | `0c0e35dc-188a-4eb3-b8ba-61752154b407` |
| BCC | Beach Cities Consulting | `b5380912-79ec-452d-a6ca-6d897b19b294` |
| FN | Fulton & Nieman | `98723287-044b-4bbb-9294-19857d4128a0` |
| TLL | Tower Legal | `3c7d2bf3-b597-4766-b5cb-2b489c2904d6` |

---

## Detailed Instructions

### Step 1: Sign in to Azure Portal

1. Open your browser and navigate to: **https://portal.azure.com**
2. Sign in with your **Global Administrator** account for the target tenant
3. Verify you're in the correct tenant by checking the directory name in the top-right corner

> 💡 **Tip:** If you're a guest in multiple tenants, click your profile picture in the top-right to switch directories.

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Azure Portal                                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Directory: HTT (0c0e35dc-188a-...)  [Switch] ▼    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📍 Verify this matches your target tenant                  │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 2: Navigate to App Registrations

1. In the search bar at the top, type: **"App registrations"**
2. Click on **App registrations** under Services
3. Alternatively: Azure Active Directory → App registrations

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Search: App registrations  [🔍]                           │
│                                                             │
│  Services                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⭐ App registrations                                  │   │
│  │     Create and manage your app registrations         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 3: Create New Registration

1. Click the **+ New registration** button (top-left)

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  App registrations                                          │
│                                                             │
│  [+ New registration]  [🔍 Search]  [Manage: Deleted apps]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

2. Fill in the registration form:

   | Field | Value |
   |-------|-------|
   | **Name** | `Riverside-Governance-Platform` |
   | **Supported account types** | ✓ Accounts in this organizational directory only (Single tenant) |
   | **Redirect URI** | (Leave blank - not needed for daemon app) |

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Register an application                                    │
│                                                             │
│  Name *                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Riverside-Governance-Platform                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Supported account types                                    │
│  ○ Accounts in any organizational directory                 │
│  ● Accounts in this organizational directory only  ✓       │
│  ○ Personal Microsoft accounts only                         │
│  ○ Personal + org accounts                                │
│                                                             │
│  Redirect URI (optional)                                    │
│  [No selection]  ┌─────────────────────────────────────┐   │
│                                                             │
│                    [Register]                               │
└─────────────────────────────────────────────────────────────┘
```

3. Click **Register**
4. **SAVE THESE VALUES** - you'll need them later:
   - **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - **Directory (tenant) ID**: Should match the tenant ID from the table above

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Riverside-Governance-Platform                              │
│                                                             │
│  Essentials                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Application (client) ID:  abc123...-xyz789          │   │
│  │ Directory (tenant) ID:    0c0e35dc...               │   │
│  │ Object ID:                def456...                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📝 COPY: Client ID and Tenant ID                           │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 4: Configure API Permissions

1. In the left sidebar, click **API permissions**
2. Click **+ Add a permission**

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  API permissions                                            │
│                                                             │
│  Configured permissions                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ No permissions configured                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [+ Add a permission]                                       │
└─────────────────────────────────────────────────────────────┘
```

3. Select **Microsoft Graph** (the big Microsoft Graph tile, not Graph API)

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Request API permissions                                    │
│                                                             │
│  Select an API:                                             │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │             │  │             │  │             │          │
│  │ Microsoft   │  │ APIs my     │  │ APIs my     │          │
│  │ Graph       │  │ org uses    │  │ tenant uses │          │
│  │   [SELECT]  │  │             │  │             │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

4. Select **Application permissions** (not Delegated!)

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Microsoft Graph                                              │
│                                                             │
│  What type of permissions does your application require?    │
│                                                             │
│  ○ Delegated permissions                                    │
│  ● Application permissions  ✓                              │
│                                                             │
│  Permission:                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Type to search...                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

5. Search for and add each permission:

   | Permission | Description |
   |------------|-------------|
   | `Reports.Read.All` | Read all reports |
   | `SecurityEvents.Read.All` | Read security events |
   | `Domain.Read.All` | Read domains |
   | `Directory.Read.All` | Read directory data |

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Select permissions                                         │
│                                                             │
│  ☑ Reports.Read.All        Read all reports               │
│  ☑ SecurityEvents.Read.All Read your organization's       │
│                              security events                │
│  ☑ Domain.Read.All         Read all domains               │
│  ☑ Directory.Read.All      Read directory data              │
│                                                             │
│                  [Add permissions]                          │
└─────────────────────────────────────────────────────────────┘
```

6. Click **Add permissions** after selecting each one

7. Verify all 4 permissions appear in the list:

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Configured permissions                                     │
│                                                             │
│  API / Permissions name             Type        Status      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Microsoft Graph                                      │   │
│  │   Reports.Read.All                Application ⚠     │   │
│  │   SecurityEvents.Read.All         Application ⚠     │   │
│  │   Domain.Read.All                 Application ⚠     │   │
│  │   Directory.Read.All              Application ⚠     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ⚠ = Not granted for HTT (grant admin consent)             │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 5: Grant Admin Consent

⚠️ **CRITICAL STEP** - Without this, the app cannot access data!

1. In the API permissions page, click **Grant admin consent for [Tenant]**

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  API permissions                                            │
│                                                             │
│  [+ Add a permission]  [Grant admin consent for HTT]  ⬅️   │
│                                                             │
│  ⚠️ Yes button appears here after clicking                 │
└─────────────────────────────────────────────────────────────┘
```

2. Click **Yes** in the confirmation dialog

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Grant admin consent confirmation                           │
│                                                             │
│  Do you want to grant admin consent for the requested      │
│  permissions for all accounts in HTT?                       │
│                                                             │
│                         [No]   [Yes]  ⬅️                   │
└─────────────────────────────────────────────────────────────┘
```

3. Verify all permissions now show **✓ Granted for [Tenant]**:

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Configured permissions                                     │
│                                                             │
│  API / Permissions name             Type        Status      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Microsoft Graph                                      │   │
│  │   Reports.Read.All                Application ✓     │   │
│  │   SecurityEvents.Read.All         Application ✓     │   │
│  │   Domain.Read.All                 Application ✓     │   │
│  │   Directory.Read.All              Application ✓     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ✓ = Granted for HTT                                        │
└─────────────────────────────────────────────────────────────┘
```

> ✅ **Success!** All permissions are now granted.

---

### Step 6: Create Client Secret

1. In the left sidebar, click **Certificates & secrets**
2. Click **+ New client secret**

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Certificates & secrets                                     │
│                                                             │
│  Client secrets                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Description       | Expires          | Value          │   │
│  │ (No client secrets)                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [+ New client secret]                                       │
└─────────────────────────────────────────────────────────────┘
```

3. Fill in the form:

   | Field | Recommended Value |
   |-------|-------------------|
   | **Description** | `Riverside-Governance-Secret-YYYY-MM-DD` |
   | **Expires** | 12 months (24 months max) |

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Add a client secret                                        │
│                                                             │
│  Description *                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Riverside-Governance-Secret-2024-01-15              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Expires *                                                  │
│  ● In 3 months                                              │
│  ○ In 1 year                                               │
│  ○ In 2 years                                              │
│  ○ Custom                                                  │
│                                                             │
│                  [Add]   [Cancel]                          │
└─────────────────────────────────────────────────────────────┘
```

4. Click **Add**
5. **🔴 IMPORTANT:** Copy the secret value **immediately**!

```
[SCREENSHOT DESCRIPTION]
┌─────────────────────────────────────────────────────────────┐
│  Client secrets                                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Secret ID:    abc123...                               │   │
│  │                                             ⬅️ COPY!  │   │
│  │ Value:        xoJ8Q~very.long.secret.here...       │   │
│  │                                             ⬅️ COPY!  │   │
│  │ Secret ID:    def456...                               │   │
│  │ Expires:      1/15/2026                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🔴 THIS IS THE ONLY TIME YOU'LL SEE THE SECRET VALUE!     │
│  🔴 COPY IT NOW - YOU CANNOT RETRIEVE IT LATER!           │
└─────────────────────────────────────────────────────────────┘
```

6. Store securely in Key Vault or password manager

---

### Step 7: Export Credentials

Create a `.env` file with the following format:

```bash
# HTT - Huntington Technology
RIVERSIDE_HTT_TENANT_ID=0c0e35dc-188a-4eb3-b8ba-61752154b407
RIVERSIDE_HTT_CLIENT_ID=<your-application-client-id>
RIVERSIDE_HTT_CLIENT_SECRET=<your-client-secret-value>

# Repeat for BCC, FN, TLL...
```

---

## Tenant-Specific Details

### HTT - Huntington Technology

```
Tenant ID:  0c0e35dc-188a-4eb3-b8ba-61752154b407
Primary Contact: (Add here)
Notes: (Add any special instructions)
```

### BCC - Beach Cities Consulting

```
Tenant ID:  b5380912-79ec-452d-a6ca-6d897b19b294
Primary Contact: (Add here)
Notes: (Add any special instructions)
```

### FN - Fulton & Nieman

```
Tenant ID:  98723287-044b-4bbb-9294-19857d4128a0
Primary Contact: (Add here)
Notes: (Add any special instructions)
```

### TLL - Tower Legal

```
Tenant ID:  3c7d2bf3-b597-4766-b5cb-2b489c2904d6
Primary Contact: (Add here)
Notes: (Add any special instructions)
```

---

## Verification Steps

### Method 1: PowerShell Verification Script

```powershell
# Test-GraphConnection.ps1
param(
    [Parameter(Mandatory)]
    [string]$TenantId,
    
    [Parameter(Mandatory)]
    [string]$ClientId,
    
    [Parameter(Mandatory)]
    [string]$ClientSecret
)

# Get access token
$tokenUrl = "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token"
$body = @{
    grant_type    = "client_credentials"
    client_id     = $ClientId
    client_secret = $ClientSecret
    scope         = "https://graph.microsoft.com/.default"
}

try {
    $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method POST -Body $body
    Write-Host "✓ Token acquired successfully" -ForegroundColor Green
    
    # Test API call
    $headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }
    $org = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/organization" -Headers $headers
    
    Write-Host "✓ Connected to: $($org.value[0].displayName)" -ForegroundColor Green
    Write-Host "✓ Verification PASSED!" -ForegroundColor Green
}
catch {
    Write-Host "✗ Verification FAILED: $_" -ForegroundColor Red
    exit 1
}
```

### Method 2: Manual Verification Steps

1. **Check token endpoint:**
   ```bash
   curl -X POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token \
     -d "grant_type=client_credentials" \
     -d "client_id={your-client-id}" \
     -d "client_secret={your-secret}" \
     -d "scope=https://graph.microsoft.com/.default"
   ```

2. **Verify API access:**
   ```bash
   curl https://graph.microsoft.com/v1.0/organization \
     -H "Authorization: Bearer {access-token}"
   ```

### Expected Results

| Check | Expected Result |
|-------|-----------------|
| Token Request | HTTP 200 with access_token |
| Organization Endpoint | Returns tenant details |
| Reports Endpoint | Returns available reports |
| Security Events | Returns security events (may be empty) |

---

## Troubleshooting

### Common Issues

#### Issue: "Insufficient privileges to complete the operation"

**Cause:** Admin consent not granted

**Solution:**
1. Go to API permissions
2. Click "Grant admin consent for [Tenant]"
3. Confirm the action

---

#### Issue: "The user or administrator has not consented to use the application"

**Cause:** Application permissions require admin consent

**Solution:**
Same as above - grant admin consent for all requested permissions.

---

#### Issue: "Invalid client secret provided"

**Cause:** Secret copied incorrectly or expired

**Solution:**
1. In Certificates & secrets, create a new secret
2. Copy the **Value** (not Secret ID) immediately
3. Update your configuration

---

#### Issue: "Application is not assigned to a role"

**Cause:** Service principal not created

**Solution:**
1. Go to Enterprise Applications
2. Find your app
3. Verify Status is Enabled

---

#### Issue: Cannot find "Grant admin consent" button

**Cause:** User doesn't have Global Admin role

**Solution:**
- Verify you have Global Administrator role
- Contact your Azure AD administrator
- Or use the PowerShell script with proper credentials

---

### Debug Commands

```powershell
# Check your current context
Get-MgContext

# List all app registrations
Get-MgApplication -Filter "displayName eq 'Riverside-Governance-Platform'"

# Check service principal
Get-MgServicePrincipal -Filter "appId eq 'YOUR-CLIENT-ID'"

# List assigned permissions
Get-MgServicePrincipalAppRoleAssignment -ServicePrincipalId (Get-MgServicePrincipal -Filter "appId eq 'YOUR-CLIENT-ID'").Id
```

---

## Security Checklist

Before considering setup complete:

- [ ] Client secrets stored in Azure Key Vault (not in code/config files)
- [ ] `.env` files added to `.gitignore`
- [ ] Expiration dates documented in calendar
- [ ] Access reviewed and documented
- [ ] Backup admin contact identified
- [ ] Principle of least privilege verified

### Key Vault Storage (Recommended)

```powershell
# Store secret in Key Vault
$secureSecret = ConvertTo-SecureString -String "your-secret" -AsPlainText -Force
Set-AzKeyVaultSecret -VaultName "riverside-kv-governance" -Name "riverside-htt-client-secret" -SecretValue $secureSecret

# Retrieve in application
$secret = Get-AzKeyVaultSecret -VaultName "riverside-kv-governance" -Name "riverside-htt-client-secret"
$plainSecret = $secret.SecretValue | ConvertFrom-SecureString -AsPlainText
```

---

## Quick Reference Card

### App Registration Settings

| Setting | Value |
|---------|-------|
| Name | `Riverside-Governance-Platform` |
| Account Type | Single tenant |
| Platform | None (daemon app) |

### Required Permissions

| API | Permission | Admin Consent |
|-----|------------|---------------|
| Microsoft Graph | Reports.Read.All | Required |
| Microsoft Graph | SecurityEvents.Read.All | Required |
| Microsoft Graph | Domain.Read.All | Required |
| Microsoft Graph | Directory.Read.All | Required |

### Support Contacts

| Issue | Contact |
|-------|---------|
| Azure AD Access | Global Admin |
| Key Vault Access | Azure Subscription Owner |
| Application Issues | Riverside DevOps Team |

---

## Appendix: Permission Details

### Reports.Read.All
- **Description:** Read all usage reports
- **Purpose:** Access Microsoft 365 activity reports
- **Risk:** Low (read-only, no sensitive data)

### SecurityEvents.Read.All
- **Description:** Read your organization's security events
- **Purpose:** Monitor security incidents and alerts
- **Risk:** Low-Medium (security metadata only)

### Domain.Read.All
- **Description:** Read domains in the tenant
- **Purpose:** Enumerate registered domains
- **Risk:** Low (public information)

### Directory.Read.All
- **Description:** Read directory data
- **Purpose:** Read users, groups, and other directory objects
- **Risk:** Medium (sensitive organizational data)

---

> 📅 **Document Version:** 1.0  
> 📝 **Last Updated:** 2024  
> 👤 **Author:** Riverside DevOps  
> 🔒 **Classification:** Internal Use Only
