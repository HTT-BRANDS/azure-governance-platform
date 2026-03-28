// =============================================================================
// Azure Cache for Redis - Basic C0
// Cost: ~$16/month | 250MB | Non-SSL port disabled
// =============================================================================

@description('Redis cache name')
param name string

@description('Location')
param location string = resourceGroup().location

@description('Tags')
param tags object = {}

@description('SKU: Basic C0 for token blacklist + rate limiting')
@allowed([
  'Basic_C0'
  'Basic_C1'
  'Standard_C0'
  'Standard_C1'
])
param skuName string = 'Basic_C0'

var skuParts = split(skuName, '_')
var family = skuParts[0] == 'Basic' || skuParts[0] == 'Standard' ? 'C' : 'P'

resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: skuParts[0]
      family: family
      capacity: int(replace(skuParts[1], 'C', ''))
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled' // Basic tier doesn't support Private Endpoints
    redisConfiguration: {
      'maxmemory-policy': 'volatile-lru' // Evict keys with TTL first (perfect for token blacklist)
    }
  }
}

@description('Redis hostname')
output hostName string = redis.properties.hostName

@description('Redis SSL port')
output sslPort int = redis.properties.sslPort

@description('Redis primary connection string')
output connectionString string = '${redis.properties.hostName}:${redis.properties.sslPort}'

// NOTE: Key-based outputs removed (listKeys() leaks secrets into ARM
// deployment history). Use Key Vault references or Managed Identity
// (Microsoft.Cache/redis/accessPolicies) at the consumption site.
// See: https://learn.microsoft.com/azure/azure-cache-for-redis/cache-azure-active-directory-for-authentication

@description('Redis resource ID — use for Key Vault reference or RBAC assignment')
output resourceId string = redis.id
