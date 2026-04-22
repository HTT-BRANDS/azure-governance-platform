// -----------------------------------------------------------------------------
// Policy definitions cannot deploy at resourceGroup scope (see BCP135). All
// current callers (deploy-governance-infrastructure.bicep at subscription
// scope) pin this module to subscription scope. For management-group policy
// definitions, create a sibling policy-definition-mg.bicep instead.
// -----------------------------------------------------------------------------
targetScope = 'subscription'

@sys.description('Name of the policy definition')
param name string

@sys.description('Display name of the policy')
param displayName string

@sys.description('Description of the policy')
param description string

@sys.description('Policy type')
@allowed(['Custom', 'BuiltIn', 'Static'])
param policyType string = 'Custom'

@sys.description('Policy mode')
@allowed(['All', 'Indexed', 'Microsoft.KeyVault.Data', 'Microsoft.Kubernetes.Data', 'Microsoft.Network.Data'])
param mode string = 'Indexed'

@sys.description('Policy rule object')
param policyRule object

@sys.description('Policy parameters object')
param parameters object = {}

@sys.description('Metadata object')
param metadata object = {}

@sys.description('Category for the policy')
param category string = 'Governance'

@sys.description('Version of the policy')
param version string = '1.0.0'

@sys.description('Source of the policy')
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
