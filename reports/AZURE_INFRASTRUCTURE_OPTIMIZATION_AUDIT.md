# Azure Infrastructure Optimization Audit Report

**Date:** 2026-03-27  
**Subscription:** HTT-CORE (32a28177-6fb2-4668-a528-6d6cafb9665e)  
**Resource Group:** rg-governance-production  
**Auditor:** Husky Infrastructure Audit Bot

---

## Executive Summary

**Overall Status:** 🟡 Needs Attention  
**Critical Issues:** 5  
**High Priority:** 8  
**Cost Savings Potential:** ~$45-75/month

---

## 1. App Service Configuration Review

### Current State

| Setting | Current Value | Recommended | Status |
|---------|---------------|-------------|--------|
| **Always On** | ❌ `False` | ✅ `True` | 🔴 **CRITICAL** |
| **HTTPS Only** | ❌ `False` | ✅ `True` | 🔴 **CRITICAL** |
| **Min TLS Version** | ✅ `1.2` | `1.2` | 🟢 Good |
| **HTTP 2.0** | ✅ `Enabled` | `Enabled` | 🟢 Good |
| **FTPS State** | ✅ `FtpsOnly` | `FtpsOnly` | 🟢 Good |
| **32-bit Worker** | ❌ `True` | `False` | 🟡 Should be 64-bit |
| **Workers** | `1` | `1` | 🟢 Fine for B1 |
| **Health Check Path** | ❌ Not set | `/health` | 🟡 Missing |
| **Client Affinity** | ❌ `Enabled` | `Disabled` | 🟡 Unnecessary for Docker |

### App Service Plan

| Attribute | Current | Notes |
|-----------|---------|-------|
| **SKU** | B1 (Basic) | Cost-optimized for current load |
| **Tier** | Linux | Correct for Docker containers |
| **Workers** | 1 | Cannot scale beyond 1 in B1 |
| **Per-site Scaling** | N/A | Not available in Basic tier |
| **Auto-scaling** | ❌ Not configured | Not available in Basic tier |

### Docker Configuration

| Setting | Value | Status |
|---------|-------|--------|
| **Image** | `acrgovprod.azurecr.io/azure-governance-platform:latest` | 🟢 Correct |
| **Tag** | `latest` | 🟡 Consider version pinning |

### 🔴 Critical Issues (App Service)

#### 1. **Always On = False** - CRITICAL
**Risk:** App goes to sleep after idle period, causing cold start delays (5-30s)  
**Impact:** Poor user experience, timeouts on first requests  
**Fix:**
```bash
az webapp config set --name app-governance-prod \
  --resource-group rg-governance-production \
  --always-on true
```

#### 2. **HTTPS Only = False** - CRITICAL
**Risk:** HTTP traffic allowed, potential for MITM attacks  
**Impact:** Security vulnerability, compliance issues  
**Fix:**
```bash
az webapp update --name app-governance-prod \
  --resource-group rg-governance-production \
  --https-only true
```

#### 3. **32-bit Worker Process**
**Risk:** Limited memory (1.5GB vs 3.5GB for 64-bit), potential OOM  
**Fix:**
```bash
az webapp config set --name app-governance-prod \
  --resource-group rg-governance-production \
  --use-32bit-worker-process false
```

---

## 2. Azure SQL Database Optimization Review

### Current State (Active Server: sql-gov-prod-mylxq53d)

| Attribute | Value | Status |
|-----------|-------|--------|
| **Edition** | Standard | 🟢 Correct |
| **Tier** | S0 | 🟢 Cost-optimized |
| **Max Size** | 250 GB | 🟢 Appropriate |
| **Zone Redundant** | False | 🟡 Expected for S0 |
| **Read Scale** | Disabled | 🟡 OK for current load |
| **TLS Version** | 1.2 | 🟢 Good |
| **Public Network** | Enabled | 🟡 Security consideration |
| **Restore Point** | 3 days available | 🟢 Good |

### Firewall Rules Analysis

- **27 IP rules configured** - All App Service outbound IPs
- **2 temporary rules** (`TempFinal`, `TempVerify`) - Should be removed
- **Pattern:** Using IP rules instead of managed identity/private endpoint

### 🔴 Critical Issues (SQL)

#### 1. **Orphaned SQL Server: sql-governance-prod**
**Status:** Has active S2-tier database costing ~$30/month unused!  

| Resource | State | Cost Impact |
|----------|-------|-------------|
| `sql-governance-prod/governance` | Online, S2 | ~$30/mo wasted |

**Fix - Migrate data if needed, then delete:**
```bash
# First verify no connections
az sql db show-connection-string --client ado.net --server sql-governance-prod --name governance

# Backup and migrate if needed, then delete
az sql db delete --name governance --server sql-governance-prod \
  --resource-group rg-governance-production --yes

az sql server delete --name sql-governance-prod \
  --resource-group rg-governance-production --yes
```

#### 2. **Temporary Firewall Rules**
```bash
# Remove temporary rules
az sql server firewall-rule delete --server sql-gov-prod-mylxq53d \
  --resource-group rg-governance-production --name TempFinal

az sql server firewall-rule delete --server sql-gov-prod-mylxq53d \
  --resource-group rg-governance-production --name TempVerify
```

#### 3. **Public Network Access Enabled**
**Recommendation:** Consider private endpoint for production

---

## 3. Key Vault Security Review

### Current State

| Setting | Current | Recommended | Status |
|---------|---------|-------------|--------|
| **Soft Delete** | ✅ `Enabled` | `Enabled` | 🟢 Good |
| **Purge Protection** | ❓ Check | `Enabled` | 🟡 Verify |
| **RBAC Authorization** | ❌ `Disabled` | `Enabled` | 🟡 Migration opportunity |
| **SKU** | Standard | Standard | 🟢 Fine |
| **Public Network** | Enabled | Disabled + rules | 🔴 Security gap |
| **Network Rules** | None configured | Restrict IPs | 🔴 Open to all |
| **Diagnostic Settings** | ❌ None | Enable logging | 🔴 Compliance gap |

### 🔴 Critical Issues (Key Vault)

#### 1. **No Network Restrictions**
**Risk:** Key Vault accessible from any IP address  
**Fix:**
```bash
# Add network rules (example)
az keyvault network-rule add --name kv-gov-prod \
  --resource-group rg-governance-production \
  --ip-address 20.115.232.20  # App Service IP

# Set default action to Deny
az keyvault update --name kv-gov-prod \
  --resource-group rg-governance-production \
  --default-action Deny
```

#### 2. **No Diagnostic Logging**
**Risk:** Cannot audit key access, compliance issues  
**Fix:** Enable diagnostic settings to Log Analytics (create workspace first)

#### 3. **Access Policies vs RBAC**
**Recommendation:** Migrate to RBAC for better security management

---

## 4. Container Registry Review

### Current State

| Setting | Current | Status |
|---------|---------|--------|
| **SKU** | Standard | 🟢 Good |
| **Admin User** | ✅ Enabled | 🔴 Security risk |
| **Anonymous Pull** | ✅ Disabled | 🟢 Good |
| **Data Endpoint** | Disabled | 🟢 OK |
| **Public Network** | Enabled | 🟡 Consider restricting |
| **Zone Redundancy** | Disabled | 🟢 Single region OK |
| **Trust Policy** | ❌ Disabled | 🟡 Enable for security |
| **Retention Policy** | ❌ Disabled | 🟡 Cost optimization |
| **ACR Tasks** | ❌ None | 🟡 Missing automation |

### Repository
- **azure-governance-platform** - Only repository (good)

### 🔴 Critical Issues (ACR)

#### 1. **Admin User Enabled** - CRITICAL
**Risk:** Username/password authentication bypasses Azure AD  
**Fix:**
```bash
az acr update --name acrgovprod \
  --resource-group rg-governance-production \
  --admin-enabled false
```
**Note:** Verify App Service uses managed identity before disabling!

#### 2. **No Content Trust Enabled**
```bash
az acr config content-trust update --name acrgovprod \
  --resource-group rg-governance-production \
  --enabled true
```

#### 3. **No Retention Policy**
**Cost Impact:** Old images accumulate storage costs  
```bash
az acr config retention update --name acrgovprod \
  --resource-group rg-governance-production \
  --status enabled --days 30
```

#### 4. **No ACR Tasks for Automated Builds**
**Missing:** Automated builds on GitHub push

---

## 5. Monitoring & Operations Gaps

### Missing Resources

| Resource | Status | Impact |
|----------|--------|--------|
| **Application Insights** | ❌ Not configured | No APM, no distributed tracing |
| **Log Analytics Workspace** | ❌ Not configured | No centralized logging |
| **Auto-scaling Rules** | ❌ Not available (B1 tier) | Manual scaling only |
| **Backup Configuration** | ❌ Not configured | No custom backups |
| **VNet Integration** | ❌ Not configured | Public endpoint exposure |
| **Managed Identity** | ❌ Not confirmed | Credential management |

### Monitoring Recommendations

1. **Enable App Insights:**
```bash
# Add to Bicep/ARM template
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'ai-governance-prod'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}
```

2. **Create Log Analytics Workspace:**
```bash
az monitor log-analytics workspace create \
  --resource-group rg-governance-production \
  --name log-governance-prod \
  --location eastus \
  --sku PerGB2018
```

---

## 6. Cost Optimization Opportunities

### Immediate Savings (~$30-45/month)

| Optimization | Current | Savings | Action |
|--------------|---------|---------|--------|
| **Delete orphaned SQL server** | S2 ($30/mo) | ~$30/mo | 🔴 **URGENT** |
| **Enable ACR retention policy** | Unbounded growth | ~$5/mo | Archive old images |
| **Disable client affinity** | Unnecessary | Negligible | Cleanup |
| **Remove temp firewall rules** | Cleanup | - | Maintenance |

### Future Considerations

| Current | Potential | Condition |
|---------|-----------|-----------|
| B1 ($13/mo) | S1 ($35/mo) | If traffic > 10K requests/day |
| S0 ($15/mo) | S1 ($30/mo) | If DTU > 40% consistently |
| Standard ACR ($5/mo) | Basic ($0) | If only 1-2 images |

---

## 7. Security Hardening Checklist

### High Priority (Do This Week)

- [ ] **Enable Always On** - Production reliability
- [ ] **Enable HTTPS Only** - Security compliance
- [ ] **Disable ACR Admin User** - Replace with managed identity
- [ ] **Delete orphaned SQL server** - Cost + security
- [ ] **Remove temporary firewall rules** - Clean up
- [ ] **Enable Key Vault diagnostic logging** - Compliance

### Medium Priority (Do This Month)

- [ ] **Enable ACR content trust** - Image signing
- [ ] **Enable ACR retention policy** - Cost optimization
- [ ] **Configure Key Vault network rules** - Security
- [ ] **Add App Insights** - Operations visibility
- [ ] **Create Log Analytics workspace** - Centralized logging
- [ ] **Switch to 64-bit workers** - Performance

### Low Priority (Future)

- [ ] **Migrate SQL to private endpoint** - Network isolation
- [ ] **Enable VNet integration for App Service** - Network isolation
- [ ] **Configure ACR tasks** - Build automation
- [ ] **Migrate Key Vault to RBAC** - Access management
- [ ] **Enable SQL TDE** - Verify (should be on by default)

---

## 8. Recommended Configuration Scripts

### Quick Fix Script
```bash
#!/bin/bash
# azure-optimization-quick-fixes.sh

RG="rg-governance-production"
APP="app-governance-prod"
SQL_SERVER="sql-gov-prod-mylxq53d"
ACR="acrgovprod"

# App Service - Critical fixes
echo "Applying App Service fixes..."
az webapp config set --name $APP --resource-group $RG --always-on true
az webapp update --name $APP --resource-group $RG --https-only true
az webapp config set --name $APP --resource-group $RG --use-32bit-worker-process false

# SQL - Cleanup
echo "Removing temporary firewall rules..."
az sql server firewall-rule delete --server $SQL_SERVER --resource-group $RG --name TempFinal 2>/dev/null || true
az sql server firewall-rule delete --server $SQL_SERVER --resource-group $RG --name TempVerify 2>/dev/null || true

# ACR - Retention
echo "Enabling ACR retention policy..."
az acr config retention update --name $ACR --resource-group $RG --status enabled --days 30

echo "Quick fixes applied!"
```

### Pre-Admin-User-Disable Check
```bash
# Verify App Service uses managed identity for ACR
az webapp identity show --name app-governance-prod --resource-group rg-governance-production

# If no identity, assign one first
az webapp identity assign --name app-governance-prod --resource-group rg-governance-production

# Grant ACR pull permission to managed identity
ACR_ID=$(az acr show --name acrgovprod --resource-group rg-governance-production --query id -o tsv)
PRINCIPAL_ID=$(az webapp identity show --name app-governance-prod --resource-group rg-governance-production --query principalId -o tsv)

az role assignment create --assignee $PRINCIPAL_ID --scope $ACR_ID --role AcrPull
```

---

## 9. Terraform/Bicep Template Updates

### Recommended Bicep Changes

See `infrastructure/modules/app-service-optimized.bicep` - ensure it includes:

```bicep
// Add these properties to webApp resource
properties: {
  siteConfig: {
    alwaysOn: true
    http20Enabled: true
    ftpsState: 'FtpsOnly'
    minTlsVersion: '1.2'
    use32BitWorkerProcess: false
    healthCheckPath: '/health'
  }
  httpsOnly: true
  clientAffinityEnabled: false
}
```

---

## Summary Dashboard

### Resource Health Score

| Resource | Score | Issues |
|----------|-------|--------|
| **App Service** | 65/100 | Always On, HTTPS, 32-bit |
| **SQL Database** | 85/100 | Orphaned server, temp rules |
| **Key Vault** | 60/100 | Network open, no logging |
| **ACR** | 70/100 | Admin user, no retention |
| **Monitoring** | 20/100 | Missing App Insights, Log Analytics |
| **Overall** | **60/100** | Needs attention |

### Immediate Action Items

1. 🔴 **Delete orphaned SQL server** (sql-governance-prod) - Save $30/mo
2. 🔴 **Enable Always On** on App Service - Fix cold starts
3. 🔴 **Enable HTTPS Only** - Security compliance
4. 🟡 **Enable ACR retention policy** - Prevent storage bloat
5. 🟡 **Remove temp firewall rules** - Clean up

---

## Appendix: Commands Used

```bash
# App Service
az webapp show --name app-governance-prod --resource-group rg-governance-production
az appservice plan show --name asp-governance-production --resource-group rg-governance-production

# SQL
az sql db show --name governance --server sql-gov-prod-mylxq53d --resource-group rg-governance-production
az sql server show --name sql-gov-prod-mylxq53d --resource-group rg-governance-production

# Key Vault
az keyvault show --name kv-gov-prod
az keyvault network-rule list --name kv-gov-prod

# ACR
az acr show --name acrgovprod --resource-group rg-governance-production

# Resources
az resource list --resource-group rg-governance-production
```

---

*Report generated by Azure Infrastructure Optimization Audit*  
*Next audit recommended: 30 days*
