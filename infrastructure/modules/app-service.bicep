@description('Name of the App Service')
param name string

@description('Location for the resource')
param location string

@description('App Service Plan ID')
param appServicePlanId string

@description('Application Insights connection string')
param appInsightsConnectionString string = ''

@description('Storage account name for file mounts')
param storageAccountName string

@description('Key Vault name (optional)')
param keyVaultName string = ''

@description('SQL Server name (optional)')
param sqlServerName string = ''

@description('SQL Database name (optional)')
param sqlDatabaseName string = ''

@description('Enable Azure SQL')
param enableAzureSql bool = false

@description('Container image tag')
param containerImage string = 'latest'

@description('Azure Container Registry name (optional)')
param acrName string = ''

@description('Environment name')
param environment string

@description('Tags to apply')
param tags object = {}

@description('Python version')
param pythonVersion string = '3.11'

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

// Reference to storage account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

// Reference to Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (!empty(keyVaultName)) {
  name: keyVaultName
}

// App Service
resource appService 'Microsoft.Web/sites@2023-12-01' = {
  name: name
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlanId
    enabled: true
    reserved: true
    httpsOnly: true
    clientAffinityEnabled: false
    clientCertEnabled: false
    hostNameSslStates: []
    siteConfig: {
      numberOfWorkers: 1
      linuxFxVersion: 'PYTHON|${pythonVersion}'
      alwaysOn: true
      httpLoggingEnabled: true
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appCommandLine: 'python -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
      healthCheckPath: '/health'
      use32BitWorkerProcess: false
      webSocketsEnabled: false
      managedPipelineMode: 'Integrated'
      loadBalancing: 'LeastRequests'
      experiments: {
        rampUpRules: []
      }
      autoHealEnabled: true
      autoHealRules: {
        actions: {
          actionType: 'Recycle'
          minProcessExecutionTime: '00:01:00'
        }
        triggers: {
          requests: {
            count: 100
            timeInterval: '00:05:00'
          }
          statusCodes: [
            {
              status: 500
              subStatus: 0
              win32Status: 0
              count: 10
              timeInterval: '00:05:00'
            }
            {
              status: 502
              subStatus: 0
              win32Status: 0
              count: 10
              timeInterval: '00:05:00'
            }
          ]
          slowRequests: {
            timeTaken: '00:01:00'
            count: 10
            timeInterval: '00:05:00'
          }
        }
      }
      appSettings: [
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'DEBUG'
          value: 'false'
        }
        {
          name: 'LOG_LEVEL'
          value: 'INFO'
        }
        {
          name: 'HOST'
          value: '0.0.0.0'
        }
        {
          name: 'PORT'
          value: '8000'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: empty(appInsightsConnectionString) ? '' : split(appInsightsConnectionString, ';')[0]
        }
        {
          name: 'CACHE_ENABLED'
          value: 'true'
        }
        {
          name: 'DATABASE_URL'
          value: enableAzureSql 
            ? 'mssql+pyodbc://@{sqlServerName}.database.windows.net:1433/${sqlDatabaseName}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no'
            : 'sqlite:///home/data/governance.db'
        }
        {
          name: 'KEY_VAULT_URL'
          value: empty(keyVaultName) ? '' : 'https://${keyVaultName}.vault.azure.net'
        }
        {
          name: 'PYTHON_VERSION'
          value: pythonVersion
        }
        {
          name: 'WEBSITE_HEALTHCHECK_MAXPINGFAILURES'
          value: '3'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'true'
        }
      ]
      connectionStrings: []
    }
  }
}

// Configure AzureFiles mount for persistent storage
resource azureStorageConfig 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: appService
  name: 'azureStorageAccounts'
  properties: {
    dataVolume: {
      type: 'AzureFiles'
      shareName: 'appdata'
      mountPath: '/home/data'
      accountName: storageAccountName
      accessKey: storageAccount.listKeys().keys[0].value
    }
    logsVolume: {
      type: 'AzureFiles'
      shareName: 'applogs'
      mountPath: '/home/logs'
      accountName: storageAccountName
      accessKey: storageAccount.listKeys().keys[0].value
    }
  }
}

// Diagnostic settings
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'AppServiceDiagnostics'
  scope: appService
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'AppServiceHTTPLogs'
        enabled: true
      }
      {
        category: 'AppServiceConsoleLogs'
        enabled: true
      }
      {
        category: 'AppServiceAppLogs'
        enabled: true
      }
      {
        category: 'AppServiceAuditLogs'
        enabled: true
      }
      {
        category: 'AppServiceIPSecAuditLogs'
        enabled: true
      }
      {
        category: 'AppServicePlatformLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// Key Vault access policy (grant app service access to Key Vault)
resource keyVaultAccessPolicy 'Microsoft.KeyVault/vaults/accessPolicies@2023-07-01' = if (!empty(keyVaultName)) {
  parent: keyVault
  name: 'add'
  properties: {
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: appService.identity.principalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}

output appServiceId string = appService.id
output appServiceName string = appService.name
output appUrl string = 'https://${appService.properties.defaultHostName}'
output principalId string = appService.identity.principalId
