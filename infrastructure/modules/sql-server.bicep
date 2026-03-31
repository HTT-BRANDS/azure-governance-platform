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

@description('Database SKU name')
@allowed([
  'Free'
  'Basic'
  'Standard_S0'
  'Standard_S1'
  'Standard_S2'
  'Premium_P1'
])
param skuName string = 'Standard_S0'

@description('Tags to apply')
param tags object = {}

@description('Enable TDE')
param enableTde bool = true

@description('Enable auditing')
param enableAuditing bool = true

// Determine SKU properties based on tier
var isFreeTier = skuName == 'Free'
var isBasicTier = skuName == 'Basic'

// SKU configuration
var skuConfig = isFreeTier ? {
  name: 'Free'
  tier: 'Free'
} : isBasicTier ? {
  name: 'Basic'
  tier: 'Basic'
} : {
  name: skuName
  tier: startsWith(skuName, 'Standard_') ? 'Standard' : startsWith(skuName, 'Premium_') ? 'Premium' : 'Standard'
}

// Max size configuration by tier
var maxSizeBytes = isFreeTier ? 34359738368 // 32 GB
  : isBasicTier ? 2147483648 // 2 GB
  : startsWith(skuName, 'Standard_S0') ? 268435456000 // 250 GB
  : 268435456000 // Default 250 GB

// Backup redundancy by tier (Free only supports Local)
var backupRedundancy = isFreeTier ? 'Local' : 'Geo'
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
    // Free Tier requires public network access
    publicNetworkAccess: isFreeTier ? 'Enabled' : 'Disabled'
    restrictOutboundNetworkAccess: 'Disabled'
  }
}

// SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: databaseName
  location: location
  tags: union(tags, isFreeTier ? {
    'CostOptimization': 'FreeTier'
    'SLA': 'None'
  } : {})
  sku: skuConfig
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: maxSizeBytes
    sampleName: ''
    zoneRedundant: false
    readScale: 'Disabled'
    requestedBackupStorageRedundancy: backupRedundancy
    isLedgerOn: false
    // Free Tier has specific HA limitations
    highAvailabilityReplicaCount: isFreeTier ? 0 : null
  }
}

// Transparent Data Encryption
resource tde 'Microsoft.Sql/servers/databases/transparentDataEncryption@2023-05-01-preview' = if (enableTde) {
  parent: sqlDatabase
  name: 'current'
  properties: {
    state: 'Enabled'
  }
}

// Allow Azure services (required for Free Tier connectivity)
resource allowAzureServices 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = if (isFreeTier) {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// VNet rule for private connectivity (not supported on Free Tier)
resource vnetRule 'Microsoft.Sql/servers/virtualNetworkRules@2023-05-01-preview' = if (enableVNetIntegration && !empty(sqlSubnetId) && !isFreeTier) {
  parent: sqlServer
  name: 'VNetRule'
  properties: {
    virtualNetworkSubnetId: sqlSubnetId
    ignoreMissingVnetServiceEndpoint: false
  }
}


output serverId string = sqlServer.id
output serverName string = sqlServer.name
output serverFqdn string = sqlServer.properties.fullyQualifiedDomainName
output databaseId string = sqlDatabase.id
output databaseName string = sqlDatabase.name
