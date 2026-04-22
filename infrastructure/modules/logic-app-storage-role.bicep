// =============================================================================
// Sub-module: assign Storage Blob Data Contributor to a Logic App's identity
// =============================================================================
// Extracted from logic-apps.bicep to support the case where the Logic App and
// its backing storage account live in DIFFERENT resource groups. Role
// assignments must be deployed at the scope of the target resource, and a
// Bicep file can only deploy to one scope, so we invoke this module with
// `scope: resourceGroup(storageAccountResourceGroup)` from the parent.
// =============================================================================

@sys.description('Name of the existing storage account in THIS resource group')
param storageAccountName string

@sys.description('Resource ID of the Logic App whose identity is being granted access. Used only for the role-assignment GUID — avoids collisions when multiple Logic Apps share a backing storage account.')
param logicAppResourceId string

@sys.description('Principal ID (objectId) to grant the role to. For system-assigned identities, this is logicApp.identity.principalId; for user-assigned, look up from the identity resource.')
param principalId string

// Storage Blob Data Contributor
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, logicAppResourceId, storageBlobDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = storageRoleAssignment.id
