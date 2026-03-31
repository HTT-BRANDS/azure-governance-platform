# Load Tests — Azure Governance Platform

Validates **NF-P03** (50+ concurrent users) and **NF-P02** (API response < 500ms cached).

## Quick Start

```bash
# Start the app
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run load test (headless, CI-friendly)
uv run locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    --users 50 \
    --spawn-rate 10 \
    --run-time 60s
```

## Load Test Scenarios

### 1. Standard Load (`GovernanceAPIUser`)
Simulates typical governance platform usage across all endpoints.

### 2. Auth Load (`AuthLoadUser`)
Tests authentication-heavy workflows:
- Login flows (`/api/v1/auth/staging-token`)
- Token validation (`/api/v1/auth/validate`)
- User info (`/api/v1/auth/me`)
- Logout (`/api/v1/auth/logout`)

```bash
uv run locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    --class-picker AuthLoadUser \
    --users 30 \
    --run-time 60s
```

### 3. Sync Load (`SyncLoadUser`)
Tests sync operation endpoints:
- Sync status (`/api/v1/sync/status`)
- Sync history (`/api/v1/sync/history`)
- Sync metrics (`/api/v1/sync/metrics`)
- Trigger sync (`/api/v1/sync/trigger`)
- Sync health (`/api/v1/sync/health`)

```bash
uv run locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    --class-picker SyncLoadUser \
    --users 20 \
    --run-time 60s
```

### 4. Mixed Load (`MixedLoadUser`)
Combines all scenarios for comprehensive testing.

## SLA Thresholds

| Metric | Threshold | Requirement | Configurable |
|--------|-----------|-------------|--------------|
| P95 response time | < 500ms | NF-P02 | `LOAD_TEST_P95_MAX_MS` |
| P99 response time | < 1000ms | (warning) | `LOAD_TEST_P99_MAX_MS` |
| Error rate | < 1% | NF-R05 | `LOAD_TEST_ERROR_RATE_MAX` |
| Minimum requests | 100 | (validation) | `LOAD_TEST_MIN_REQUESTS` |
| Concurrent users | 50+ | NF-P03 | `--users` |

### Customizing SLA Thresholds

```bash
# Stricter SLA for production readiness
LOAD_TEST_P95_MAX_MS=200 \
LOAD_TEST_ERROR_RATE_MAX=0.5 \
uv run locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    --users 100 \
    --run-time 120s
```

## Traffic Distribution

### Standard User (`GovernanceAPIUser`)

| Category | Weight | Endpoints |
|----------|--------|-----------|
| Health | 10% | /health, /metrics |
| Cost Management | 30% | summary, trends, anomalies |
| Compliance | 25% | summary, frameworks |
| Resources | 20% | inventory, quotas |
| Identity | 10% | summary |
| Recommendations | 5% | recommendations |

### Auth User (`AuthLoadUser`)

| Operation | Weight |
|-----------|--------|
| Staging token login | 5 |
| Token validation | 3 |
| Get user info | 2 |
| Logout | 1 |

### Sync User (`SyncLoadUser`)

| Operation | Weight |
|-----------|--------|
| Sync status | 4 |
| Sync history | 3 |
| Sync metrics | 2 |
| Trigger sync | 1 |
| Sync health | 1 |

## CI Integration

The load test automatically fails on SLA violations:

```bash
# Exit code 1 if any SLA is breached
uv run locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    --users 50 \
    --spawn-rate 10 \
    --run-time 60s \
    --exit-code-on-error 0  # Don't let locust exit code fail CI

# Check the process exit code for SLA results
echo "Load test exit code: $?"
```

## Output Format

```
======================================================================
LOAD TEST SLA REPORT
======================================================================

📊 REQUEST STATISTICS
   Total requests:  1,234
   Failed requests: 0
   Error rate:      0.00%

⏱️  RESPONSE TIMES
   p50 (median):    45ms
   p75:             78ms
   p95:             156ms
   p99:             234ms
   Max:             512ms
   Min:             12ms
   Avg:             67ms

📋 SLA THRESHOLDS
   p95 max:         500ms
   p99 max:         1000ms
   Error rate max:  1.0%

🔍 PER-ENDPOINT P95 (> 500ms threshold):
   All endpoints within SLA ✓

✅ SLA CHECKS
   ✓ p95: 156ms <= 500ms
   ✓ p99: 234ms <= 1000ms
   ✓ Error rate: 0.00% <= 1.0%
======================================================================
✅ LOAD TEST PASSED in 1.5s
```

## Slow Request Detection

Requests taking > 1 second are automatically logged:

```
[SLOW REQUEST] 2025-01-15T10:30:45Z - /api/v1/costs/summary: 1200ms
```

## CSV Output for Analysis

```bash
# Generate CSV reports
uv run locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --headless \
    --users 50 \
    --run-time 60s \
    --csv tests/load/results

# Files generated:
#   tests/load/results_stats.csv      - Aggregated stats
#   tests/load/results_stats_history.csv - Time series
#   tests/load/results_failures.csv   - Failed requests
#   tests/load/results_exceptions.csv - Exceptions
```

## Best Practices

1. **Warm up**: Run a short test before the main test to warm caches
2. **Ramp up**: Use `--spawn-rate` to gradually increase load
3. **Realistic timing**: Use `--wait-time` between requests (1-5s typical)
4. **Monitor**: Watch both the app and load generator resources
5. **Baseline**: Establish baselines in your environment for comparison
