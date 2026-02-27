@description('Name of the Log Analytics workspace')
param name string

@description('Location for the resource')
param location string

@description('Log retention in days')
param retentionInDays int = 30

@description('SKU for the workspace')
param sku string = 'PerGB2018'

@description('Tags to apply')
param tags object = {}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: sku
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

output workspaceId string = logAnalyticsWorkspace.id
output workspaceName string = logAnalyticsWorkspace.name
output customerId string = logAnalyticsWorkspace.properties.customerId
