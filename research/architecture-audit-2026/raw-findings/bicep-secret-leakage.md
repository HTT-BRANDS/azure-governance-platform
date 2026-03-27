# Bicep IaC Secret Output Leakage — Raw Findings

## Vulnerability in Project

### File: `infrastructure/modules/sql-server.bicep` (line 89)
```bicep
output connectionString string = 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=${databaseName};User ID=${adminUsername};Password=${adminPassword};Encrypt=true;TrustServerCertificate=false;Connection Timeout=30;'
```

### Bicep Linter Warnings (from `infrastructure/deploy-output.json`)
```
/infrastructure/modules/sql-server.bicep(89,135) : Warning outputs-should-not-contain-secrets: 
  Outputs should not contain secrets. Found possible secret: secure value 'adminUsername'

/infrastructure/modules/sql-server.bicep(89,161) : Warning outputs-should-not-contain-secrets: 
  Outputs should not contain secrets. Found possible secret: secure value 'adminPassword'
```

## Where Secrets Are Exposed

### 1. Azure Deployment History (Permanent Record)
- Azure Resource Manager stores all deployment outputs in the deployment history
- Visible at: Azure Portal → Resource Group → Deployments → {deployment-name} → Outputs
- Queryable via REST API: `GET /subscriptions/{id}/resourcegroups/{rg}/providers/Microsoft.Resources/deployments/{name}?api-version=2023-07-01`
- **Retention**: Deployment history is retained indefinitely by default (up to 800 deployments)

### 2. CLI/PowerShell Output
```bash
# This command would display the password in plaintext
az deployment sub show --name sqlServerDeploy --query properties.outputs.connectionString.value
```

### 3. CI/CD Pipeline Logs
- If any deployment step captures `az deployment` output, the password appears in logs
- GitHub Actions, Azure DevOps, and other CI systems often log deployment outputs

### 4. Local Files
- `infrastructure/deploy-output.json` may contain the rendered output
- `.azure/` cache directories may store deployment state

## Microsoft Official Guidance

### From Bicep Outputs Documentation
> With Bicep version 0.35.1 and later, you can mark string or object outputs as secure. 
> When an output is decorated with `@secure()`, Azure Resource Manager treats the output 
> value as sensitive, **preventing it from being logged or displayed in deployment history**, 
> Azure portal, or command-line outputs.

### Bicep Linter Rule: `outputs-should-not-contain-secrets`
- **Rule ID**: `outputs-should-not-contain-secrets`
- **Level**: Warning (should be treated as Error for production)
- **Documentation**: https://aka.ms/bicep/linter-diagnostics#outputs-should-not-contain-secrets
- **Detection**: Automatically detects when `@secure()` parameters are used in output values

## Remediation

### Best Practice: Don't output secrets at all
```bicep
// Store in Key Vault during deployment
resource kvSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'sql-connection-string'
  properties: {
    value: 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;...'
  }
}

// Output only non-sensitive identifiers
output serverFqdn string = sqlServer.properties.fullyQualifiedDomainName
output databaseName string = sqlDatabase.name
// NO connectionString output
```

### Additional Required Action
After fixing the template, **rotate the SQL admin password** since it has likely already been exposed in deployment history.
