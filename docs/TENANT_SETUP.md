# Azure Tenant Setup Guide for DMARC/DKIM Monitoring

This guide walks through setting up Azure AD app registrations for Tyler's 5 Riverside tenants to enable DMARC/DKIM monitoring through the Azure Governance Platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Tenant Overview](#tenant-overview)
3. [App Registration Setup](#app-registration-setup)
4. [Graph API Permissions](#graph-api-permissions)
5. [Client Secrets & Key Vault](#client-secrets--key-vault)
6. [Admin Consent](#admin-consent)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- **Global Admin** access to all Riverside tenants
- **Azure PowerShell** or **Azure CLI** installed
- **Azure Key Vault** in your primary managing tenant
- The **Azure Governance Platform** deployed and running

### Required Tools

```powershell
# Install Azure PowerShell modules
Install-Module -Name Az -AllowClobber -Force -Scope CurrentUser

# Or install Azure CLI
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
```

---

## Tenant Overview

| Code | Name | Tenant ID | Admin Email | Status |
|------|------|-----------|-------------|--------|
| HTT | Head-To-Toe | `0c0e35dc-188a-4eb3-b8ba-61752154b407` | tyler.granlund-admin@httbrands.com | Active |
| BCC | Bishops | `b5380912-79ec-452d-a6ca-6d897b19b294` | tyler.granlund-Admin@bishopsbs.onmicrosoft.com | Active |
| FN | Frenchies | `98723287-044b-4bbb-9294-19857d4128a0` | tyler.granlund-Admin@ftgfrenchiesoutlook.onmicrosoft.com | Active |
| TLL | Lash Lounge | `3c7d2bf3-b597-4766-b5cb-2b489c2904d6` | tyler.granlund-Admin@LashLoungeFranchise.onmicrosoft.com | Active |
| DCE | Delta Crown Extensions | TBD | tyler.granlund-Admin@deltacrownextensions.onmicrosoft.com | Pending |

---

## App Registration Setup

For each tenant, create an app registration to enable API access for DMARC/DKIM monitoring.

### Method 1: Azure Portal (Recommended for first setup)

1. **Sign in to Azure Portal** (https://portal.azure.com) with Global Admin credentials

2. **Navigate to Azure Active Directory** > **App registrations**

3. **Click "New registration"**

4. **Configure the app:**
   - **Name:** `Azure Governance Platform - DMARC/DKIM`
   - **Supported account types:** `Accounts in this organizational directory only (Single tenant)`
   - **Redirect URI:** Leave blank (not needed for daemon apps)

5. **Click "Register"**

6. **Copy the Application (client) ID** - you'll need this for the configuration

7. **Copy the Directory (tenant) ID** - verify it matches the table above

### Method 2: PowerShell (For automation)

```powershell
# Connect to the tenant
Connect-AzAccount -TenantId "0c0e35dc-188a-4eb3-b8ba-61752154b407"

# Create the app registration
$AppRegistration = New-AzADApplication `
    -DisplayName "Azure Governance Platform - DMARC/DKIM" `
    -SignInAudience "AzureADMyOrg"

# Create a service principal
$ServicePrincipal = New-AzADServicePrincipal `
    -ApplicationId $AppRegistration.AppId

# Output the IDs
Write-Host "Application ID: $($AppRegistration.AppId)"
Write-Host "Tenant ID: $((Get-AzContext).Tenant.Id)"
```

---

## Graph API Permissions

The app requires the following **Application** permissions (not Delegated):

| Permission | Description | Why It's Needed |
|------------|-------------|-----------------|
| `Reports.Read.All` | Read all usage reports | Access email authentication reports for DMARC/DKIM analysis |
| `SecurityEvents.Read.All` | Read security events | Monitor security alerts related to email spoofing |
| `Domain.Read.All` | Read all domains | Verify custom domain configuration for DKIM |
| `Directory.Read.All` | Read directory data | Read organization and user context |

### Add Permissions via Portal

1. Go to your app registration
2. Click **API permissions** > **Add a permission**
3. Select **Microsoft Graph** > **Application permissions**
4. Search for and add each permission:
   - `Reports.Read.All`
   - `SecurityEvents.Read.All`
   - `Domain.Read.All`
   - `Directory.Read.All`

### Add Permissions via PowerShell

```powershell
# Define required permissions
$RequiredPermissions = @(
    "230c1aed-a721-4c5d-9cb4-a90514e508ef"  # Reports.Read.All
    "bf394140-e372-4bf9-a898-299cfc7564e5"  # SecurityEvents.Read.All
    "dbb9058a-0e50-4048-992f-029bf1600b55"  # Domain.Read.All
    "7ab1d382-f21e-4acd-a863-ba3e13f7da61"  # Directory.Read.All
)

# Get the service principal for Microsoft Graph
$GraphServicePrincipal = Get-AzADServicePrincipal -ApplicationId "00000003-0000-0000-c000-000000000000"

# Add each permission
foreach ($PermissionId in $RequiredPermissions) {
    $ResourceAccess = New-Object -TypeName "Microsoft.Open.AzureAD.Model.ResourceAccess" -ArgumentList $PermissionId, "Role"
    $RequiredResourceAccess = New-Object -TypeName "Microsoft.Open.AzureAD.Model.RequiredResourceAccess"
    $RequiredResourceAccess.ResourceAppId = $GraphServicePrincipal.AppId
    $RequiredResourceAccess.ResourceAccess = $ResourceAccess
    
    # Apply to app registration
    Set-AzureADApplication -ObjectId $AppRegistration.ObjectId -RequiredResourceAccess @($RequiredResourceAccess)
}
```

---

## Client Secrets & Key Vault

### Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. **Description:** `Governance Platform Secret`
4. **Expires:** Select 24 months (or per your security policy)
5. Click **Add**

**IMPORTANT:** Copy the secret value immediately - you won't see it again!

### Store in Azure Key Vault

For production, store secrets in Azure Key Vault:

```powershell
# Variables
$KeyVaultName = "riverside-kv"  # Your Key Vault name
$TenantCode = "htt"             # htt, bcc, fn, tll, dce
$SecretValue = "your-secret-here"

# Convert to secure string
$SecureSecret = ConvertTo-SecureString -String $SecretValue -AsPlainText -Force

# Store in Key Vault
Set-AzKeyVaultSecret `
    -VaultName $KeyVaultName `
    -Name "$TenantCode-client-secret" `
    -SecretValue $SecureSecret
```

### Secret Naming Convention

| Tenant | Key Vault Secret Name |
|--------|----------------------|
| HTT | `htt-client-secret` |
| BCC | `bcc-client-secret` |
| FN | `fn-client-secret` |
| TLL | `tll-client-secret` |
| DCE | `dce-client-secret` |

---

## Admin Consent

After adding permissions, you must grant **Admin Consent** for the application to access the data.

### Via Portal

1. Go to **API permissions** in your app registration
2. Click **Grant admin consent for [Your Organization]**
3. Confirm by clicking **Yes**

You should see green checkmarks next to all permissions.

### Via PowerShell

```powershell
# Grant admin consent using Microsoft Graph PowerShell
Connect-MgGraph -Scopes "Application.ReadWrite.All", "Directory.Read.All"

$ServicePrincipalId = $ServicePrincipal.Id
$ResourceId = $GraphServicePrincipal.Id

# Grant consent for each permission
foreach ($PermissionId in $RequiredPermissions) {
    $Params = @{
        ClientId = $ServicePrincipalId
        ConsentType = "AllPrincipals"
        ResourceId = $ResourceId
        Scope = $PermissionId
    }
    
    New-MgOAuth2PermissionGrant @Params
}
```

### Verify Consent

```powershell
# Check granted permissions
Get-AzureADServicePrincipalOAuth2PermissionGrant -ObjectId $ServicePrincipal.ObjectId
```

---

## Verification

### PowerShell Verification Script

Run the provided verification script:

```powershell
# Navigate to the scripts directory
cd scripts

# Run verification for all tenants
.\verify-tenant-access.ps1

# Or verify a specific tenant
.\verify-tenant-access.ps1 -TenantCode HTT

# Include Graph API testing
.\verify-tenant-access.ps1 -TestGraphCalls

# Use Key Vault for secrets
.\verify-tenant-access.ps1 -KeyVaultName "riverside-kv" -TestGraphCalls
```

### Manual Verification

```powershell
# Get access token
$TenantId = "0c0e35dc-188a-4eb3-b8ba-61752154b407"
$AppId = "e1dfb17f-b695-4dad-92c0-20e26ce069ab"
$ClientSecret = "your-secret"

$Body = @{
    grant_type = "client_credentials"
    client_id = $AppId
    client_secret = $ClientSecret
    scope = "https://graph.microsoft.com/.default"
}

$TokenResponse = Invoke-RestMethod `
    -Uri "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token" `
    -Method Post `
    -Body $Body

$AccessToken = $TokenResponse.access_token

# Test Graph API call
$Headers = @{
    Authorization = "Bearer $AccessToken"
}

# Get organization info
Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/organization" `
    -Headers $Headers

# Get domains
Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/domains" `
    -Headers $Headers

# Get security alerts
Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/security/alerts" `
    -Headers $Headers
```

---

## Troubleshooting

### Common Issues

#### "Insufficient privileges to complete the operation"

**Cause:** Admin consent not granted  
**Solution:** Grant admin consent for all API permissions

#### "Invalid client secret provided"

**Cause:** Secret expired or incorrect  
**Solution:** Create a new secret in the app registration and update Key Vault

#### "The identity of the calling application could not be established"

**Cause:** App registration doesn't exist in the target tenant  
**Solution:** Verify you're connecting to the correct tenant ID

#### "Access token is empty or null"

**Cause:** Incorrect tenant ID, app ID, or secret  
**Solution:** Verify all credentials match the configuration

### Diagnostic Commands

```powershell
# Verify app registration exists
Get-AzADApplication -ApplicationId "e1dfb17f-b695-4dad-92c0-20e26ce069ab"

# Check service principal
Get-AzADServicePrincipal -ApplicationId "e1dfb17f-b695-4dad-92c0-20e26ce069ab"

# List granted permissions
Get-AzureADServicePrincipalOAuth2PermissionGrant `
    -ObjectId (Get-AzADServicePrincipal -ApplicationId "e1dfb17f-b695-4dad-92c0-20e26ce069ab").Id

# Check Key Vault secret
Get-AzKeyVaultSecret -VaultName "riverside-kv" -Name "htt-client-secret"
```

---

## Security Best Practices

### 1. Least Privilege

- Only request the minimum permissions needed
- Regularly audit granted permissions
- Remove unused app registrations

### 2. Secret Management

- Store secrets in Key Vault, never in code
- Set secret expiration reminders
- Rotate secrets every 90-180 days
- Use certificate-based auth when possible

### 3. Monitoring

- Enable audit logs for app registrations
- Monitor for unusual API activity
- Set up alerts for authentication failures

### 4. Network Security

- Restrict Key Vault access with VNet/service endpoints
- Use managed identities where possible
- Enable Key Vault soft-delete and purge protection

---

## Next Steps

After completing setup:

1. Run the verification script: `scripts/verify-tenant-access.ps1`
2. Initialize database entries: `python scripts/setup-tenants.py --init`
3. Configure the governance platform: Update `.env` with Key Vault URL
4. Test DMARC/DKIM data collection
5. Set up monitoring alerts

For support, see:
- [Microsoft Graph Permissions Reference](https://docs.microsoft.com/en-us/graph/permissions-reference)
- [Azure AD App Registration Docs](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Key Vault Best Practices](https://docs.microsoft.com/en-us/azure/key-vault/general/best-practices)
