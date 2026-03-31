@description('Name of the SQL Server')
param serverName string

@description('Name of the database')
param databaseName string

@description('Location for the resources')
param location string

@description('Administrator username')
@secure()
param adminUsername string

@description('Administrator password')
@secure()
param adminPassword string

@description('Enable VNet integration for private connectivity')
param enableVNetIntegration bool = false

@description('VNet subnet ID for SQL server')
param sqlSubnetId string = ''

@description('Tags to apply')
param tags object = {}

@description('Enable TDE')
param enableTde bool = true

@description('Enable auditing')
param enableAuditing bool = true

// Azure SQL Free Tier Limits:
// - 1 free database per subscription
// - Max size: 32 GB (2 GB data + 30 GB log)
// - Basic compute (5 DTU equivalent)
// - No SLA
// - 7-day point-in-time restore
// - No geo-replication
// - 30 max concurrent connections

var freeTierSku = {
  name: 'Free'
  tier: 'Free'
  capacity: 0
}

var freeTierMaxSizeBytes = 34359738368 // 32 GB

// SQL Server
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: serverName
  location: location
  tags: tags
  properties: {
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'  // Free tier requires public access (can restrict by firewall)
    restrictOutboundNetworkAccess: 'Disabled'
  }
}

// SQL Database - Free Tier
// Note: Free tier has specific restrictions:
// - Cannot be used with VNet rules (requires public access)
// - No geo-redundancy
// - No auto-failover
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: databaseName
  location: location
  tags: union(tags, {
    'CostOptimization': 'FreeTier'
    'Environment': 'Staging'
    'SLA': 'None'
  })
  sku: freeTierSku
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: freeTierMaxSizeBytes
    sampleName: ''
    zoneRedundant: false
    readScale: 'Disabled'
    requestedBackupStorageRedundancy: 'Local'  // Free tier only supports local redundancy
    isLedgerOn: false
    // Free tier does not support high availability
    highAvailabilityReplicaCount: 0
    // No secondary replicas on free tier
    createMode: 'Default'
  }
}

// Transparent Data Encryption (enabled by default on all tiers)
resource tde 'Microsoft.Sql/servers/databases/transparentDataEncryption@2023-05-01-preview' = if (enableTde) {
  parent: sqlDatabase
  name: 'current'
  properties: {
    state: 'Enabled'
  }
}

// Server-level firewall rule - restrict to Azure services only
// For staging, we allow Azure services. For stricter control, specify IP ranges.
resource allowAzureServices 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Note: VNet rules are NOT supported with Free Tier
// Free Tier requires public network access
// Use firewall rules for access control instead

// Auditing (best practice even on free tier)
resource auditing 'Microsoft.Sql/servers/auditingSettings@2023-05-01-preview' = if (enableAuditing) {
  parent: sqlServer
  name: 'default'
  properties: {
    state: 'Enabled'
    retentionDays: 7  // Free tier limitation
    auditActionsAndGroups: [
      'SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP'
      'FAILED_DATABASE_AUTHENTICATION_GROUP'
      'BATCH_COMPLETED_GROUP'
    ]
    isAzureMonitorTargetEnabled: true
  }
}

// Diagnostic settings for basic monitoring
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'SQLFreeTierDiagnostics'
  scope: sqlDatabase
  properties: {
    logs: [
      {
        category: 'SQLInsights'
        enabled: true
        retentionPolicy: {
          days: 7
          enabled: true
        }
      }
      {
        category: 'Errors'
        enabled: true
        retentionPolicy: {
          days: 7
          enabled: true
        }
      }
    ]
    metrics: [
      {
        category: 'Basic'
        enabled: true
        retentionPolicy: {
          days: 7
          enabled: true
        }
      }
    ]
  }
}

// Alert for storage approaching limit (80% of 32GB = 25.6GB)
resource storageAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${serverName}-${databaseName}-storage-alert'
  location: 'global'
  properties: {
    description: 'Alert when database storage exceeds 80% of Free Tier limit'
    severity: 2
    enabled: true
    scopes: [
      sqlDatabase.id
    ]
    evaluationFrequency: 'PT15M'
    windowSize: 'PT1H'
    criteria: {
      allOf: [
        {
          threshold: 80
          name: 'StoragePercent'
          metricNamespace: 'Microsoft.Sql/servers/databases'
          metricName: 'storage_percent'
          operator: 'GreaterThan'
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
    }
    actions: []
  }
}

// Outputs
output serverId string = sqlServer.id
output serverName string = sqlServer.name
output serverFqdn string = sqlServer.properties.fullyQualifiedDomainName
output databaseId string = sqlDatabase.id
output databaseName string = sqlDatabase.name
output tier string = 'Free'
output maxSizeGb int = 32
output limitations array = [
  'Max 32 GB storage (2 GB data + 30 GB log)'
  'Basic compute (5 DTU equivalent)'
  'No SLA guarantee'
  'No geo-redundancy'
  'Local backup only (7-day retention)'
  'Max 30 concurrent connections'
  'No VNet integration support'
  'Public network access required'
]
