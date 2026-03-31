# Azure Monitor Workbooks

Custom dashboards for the Azure Governance Platform using Azure Monitor Workbooks.

## Available Workbooks

### governance-dashboard.json
A comprehensive monitoring dashboard for the Azure Governance Platform with the following features:

**Overview Tab:**
- Real-time status tiles showing total tenants, healthy syncs, failed syncs, and active alerts
- Operations timeline chart showing activity across all tenants

**Sync Status Tab:**
- Detailed sync status table by tenant and sync type
- Success/failure rates with visual indicators
- Average sync duration metrics
- Pie chart showing sync distribution by type

**Cost Analysis Tab:**
- Cost summary table by tenant with total, average daily, and max daily costs
- Daily cost trends visualization
- Automatic currency formatting

**Compliance Tab:**
- Compliance scorecard with letter grades (A-F)
- Framework-specific compliance tracking
- Color-coded compliance scores
- Trends over time

**Tenant Health Tab:**
- Real-time health status (Healthy/Degraded/Unhealthy)
- Response time monitoring
- Error rate tracking
- Recent errors table with severity levels

## Deployment

### Via Azure Portal
1. Navigate to Azure Monitor > Workbooks
2. Click "New"
3. Click "Advanced Editor" (</> icon)
4. Paste the JSON content from `governance-dashboard.json`
5. Click "Apply"
6. Save to desired location (subscription/resource group)

### Via Azure CLI
```bash
# Deploy workbook
az monitor workbook create \
  --category "workbook" \
  --display-name "Azure Governance Platform Dashboard" \
  --serialized-data @governance-dashboard.json \
  --resource-group "rg-governance-monitoring" \
  --location "eastus"
```

### Via Bicep
```bicep
module workbook './workbook.bicep' = {
  name: 'governance-workbook'
  params: {
    name: 'governance-dashboard'
    displayName: 'Azure Governance Platform Dashboard'
    serializedData: loadJsonContent('governance-dashboard.json')
    location: location
  }
}
```

## Prerequisites

- Log Analytics workspace with governance platform logs
- Proper permissions on the workspace
- Log data flowing from the governance platform application

## Log Schema

The workbook expects the following custom dimensions in AppTraces:

| Field | Description | Example |
|-------|-------------|---------|
| `TenantId` | Target tenant identifier | `contoso.onmicrosoft.com` |
| `SyncType` | Type of sync operation | `identity`, `compliance`, `costs` |
| `Cost` | Cost value for cost logs | `1234.56` |
| `Currency` | Currency code | `USD` |
| `ComplianceFramework` | Framework being checked | `SOC2`, `NIST-CSF` |
| `ComplianceScore` | Compliance percentage | `85.5` |
| `ResponseTime` | API response time in ms | `250` |
| `OperationName` | Operation being performed | `SyncIdentity` |

## Customization

### Adding New Panels
1. Edit the JSON template
2. Add a new item in the appropriate section
3. Define KQL query for your data
4. Set visualization type (table, chart, tiles, etc.)

### Modifying Thresholds
Update the `thresholdsGrid` in formatter configurations:
```json
{
  "operator": ">=",
  "thresholdValue": "90",
  "representation": "green"
}
```

### Adding New Parameters
Add to the parameters section:
```json
{
  "id": "new-parameter",
  "version": "KqlParameterItem/1.0",
  "name": "NewParameter",
  "type": 1,
  "isRequired": true
}
```

## Sharing

Workbooks can be shared with:
- Individual users (via Azure RBAC)
- Entire resource groups
- Azure AD groups
- Scoped to specific subscriptions

## Refresh Rates

- Tables: Manual or on-demand
- Charts: Auto-refresh every 5 minutes
- Status tiles: Auto-refresh every 1 minute

## Troubleshooting

**No data showing:**
- Verify logs are flowing to Log Analytics
- Check time range parameter
- Confirm tenant selector includes your tenants

**Permission errors:**
- Ensure you have Reader access to the Log Analytics workspace
- Check workbook resource group permissions

**Query errors:**
- Verify field names match your log schema
- Check for case sensitivity in KQL queries
