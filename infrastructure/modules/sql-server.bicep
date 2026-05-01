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

@description('Whether to set/rotate the SQL administrator password. Existing-server reconciliation should keep this false unless password rotation is explicitly approved.')
param setAdminPassword bool = true

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

@description('Optional public network access override. Empty keeps the module default: Enabled for Free tier, Disabled otherwise.')
@allowed([
  ''
  'Enabled'
  'Disabled'
])
param publicNetworkAccessOverride string = ''

@description('Optional database max size bytes override. Use 0 to keep SKU-based default.')
param maxSizeBytesOverride int = 0

@description('Optional requested backup storage redundancy override. Empty keeps SKU-based default.')
@allowed([
  ''
  'Local'
  'Geo'
  'Zone'
  'GeoZone'
])
param backupRedundancyOverride string = ''

@description('Name for the Free-tier Azure-services firewall rule.')
param allowAzureServicesFirewallRuleName string = 'AllowAzureServices'

@description('Enable TDE')
param enableTde bool = true

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
var defaultMaxSizeBytes = isFreeTier ? 34359738368 // 32 GB
  : isBasicTier ? 2147483648 // 2 GB
  : startsWith(skuName, 'Standard_S0') ? 268435456000 // 250 GB
  : 268435456000 // Default 250 GB
var maxSizeBytes = maxSizeBytesOverride > 0 ? maxSizeBytesOverride : defaultMaxSizeBytes

// Backup redundancy by tier (Free only supports Local)
var defaultBackupRedundancy = isFreeTier ? 'Local' : 'Geo'
var backupRedundancy = empty(backupRedundancyOverride) ? defaultBackupRedundancy : backupRedundancyOverride
var publicNetworkAccess = empty(publicNetworkAccessOverride) ? (isFreeTier ? 'Enabled' : 'Disabled') : publicNetworkAccessOverride
// SQL Server
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: serverName
  location: location
  tags: tags
  properties: union({
    administratorLogin: adminUsername
    version: '12.0'
    minimalTlsVersion: '1.2'
    // Free Tier requires public network access; existing environments can explicitly model live public access.
    publicNetworkAccess: publicNetworkAccess
    restrictOutboundNetworkAccess: 'Disabled'
  }, setAdminPassword ? {
    administratorLoginPassword: adminPassword
  } : {})
}

// SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: databaseName
  location: location
  tags: union(tags, isFreeTier ? {
    CostOptimization: 'FreeTier'
    SLA: 'None'
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
  name: allowAzureServicesFirewallRuleName
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
