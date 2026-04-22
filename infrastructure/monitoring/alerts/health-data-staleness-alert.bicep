// =============================================================================
// health-data-staleness-alert.bicep — 3cs7
// =============================================================================
//
// Option B: App Insights availability test + content-match + metric alert.
// Pings /api/v1/health/data every 5 minutes from multiple regions. Test fails
// if the response does NOT contain "any_stale":false (i.e. at least one domain
// is stale). Metric alert on availabilityResults/availabilityPercentage fires
// the existing governance-alerts action group.
//
// Why option B (not option A telemetry-driven):
//   YAGNI. The JSON response already carries per-domain stale flags, so we
//   lose nothing by polling it. Option A (custom metrics + KQL scheduled
//   query) would add ~300 lines of app + Bicep code for zero user-visible
//   benefit at this stage. If per-domain alerting becomes necessary later,
//   upgrading to option A is a pure-add (this test can coexist).
//
// DEPLOY:
//   az deployment group create \
//     --resource-group rg-governance-production \
//     --template-file infrastructure/monitoring/alerts/health-data-staleness-alert.bicep \
//     --parameters appInsightsName=governance-appinsights \
//                  actionGroupName=governance-alerts \
//                  targetUrl=https://<prod-app>.azurewebsites.net/api/v1/health/data
//
// See: docs/monitoring/health-data-staleness-alert.md
// =============================================================================

@description('Name of the existing Application Insights component in this resource group')
param appInsightsName string

@description('Name of the existing action group in this resource group to notify')
param actionGroupName string = 'governance-alerts'

@description('Full URL of the /api/v1/health/data endpoint to probe')
param targetUrl string

@description('Location for monitoring resources (alerts live globally; webtest is regional)')
param location string = resourceGroup().location

@description('How often the availability test runs, in seconds (300 = 5 min)')
@allowed([
  300
  600
  900
])
param frequencySeconds int = 300

@description('Per-test timeout, in seconds')
param timeoutSeconds int = 30

@description('Severity level for the alert (0=critical, 4=verbose)')
@allowed([
  0
  1
  2
  3
  4
])
param severity int = 2

@description('Tags to apply to monitoring resources')
param tags object = {
  Project: 'governance'
  Environment: 'production'
  Purpose: 'health-data-freshness'
  ManagedBy: 'bicep:health-data-staleness-alert'
}

// ── Existing resources ──────────────────────────────────────────────────────
resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' existing = {
  name: actionGroupName
}

// ── Availability test with content-match ────────────────────────────────────
// The content-match rule flips the test to FAIL whenever the response does
// NOT contain the substring "any_stale":false (note the JSON formatting
// matches what /api/v1/health/data emits). Failing tests drop
// availabilityPercentage below 100, which triggers the metric alert below.
var testName = 'health-data-staleness-${uniqueString(resourceGroup().id, appInsightsName)}'

resource availabilityTest 'Microsoft.Insights/webtests@2022-06-15' = {
  name: testName
  location: location
  tags: union(tags, {
    // Required hidden-link tag so App Insights "owns" the test
    'hidden-link:${appInsights.id}': 'Resource'
  })
  kind: 'standard'
  properties: {
    SyntheticMonitorId: testName
    Name: 'health-data staleness probe'
    Description: 'Fails when /api/v1/health/data reports any_stale=true (3cs7)'
    Enabled: true
    Frequency: frequencySeconds
    Timeout: timeoutSeconds
    Kind: 'standard'
    RetryEnabled: true
    Locations: [
      // Multi-region spread so a single-region blip doesn't false-positive.
      { Id: 'us-ca-sjc-azr' } // West US
      { Id: 'us-tx-sn1-azr' } // South Central US
      { Id: 'us-va-ash-azr' } // East US
    ]
    Request: {
      RequestUrl: targetUrl
      HttpVerb: 'GET'
      ParseDependentRequests: false
      Headers: [
        { key: 'User-Agent', value: 'azure-availability-test/3cs7' }
      ]
    }
    ValidationRules: {
      ExpectedHttpStatusCode: 200
      SSLCheck: true
      SSLCertRemainingLifetimeCheck: 30
      ContentValidation: {
        ContentMatch: '"any_stale":false'
        IgnoreCase: false
        PassIfTextFound: true
      }
    }
  }
}

// ── Metric alert: availability dropped below threshold ──────────────────────
resource staleAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'alert-health-data-any-stale'
  location: 'global'
  tags: tags
  properties: {
    description: 'Fires when /api/v1/health/data reports any_stale=true for > evaluationPeriod. See bd-3cs7.'
    severity: severity
    enabled: true
    scopes: [
      availabilityTest.id
      appInsights.id
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.WebtestLocationAvailabilityCriteria'
      webTestId: availabilityTest.id
      componentId: appInsights.id
      // Alert if < 2 out of 3 locations pass within a 15-minute window.
      // Tolerates single-region transient hiccups; catches real outages.
      failedLocationCount: 2
    }
    actions: [
      {
        actionGroupId: actionGroup.id
        // Include stale-domain detail if we ever move to option A.
        webHookProperties: {}
      }
    ]
  }
}

// ── Outputs ─────────────────────────────────────────────────────────────────
output webTestId string = availabilityTest.id
output webTestName string = availabilityTest.name
output alertId string = staleAlert.id
