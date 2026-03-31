# 📊 Monitoring & Alerting Configuration

Prometheus alerting rules and Alertmanager configuration for the Azure Governance Platform.

## Files

| File | Description |
|------|-------------|
| `alerting-rules.yml` | Prometheus alerting rules (22+ alerts across 8 groups) |
| `alertmanager.yml` | Alertmanager routing configuration |

## Alert Groups

### 1. Performance Alerts
Monitors API response times and error rates:
- **HighP95ResponseTime** (warning): P95 > 1s for 5min
- **CriticalP99ResponseTime** (critical): P99 > 2s for 2min
- **HighErrorRate** (warning): Error rate > 1%
- **CriticalErrorRate** (critical): Error rate > 5%

### 2. Sync Operation Alerts
Monitors data synchronization jobs:
- **SyncJobTooSlow**: Sync taking > 10 minutes
- **SyncJobFailed**: Any sync failure
- **NoRecentSync**: No sync in 2+ hours
- **StaleSyncData**: Data 4+ hours old (critical)
- **TooManyActiveSyncJobs**: > 5 concurrent syncs

### 3. Authentication Alerts
Monitors auth system health:
- **HighAuthFailureRate**: > 10% auth failures
- **AuthLatencyTooHigh**: P95 auth > 2s
- **ManyExpiredTokens**: Many token expiry errors

### 4. Database Alerts
Monitors database performance:
- **SlowDBQuery**: P95 query time > 1s
- **DBConnectionErrors**: Connection failures
- **DBDeadlockDetected**: Deadlock events
- **DBPoolExhaustion**: Pool > 90% used

### 5. Cache Alerts
- **LowCacheHitRate**: Hit rate < 50%
- **CacheErrorsIncreasing**: Error spike

### 6. External API Alerts
- **ExternalAPILatencyHigh**: API calls > 5s
- **ExternalAPIErrors**: API error spike
- **RateLimitApproaching**: Low rate limit remaining
- **AzureAuthErrors**: Azure API auth issues

### 7. Business Logic Alerts
- **ComplianceScoreDrop**: Score dropped > 20%
- **LowComplianceScore**: Score < 50%
- **CostAnomalyDetected**: Cost anomalies

### 8. Infrastructure Alerts
- **InstanceDown**: Service unavailable
- **HighMemoryUsage**: Memory > 1.5GB
- **HighCPUUsage**: CPU > 80%
- **DiskSpaceLow**: Disk < 10%

## Deployment

### Prometheus Rules

Copy the rules file to your Prometheus rules directory:

```bash
# On Prometheus server
sudo cp alerting-rules.yml /etc/prometheus/rules.d/azure-governance-alerts.yml

# Verify rules
promtool check rules /etc/prometheus/rules.d/azure-governance-alerts.yml

# Reload Prometheus (SIGHUP or API)
curl -X POST http://localhost:9090/-/reload
```

### Alertmanager

```bash
# Copy configuration
sudo cp alertmanager.yml /etc/alertmanager/alertmanager.yml

# Verify configuration
amtool check-config /etc/alertmanager/alertmanager.yml

# Restart Alertmanager
sudo systemctl restart alertmanager
```

## Environment Variables

Set these for Alertmanager:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"  # pragma: allowlist secret
export PAGERDUTY_SERVICE_KEY="your-pagerduty-integration-key"
export SMTP_USER="alerts@governance.example.com"
export SMTP_PASS="your-smtp-password"
```

## Testing Alerts

### Simulate an alert

```bash
# Send test alert to Alertmanager
curl -X POST http://alertmanager:9093/-/reload

# Test alert rule
curl -G "http://prometheus:9090/api/v1/query" \
  --data-urlencode 'query=governance_sync_duration_seconds{quantile="0.95"} > 600'
```

### Silence an alert

```bash
# Create silence via API
curl -X POST http://alertmanager:9093/api/v1/silences \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "HighP95ResponseTime"},
      {"name": "severity", "value": "warning"}
    ],
    "startsAt": "2025-01-01T00:00:00Z",
    "endsAt": "2025-01-01T01:00:00Z",
    "createdBy": "ops-team",
    "comment": "Planned maintenance window"
  }'
```

## Grafana Dashboards

Import the dashboards from `config/monitoring/dashboards/`:

1. **API Performance**: Response times, throughput, error rates
2. **Sync Jobs**: Job status, duration, record counts
3. **Authentication**: Login rates, token operations, failures
4. **Infrastructure**: CPU, memory, disk usage
5. **Business Metrics**: Compliance scores, cost anomalies

## Severity Definitions

| Severity | Response Time | Notification |
|----------|-----------------|--------------|
| critical | Immediate | PagerDuty + Slack #critical |
| warning | 30 minutes | Slack #warnings |
| info | Next business day | Slack #info (optional) |

## Runbooks

Link runbooks in alert annotations:

```yaml
annotations:
  runbook_url: "https://wiki.internal/runbooks/high-response-time"
```

Example runbook structure:
1. **Check**: What to verify first
2. **Diagnose**: How to identify root cause
3. **Mitigate**: Immediate steps to reduce impact
4. **Resolve**: How to fix the underlying issue
5. **Prevent**: Actions to prevent recurrence

## Custom Metrics

The platform exposes these custom metrics (from `app/core/metrics.py`):

```
# Sync operations
governance_sync_duration_seconds{sync_type, status}
governance_sync_records_total{sync_type, record_type}
governance_sync_active_jobs{sync_type}
governance_sync_last_success_timestamp{sync_type}

# Auth operations
governance_auth_latency_seconds{operation, provider}
governance_auth_attempts_total{operation, result}
governance_auth_active_sessions{tenant_id}
governance_token_operations_total{operation, token_type}

# Database
governance_db_query_duration_seconds{operation, table}
governance_db_connections_active{state}
governance_db_pool_size{pool_type}
governance_db_errors_total{error_type}

# Cache
governance_cache_operations_total{backend, operation, result}
governance_cache_size_bytes{backend}
governance_cache_ttl_seconds{cache_type}

# External APIs
governance_external_api_latency_seconds{service, endpoint}
governance_external_api_errors_total{service, error_type, status_code}
governance_external_api_rate_limit_remaining{service}

# Business logic
governance_compliance_score{tenant_id, framework}
governance_cost_anomalies_total{severity, resource_type}
governance_recommendations_generated_total{category, priority}
```

## Integration with Azure Monitor

Optionally forward alerts to Azure Monitor:

```yaml
# Additional webhook receiver in alertmanager.yml
- name: 'azure-monitor'
  webhook_configs:
    - url: 'https://your-logic-app.azurewebsites.net/api/alerts'
      send_resolved: true
```
