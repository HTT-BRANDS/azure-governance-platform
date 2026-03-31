# Phase 3 Infrastructure: Production Hardening with Monitoring & Observability

## Summary

Successfully implemented production hardening with comprehensive alerting and availability monitoring for Azure Governance Platform.

## Resources Created

### 1. Alert Rules (3 Critical Alerts)

| Alert Name | Severity | Condition | Evaluation | Window |
|------------|----------|-----------|------------|--------|
| **Server Errors - Critical** | 0 (Critical) | `requests/failed count > 10` | 1 minute | 5 minutes |
| **High Response Time - Warning** | 2 (Warning) | `requests/duration avg > 1000ms` | 1 minute | 5 minutes |
| **Availability Drop - Critical** | 0 (Critical) | `availabilityPercentage avg < 99%` | 1 minute | 5 minutes |

All alerts are configured to:
- **Resource Scope**: governance-appinsights Application Insights
- **Action Group**: governance-alerts (emails admin@httbrands.com)
- **Status**: Enabled
- **Tags**: Phase=phase3, with appropriate AlertType and Severity tags

### 2. Action Group

- **Name**: `governance-alerts`
- **Short Name**: `gov-alerts`
- **Email Recipients**: admin@httbrands.com
- **Schema**: Common Alert Schema enabled
- **Status**: Enabled

### 3. Availability Test (Ping Test)

- **Name**: `Production Health Check`
- **Type**: Ping test
- **Target**: https://app-governance-prod.azurewebsites.net/health
- **Frequency**: Every 5 minutes (300 seconds)
- **Timeout**: 30 seconds
- **Status**: Enabled
- **Retry**: Enabled

**Test Locations** (3 locations for geographic coverage):
- San Jose, CA (us-ca-sjc-azr)
- Miami, FL (us-fl-mia-edge)
- Ashburn, VA (us-va-ash-azr)

**Expected Response**:
- HTTP Method: GET
- Expected Status Code: 200
- Follow Redirects: Yes

## Alert Details

### Alert 1: Server Errors - Critical
```
Metric: requests/failed
Aggregation: Count
Threshold: > 10
Severity: 0 (Critical)
Purpose: Alert when server errors exceed 10 per minute
```

**Why this matters**: 5xx errors indicate server-side failures that affect user experience and may indicate application bugs, database connectivity issues, or infrastructure problems.

### Alert 2: High Response Time - Warning
```
Metric: requests/duration
Aggregation: Average
Threshold: > 1000ms
Severity: 2 (Warning)
Purpose: Alert when average response time exceeds 1 second
```

**Why this matters**: Slow response times degrade user experience and may indicate performance bottlenecks, database query issues, or resource constraints.

### Alert 3: Availability Drop - Critical
```
Metric: availabilityResults/availabilityPercentage
Aggregation: Average
Threshold: < 99%
Severity: 0 (Critical)
Purpose: Alert when availability drops below 99%
```

**Why this matters**: Availability is the most critical metric for production systems. Downtime affects all users and may violate SLAs.

## Resource IDs

```
Action Group:
/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/microsoft.insights/actionGroups/governance-alerts

Application Insights:
/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/microsoft.insights/components/governance-appinsights

Web Test:
/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/microsoft.insights/webtests/Production Health Check
```

## Portal URLs

### Alert Rules
```
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.Insights/metricAlerts/Server%20Errors%20-%20Critical
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.Insights/metricAlerts/High%20Response%20Time%20-%20Warning
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.Insights/metricAlerts/Availability%20Drop%20-%20Critical
```

### Action Group
```
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/microsoft.insights/actionGroups/governance-alerts
```

### Availability Test
```
https://portal.azure.com/#@/resource/subscriptions/32a28177-6fb2-4668-a528-6d6cafb9665e/resourceGroups/rg-governance-production/providers/Microsoft.Insights/webTests/Production%20Health%20Check
```

## Verification Commands

### List All Alert Rules
```bash
az monitor metrics alert list \
  --resource-group rg-governance-production \
  --query "[].{Name:name, Description:description, Severity:severity, Enabled:enabled}"
```

### Check Action Group
```bash
az monitor action-group show \
  --name governance-alerts \
  --resource-group rg-governance-production
```

### Check Availability Test
```bash
az monitor app-insights web-test show \
  --name "Production Health Check" \
  --resource-group rg-governance-production
```

### View Recent Alert History
```bash
az monitor activity-log list \
  --resource-group rg-governance-production \
  --query "[?contains(resourceId, 'metricAlerts')]"
```

## Alert Severity Levels

| Severity | Level | Response Time |
|----------|-------|---------------|
| 0 | Critical | Immediate |
| 1 | Error | Within 15 minutes |
| 2 | Warning | Within 1 hour |
| 3 | Informational | Next business day |
| 4 | Verbose | Log only |

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Governance Platform                 │
│                   app-governance-prod                        │
│                      (App Service)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Telemetry
                       ▼
        ┌──────────────────────────────┐
        │    Application Insights      │
        │   governance-appinsights     │
        └──────────────┬───────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌────────────┐ ┌─────────────┐ ┌────────────────┐
│   Alerts   │ │   Logs     │ │  Availability  │
│  (3 rules) │ │  (Kusto)   │ │    (ping)      │
└─────┬──────┘ └─────────────┘ └────────────────┘
      │
      │ Triggers
      ▼
┌─────────────────┐
│  Action Group   │
│ governance-    │
│   alerts        │
└────────┬────────┘
         │
         │ Email
         ▼
┌─────────────────┐
│ admin@httbrands │
│     .com        │
└─────────────────┘
```

## Deployment Script

The complete deployment was executed using:

```bash
./infrastructure/scripts/setup-phase3-monitoring.sh
```

Script location: `infrastructure/scripts/setup-phase3-monitoring.sh`

## Next Steps (Phase 4 Recommendations)

1. **Custom Dashboards**: Create Azure Monitor Workbooks for governance-specific metrics
2. **Log-Based Alerts**: Set up alerts based on Kusto queries for business logic errors
3. **Auto-Scaling**: Configure App Service auto-scaling based on response time metrics
4. **Additional Notification Channels**: Add Teams/Slack webhooks to action group
5. **Runbook Integration**: Link alerts to automated remediation runbooks
6. **Alert Tuning**: Monitor alert frequency and tune thresholds based on production data

## Cost Impact

| Resource | Monthly Cost (Estimated) |
|----------|---------------------------|
| Metric Alerts (3) | ~$3.00 |
| Availability Test (3 locations × 288 tests/day) | ~$5.00 |
| Action Group Notifications | Negligible |
| **Total** | **~$8.00/month** |

## Troubleshooting

### Alerts Not Firing
1. Check if Application Insights is receiving telemetry
2. Verify App Service has APPINSIGHTS_INSTRUMENTATIONKEY configured
3. Ensure alert conditions are appropriate for your traffic volume

### Email Not Received
1. Check spam/junk folders
2. Verify email address in action group
3. Test action group from Azure Portal

### Availability Test Failing
1. Verify /health endpoint returns 200
2. Check if health endpoint is accessible from public internet
3. Review timeout settings if health check takes longer than 30s

## Compliance & Security

- ✅ All alerts use secure email delivery
- ✅ No secrets in alert descriptions
- ✅ Resource tags applied for cost tracking
- ✅ Alert rules scoped to specific resources only
- ✅ Availability test does not expose sensitive data

## Resources Summary

| Resource Type | Name | Status |
|--------------|------|--------|
| Action Group | governance-alerts | ✅ Active |
| Metric Alert | Server Errors - Critical | ✅ Active |
| Metric Alert | High Response Time - Warning | ✅ Active |
| Metric Alert | Availability Drop - Critical | ✅ Active |
| Web Test | Production Health Check | ✅ Active |

---

**Setup Date**: 2026-03-31
**Status**: ✅ **COMPLETE**
**Next Phase**: Custom dashboards and log-based alerts

**Documentation**: This document should be updated when:
- New alerts are added
- Alert thresholds are modified
- Notification channels change
- Additional tests are created
