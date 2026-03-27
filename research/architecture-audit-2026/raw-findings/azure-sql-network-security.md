# Azure SQL Public Network Access — Raw Findings

## Current Project Configuration

### File: `infrastructure/modules/sql-server.bicep`
```bicep
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  properties: {
    publicNetworkAccess: 'Enabled'           // ⚠️ SECURITY ISSUE
    restrictOutboundNetworkAccess: 'Disabled' // ⚠️ No outbound restrictions
    minimalTlsVersion: '1.2'                 // ✅ Correct
  }
}

// This rule allows ANY Azure service globally
resource allowAzureServices 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = {
  name: 'AllowAllAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'   // ⚠️ Allows all Azure IPs
    endIpAddress: '0.0.0.0'
  }
}
```

### File: `infrastructure/main.bicep`
```bicep
param enableVNetIntegration bool = false    // ⚠️ VNet disabled by default
```

## Microsoft Official Recommendations (March 2026)

### Azure Security Benchmark v3 — NS-2: Secure cloud services with network controls
- **Recommendation**: "Disable public network access to Azure SQL Database by setting publicNetworkAccess to Disabled"
- **Azure Policy**: `Azure SQL Database should have public network access disabled` (built-in policy)
- **Microsoft Defender for Cloud**: Flags public network access as a security finding

### Azure Private Link Documentation Warning
> **Important**: When you add a private endpoint connection, public routing to your logical 
> server isn't blocked by default. In the Firewall and virtual networks pane, the setting 
> **Deny public network access** isn't selected by default. To disable public network access, 
> ensure that you select **Deny public network access**.

### What `AllowAllAzureIps (0.0.0.0)` Actually Allows
This firewall rule permits connections from:
- ✅ Your App Service in the same subscription
- ⚠️ Any Azure VM in ANY subscription globally
- ⚠️ Any Azure App Service in ANY subscription globally  
- ⚠️ Any Azure Function in ANY subscription globally
- ⚠️ Compromised Azure resources anywhere in the Azure cloud

This is NOT limited to the project's subscription, resource group, or VNet.

## Recommended Architecture

### Target State
```
[App Service B1] → [VNet Integration] → [Private Endpoint] → [Azure SQL]
                                                                    ↑
                                                    publicNetworkAccess: 'Disabled'
```

### Required Bicep Changes

1. **Enable VNet integration** (main.bicep): `enableVNetIntegration = true`
2. **Create Private Endpoint** for SQL Server
3. **Create Private DNS Zone** (`privatelink.database.windows.net`)
4. **Set `publicNetworkAccess: 'Disabled'`**
5. **Remove `AllowAllAzureIps` firewall rule**

### Cost Impact
| Resource | Monthly Cost |
|----------|-------------|
| Private Endpoint | Free |
| VNet | Free |
| Private DNS Zone | ~$0.50/month |
| VNet Integration (B1) | Already included in B1 plan |
| **Total additional** | **~$0.50/month** |

### Migration Risk
- **Order matters**: Enable VNet integration and Private Endpoint BEFORE disabling public access
- **DNS resolution**: App Service must resolve `*.database.windows.net` to the private IP
- **Connection string**: No changes needed — same FQDN resolves to private IP via Private DNS
- **Testing**: Use `nslookup` from App Service console to verify private DNS resolution
