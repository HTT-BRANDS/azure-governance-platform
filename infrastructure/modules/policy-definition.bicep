@description('Name of the policy definition')
param name string

@description('Display name of the policy')
param displayName string

@description('Description of the policy')
param description string

@description('Policy type')
@allowed(['Custom', 'BuiltIn', 'Static'])
param policyType string = 'Custom'

@description('Policy mode')
@allowed(['All', 'Indexed', 'Microsoft.KeyVault.Data', 'Microsoft.Kubernetes.Data', 'Microsoft.Network.Data'])
param mode string = 'Indexed'

@description('Policy rule object')
param policyRule object

@description('Policy parameters object')
param parameters object = {}

@description('Metadata object')
param metadata object = {}

@description('Category for the policy')
param category string = 'Governance'

@description('Version of the policy')
param version string = '1.0.0'

@description('Source of the policy')
param source string = 'Azure Governance Platform'

// Policy definition resource
resource policyDefinition 'Microsoft.Authorization/policyDefinitions@2021-06-01' = {
  name: name
  properties: {
    displayName: displayName
    description: description
    policyType: policyType
    mode: mode
    metadata: union(metadata, {
      version: version
      category: category
      source: source
    })
    parameters: parameters
    policyRule: policyRule
  }
}

// Outputs
output policyId string = policyDefinition.id
output policyName string = policyDefinition.name
