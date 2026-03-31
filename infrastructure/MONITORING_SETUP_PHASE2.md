# Phase 2 Infrastructure: Application Insights & Log Analytics Setup

## Summary

Successfully implemented monitoring infrastructure for Azure Governance Platform production environment.

## Resources Created

### 1. Application Insights
- **Name**: `governance-appinsights`
- **Location**: `westus2`
- **Type**: Web Application
- **Instrumentation Key**: `ebdd7066-8502-4b03-91cd-f54c80bcade2`
- **Application ID**: `governance-appinsights`
- **AppId**: `6c3ba2a4-7e3e-48c3-b231-8287ead9dd0a`
- **Workspace**: Linked to `governance-logs` Log Analytics workspace
- **Connection String**: 
  ```
  InstrumentationKey=ebdd7066-8502-4b03-91cd-f54c80bcade2;IngestionEndpoint=https://westus2-2.in.applicationinsights.azure.com/;LiveEndpoint=https://westus2.livediagnostics.monitor.azure.com/;ApplicationId=6c3ba2a4-7e3e-48c3-b231-8287ead9dd0a
  ```

### 2. Log Analytics Workspace
- **Name**: `governance-logs`
- **Location**: `westus2`
- **Customer ID**: `d4b9bec8-0ec4-4c9c-929d-e94fe94851dc`
- **Resource Group**: `rg-governance-production`
- **Retention**: 30 days
- **Provisioning State**: Succeeded
- **Network Access**: Enabled for both ingestion and query

### 3. Key Vault Secret
- **Vault**: `kv-gov-prod`
- **Secret Name**: `app-insights-connection`
- **Status**: Enabled
- **Purpose**: Stores Application Insights connection string for secure access

## App Service Configuration

The production App Service (`app-governance-prod`) has been configured with:

| Setting | Value | Purpose |
|---------|-------|---------|
| `APPINSIGHTS_INSTRUMENTATIONKEY` | `ebdd7066-8502-4b03-91cd-f54c80bcade2` | Instrumentation key for App Insights |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Full connection string | Complete connection string |
| `ApplicationInsightsAgent_EXTENSION_VERSION` | `~2` | Enables App Insights agent extension |

### Diagnostic Logging Configuration
- **Application Logging**: Enabled (FileSystem, Verbose level)
- **Detailed Error Messages**: Enabled
- **Failed Request Tracing**: Enabled
- **HTTP Logs**: Enabled (FileSystem, 3-day retention, 100MB limit)

## Monitoring URLs

### Application Insights Portal
```
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.Insights/components/governance-appinsights/overview
```

### Log Analytics Workspace
```
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.OperationalInsights/workspaces/governance-logs/logs
```

### Application Insights - Live Metrics Stream
```
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.Insights/components/governance-appinsights/liveMetricsStream
```

### Application Insights - Application Map
```
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.Insights/components/governance-appinsights/applicationMap
```

### Log Analytics - Query Interface
```
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.OperationalInsights/workspaces/governance-logs/queryLogs
```

## Verification Commands

### Check App Insights Status
```bash
az monitor app-insights component show \
  --app governance-appinsights \
  --resource-group rg-governance-production
```

### Check Log Analytics Workspace
```bash
az monitor log-analytics workspace show \
  --name governance-logs \
  --resource-group rg-governance-production
```

### Check App Service Settings
```bash
az webapp config appsettings list \
  --name app-governance-prod \
  --resource-group rg-governance-production \
  --query "[?contains(name, 'APPINSIGHTS') || contains(name, 'ApplicationInsights')]"
```

### View Recent Logs in Log Analytics
```kusto
// Application Insights - Last 24 hours
requests
| where timestamp > ago(24h)
| summarize count() by name, resultCode
| order by count_ desc

// Exceptions
exceptions
| where timestamp > ago(24h)
| summarize count() by problemId
| order by count_ desc

// Performance - Average response time
requests
| where timestamp > ago(24h)
| summarize avg(duration) by name
| order by avg_duration desc
```

## Key Features Enabled

1. **Request Tracking**: All HTTP requests to the application are tracked
2. **Dependency Tracking**: External service calls are monitored
3. **Exception Logging**: Application exceptions are automatically captured
4. **Performance Metrics**: Response times, throughput, and availability
5. **Live Metrics**: Real-time monitoring during deployments
6. **Application Map**: Visual representation of service dependencies
7. **Smart Detection**: Automatic anomaly detection
8. **Alerting**: Can be configured for critical metrics

## Next Steps (Future Phases)

1. **Create Alert Rules**: Set up alerts for:
   - High error rates (> 5%)
   - Response time degradation (> 2s average)
   - Availability failures
   - Exception spikes

2. **Custom Dashboards**: Create monitoring dashboards in Azure Portal

3. **Availability Tests**: Set up multi-region availability monitoring

4. **Log-based Metrics**: Create custom metrics from log queries

5. **Workbooks**: Deploy Azure Monitor Workbooks for governance insights

## Notes

- Traffic has been generated to verify the monitoring is active
- All resources are in the same resource group: `rg-governance-production`
- All resources are in the same region: `westus2`
- The connection string is securely stored in Key Vault for rotation purposes
- The setup follows Azure best practices for production monitoring

## Resources Created

| Resource | Name | Type | Location |
|----------|------|------|----------|
| Application Insights | governance-appinsights | Microsoft.Insights/components | westus2 |
| Log Analytics Workspace | governance-logs | Microsoft.OperationalInsights/workspaces | westus2 |
| Key Vault Secret | app-insights-connection | Microsoft.KeyVault/vaults/secrets | westus2 |

---

**Setup Date**: 2026-03-31
**Status**: ✅ Complete
**Next Phase**: Alert configuration and custom dashboards
