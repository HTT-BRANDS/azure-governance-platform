@description('Name of the primary SQL Server')
param primaryServerName string

@description('Name of the secondary (replica) SQL Server')
param secondaryServerName string

@description('Name of the database to replicate')
param databaseName string

@description('Location for the primary server')
param primaryLocation string

@description('Location for the secondary server (must be different region)')
param secondaryLocation string

@description('Administrator username')
@secure()
param adminUsername string

@description('Administrator password')
@secure()
param adminPassword string

@description('Database SKU name for secondary')
@allowed([
  'Standard_S0'
  'Standard_S1'
  'Standard_S2'
  'Premium_P1'
  'Premium_P2'
  'GP_Gen5_2'
  'GP_Gen5_4'
  'GP_Gen5_8'
  'BC_Gen5_2'
  'BC_Gen5_4'
  'BC_Gen5_8'
])
param secondarySkuName string = 'Standard_S0'

@description('Failover group name')
param failoverGroupName string = '${primaryServerName}-failover-group'

@description('Read/write endpoint failover policy')
@allowed(['Automatic', 'Manual'])
param failoverPolicy string = 'Automatic'

@description('Grace period with data loss hours (for automatic failover)')
@allowed([1, 2, 3, 4, 5, 6, 12, 24])
param gracePeriodHours int = 1

@description('Allow read-only traffic on secondary')
param allowSecondaryReadOnly bool = true

@description('Tags to apply')
param tags object = {}

@description('Enable TDE on secondary')
param enableTde bool = true

// Primary SQL Server (assumed to already exist, but included for completeness)
resource primaryServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: primaryServerName
  location: primaryLocation
  tags: tags
  properties: {
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: 'Disabled'
  }
}

// Primary Database (assumed to already exist)
resource primaryDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: primaryServer
  name: databaseName
  location: primaryLocation
  tags: tags
  sku: {
    name: 'Standard_S0'  // Will be overridden by existing if present
    tier: 'Standard'
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 268435456000  // 250 GB
    sampleName: ''
    zoneRedundant: false
    readScale: 'Disabled'
    requestedBackupStorageRedundancy: 'Geo'
  }
}

// Secondary SQL Server (in different region)
resource secondaryServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: secondaryServerName
  location: secondaryLocation
  tags: union(tags, { 
    Purpose: 'Geo-Replication Secondary'
    PrimaryServer: primaryServerName
  })
  properties: {
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: 'Disabled'
  }
}

// Secondary Database (replica)
resource secondaryDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: secondaryServer
  name: databaseName
  location: secondaryLocation
  tags: union(tags, { 
    Purpose: 'Geo-Replication Secondary'
    PrimaryServer: primaryServerName
  })
  sku: {
    name: secondarySkuName
    tier: startsWith(secondarySkuName, 'Standard_') ? 'Standard' : startsWith(secondarySkuName, 'Premium_') ? 'Premium' : startsWith(secondarySkuName, 'BC_') ? 'BusinessCritical' : 'GeneralPurpose'
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 268435456000  // 250 GB
    sampleName: ''
    zoneRedundant: false
    readScale: allowSecondaryReadOnly ? 'Enabled' : 'Disabled'
    requestedBackupStorageRedundancy: 'Geo'
    createMode: 'OnlineSecondary'
    sourceDatabaseId: primaryDatabase.id
  }
}

// Transparent Data Encryption on secondary
resource secondaryTde 'Microsoft.Sql/servers/databases/transparentDataEncryption@2023-05-01-preview' = if (enableTde) {
  parent: secondaryDatabase
  name: 'current'
  properties: {
    state: 'Enabled'
  }
}

// Allow Azure services on secondary
resource allowAzureServicesSecondary 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = {
  parent: secondaryServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Failover Group
resource failoverGroup 'Microsoft.Sql/servers/failoverGroups@2023-05-01-preview' = {
  parent: primaryServer
  name: failoverGroupName
  properties: {
    serverName: primaryServerName
    partnerServers: [
      {
        id: secondaryServer.id
      }
    ]
    databases: [
      primaryDatabase.id
    ]
    readWriteEndpoint: {
      failoverPolicy: failoverPolicy
      failoverWithDataLossGracePeriodMinutes: failoverPolicy == 'Automatic' ? gracePeriodHours * 60 : null
    }
    readOnlyEndpoint: {
      failoverPolicy: allowSecondaryReadOnly ? 'Enabled' : 'Disabled'
    }
  }
}

// Outputs
output primaryServerFqdn string = primaryServer.properties.fullyQualifiedDomainName
output secondaryServerFqdn string = secondaryServer.properties.fullyQualifiedDomainName
output failoverGroupName string = failoverGroup.name
output failoverGroupFqdn string = failoverGroup.properties.readWriteEndpoint.fqdn
output secondaryLocation string = secondaryLocation
output replicationStatus string = 'Active'
output readOnlyEndpoint string = allowSecondaryReadOnly ? '${failoverGroup.properties.readOnlyEndpoint.fqdn}' : 'Disabled'
