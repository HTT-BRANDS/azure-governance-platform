@description('Name of the workbook')
param name string

@description('Display name of the workbook')
param displayName string = 'Azure Governance Platform Dashboard'

@description('Location for the resource')
param location string = resourceGroup().location

@description('Serialized JSON content of the workbook')
param serializedData object

@description('Category for the workbook')
param category string = 'workbook'

@description('Description of the workbook')
param description string = 'Governance platform monitoring dashboard'

@description('Tags to apply')
param tags object = {}

@description('Source ID for the workbook (typically the resource ID of Log Analytics workspace)')
param sourceId string = ''

// Generate unique workbook ID
var workbookId = guid(resourceGroup().id, name)

// Workbook resource
resource workbook 'Microsoft.Insights/workbooks@2022-04-01' = {
  name: workbookId
  location: location
  tags: tags
  kind: 'shared'
  properties: {
    displayName: displayName
    description: description
    category: category
    serializedData: string(serializedData)
    sourceId: !empty(sourceId) ? sourceId : 'Azure Monitor'
    version: '1.0'
  }
}

// Outputs
output workbookId string = workbook.id
output workbookName string = workbook.name
output displayName string = workbook.properties.displayName
