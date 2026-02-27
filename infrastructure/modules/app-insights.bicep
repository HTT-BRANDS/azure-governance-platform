@description('Name of the Application Insights resource')
param name string

@description('Location for the resource')
param location string

@description('Log Analytics workspace ID')
param logAnalyticsWorkspaceId string

@description('Application Insights type')
@allowed(['web', 'other'])
param applicationType string = 'web'

@description('Tags to apply')
param tags object = {}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: applicationType
  properties: {
    Application_Type: applicationType
    Flow_Type: 'Bluefield'
    Request_Source: 'rest'
    WorkspaceResourceId: logAnalyticsWorkspaceId
    RetentionInDays: 90
    DisableIpMasking: false
  }
}

output instrumentationKey string = appInsights.properties.InstrumentationKey
output connectionString string = appInsights.properties.ConnectionString
output appId string = appInsights.properties.AppId
