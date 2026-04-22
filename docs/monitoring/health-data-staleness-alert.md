# `/health/data` Staleness Alert

Ticket: [3cs7](../../.beads/) · Parent audit: bd-dais (closed) · Approach: Option B (availability test)

## What it does

A multi-region Application Insights availability test pings
`/api/v1/health/data` every 5 minutes. If the response does **not** contain
`"any_stale":false`, the test fails. A metric alert on the failed
availability percentage fires the `governance-alerts` action group when
at least 2 of 3 regions fail within a 15-minute window.

That means you get alerted when **any** of the 10 domain sync jobs falls
behind the freshness threshold (currently set via `DATA_FRESHNESS_THRESHOLD_HOURS`
env var, default 25h).

## Why option B (and not option A)

The ticket described three options; this is option B (availability test).
Full rationale is in the Bicep header comment, but the short version:

| | Option A (telemetry) | **Option B (webtest)** | Option C (log query) |
|---|---|---|---|
| App code change | ~150 lines | **none** | none |
| Bicep size | ~100 lines | **~90 lines** | ~60 lines |
| Per-domain alerting | yes | no (response has the data; alert doesn't use it yet) | no |
| Coexists with others | — | **yes** | yes |

**YAGNI wins.** The response already exposes per-domain stale flags, so
if per-domain alerting becomes required later, option A is a pure-add —
the webtest keeps working unchanged.

## Deploy

```bash
# 1. Dry-run (what-if) — always do this first
az deployment group what-if \
    --resource-group rg-governance-production \
    --template-file infrastructure/monitoring/alerts/health-data-staleness-alert.bicep \
    --parameters appInsightsName=governance-appinsights \
                 actionGroupName=governance-alerts \
                 targetUrl=https://<prod-app>.azurewebsites.net/api/v1/health/data

# 2. Deploy for real
az deployment group create \
    --resource-group rg-governance-production \
    --template-file infrastructure/monitoring/alerts/health-data-staleness-alert.bicep \
    --parameters appInsightsName=governance-appinsights \
                 actionGroupName=governance-alerts \
                 targetUrl=https://<prod-app>.azurewebsites.net/api/v1/health/data
```

### Parameters

| Param | Default | Notes |
|---|---|---|
| `appInsightsName` | *(required)* | Existing App Insights component in the RG |
| `actionGroupName` | `governance-alerts` | Existing action group in the RG |
| `targetUrl` | *(required)* | Full `/api/v1/health/data` URL |
| `frequencySeconds` | `300` (5 min) | Allowed: 300 / 600 / 900 |
| `timeoutSeconds` | `30` | Per-test |
| `severity` | `2` | 0 = critical, 4 = verbose |

## Verify

After deployment:

```bash
# List recent webtest runs
az monitor app-insights web-test show \
    --resource-group rg-governance-production \
    --name health-data-staleness-<uniqueString> \
    --query 'properties.{enabled:Enabled,frequency:Frequency,locations:Locations[].Id}'

# Force a test fire (if you want to see the alert path work end-to-end)
az monitor metrics alert show \
    --resource-group rg-governance-production \
    --name alert-health-data-any-stale
```

Or just eyeball it in the portal under **Application Insights →
Availability** for about 10 minutes — you'll see green dots (passing)
or red X's (failing).

## Tune

If you see false-positive flapping (some single-region hiccup triggers
the alert), raise `failedLocationCount` in the Bicep from `2` to `3`.
If you want faster detection, tighten `windowSize` from `PT15M` to
`PT10M` (but expect more noise).

## Open follow-ups

- None currently. If per-domain granular alerting is desired later, file
  a new bd issue to upgrade to option A (telemetry + custom metric +
  KQL scheduled query). The response body already carries the per-domain
  data needed.

## Related

- `infrastructure/monitoring/alerts/health-data-staleness-alert.bicep`
- `app/api/routes/health.py` — `/api/v1/health/data` endpoint
- bd tickets: 3cs7 (this), dais (endpoint side, closed), w1cc (audit, closed)
