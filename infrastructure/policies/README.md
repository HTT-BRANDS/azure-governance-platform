# Azure Policy Definitions for Governance

Compliance policies for the Azure Governance Platform. These policies enforce organizational standards across all Azure resources.

## Available Policies

### 1. Require Mandatory Tags (`require-tags-policy.json`)
**Purpose:** Ensures all resources have required governance tags

**Required Tags:**
- `Application` - Application or service name
- `Environment` - Environment classification (prod, staging, dev)
- `Owner` - Responsible team or individual
- `CostCenter` - Cost allocation code
- `DataClassification` - Data sensitivity level

**Modes:**
- `Audit` - Reports non-compliant resources (default)
- `Deny` - Prevents creation of non-compliant resources
- `Disabled` - Policy is inactive

**Exclusions:**
- VM extensions (automatically created)
- SQL database child resources

### 2. Enforce Encryption (`enforce-encryption-policy.json`)
**Purpose:** Mandates encryption for data at rest and in transit

**Coverage:**
- Storage accounts: Blob and file encryption enabled
- Storage accounts: Minimum TLS 1.2 required
- Storage accounts: HTTPS traffic only
- SQL databases: Transparent Data Encryption (TDE) enabled
- Managed disks: Encryption at rest

**Modes:**
- `Audit` - Reports violations
- `Deny` - Blocks unencrypted resource creation (default)
- `DeployIfNotExists` - Automatically enables encryption
- `Disabled` - Policy inactive

### 3. Prevent Public Storage Access (`prevent-public-storage-policy.json`)
**Purpose:** Prevents data exposure through overly permissive storage configurations

**Blocks:**
- Public blob access enabled
- Default network ACL set to "Allow"
- Public network access enabled without restrictions
- IP rules allowing 0.0.0.0/0

**Modes:**
- `Audit` - Reports violations
- `Deny` - Blocks public access configurations (default)
- `Disabled` - Policy inactive

**Exemptions:**
- Configurable list of storage account names
- Useful for public-facing static websites

### 4. Compliance Audit (`compliance-audit-policy.json`)
**Purpose:** Audits resources for comprehensive compliance standards

**Checks:**
- VM patch status reporting
- SQL auditing enabled
- Key Vault soft-delete and purge protection
- Application insights/monitoring tags
- Storage soft-delete for blobs

**Modes:**
- `Audit` - Always reports
- `AuditIfNotExists` - Reports when controls missing (default)
- `Disabled` - Policy inactive

## Deployment

### Via Azure Portal
1. Navigate to Policy > Definitions
2. Click "+ Policy definition"
3. Select target subscription
4. Enter definition name matching JSON file
5. Paste JSON content from policy file
6. Save

### Via Azure CLI
```bash
# Create policy definition
az policy definition create \
  --name "governance-require-tags" \
  --display-name "Governance: Require Mandatory Tags" \
  --description "Ensures all resources have required governance tags" \
  --rules @require-tags-policy.json \
  --params '{"requiredTags": {"value": ["Application", "Environment", "Owner", "CostCenter"]}}' \
  --mode Indexed

# Assign policy
az policy assignment create \
  --name "require-tags-assignment" \
  --policy "governance-require-tags" \
  --scope "/subscriptions/{subscription-id}" \
  --params '{"effect": {"value": "Audit"}}'
```

### Via PowerShell
```powershell
# Create policy definition
$policy = New-AzPolicyDefinition `
  -Name "governance-require-tags" `
  -DisplayName "Governance: Require Mandatory Tags" `
  -Description "Ensures all resources have required governance tags" `
  -Policy .

# Assign policy
New-AzPolicyAssignment `
  -Name "require-tags-assignment" `
  -PolicyDefinition $policy `
  -Scope "/subscriptions/{subscription-id}" `
  -PolicyParameterObject @{"effect"="Audit"}
```

### Via Bicep
```bicep
module tagPolicy './policy-definition.bicep' = {
  name: 'tag-policy'
  params: {
    name: 'governance-require-tags'
    policyRule: loadJsonContent('require-tags-policy.json').properties.policyRule
    parameters: loadJsonContent('require-tags-policy.json').properties.parameters
  }
}

module tagAssignment './policy-assignment.bicep' = {
  name: 'tag-assignment'
  params: {
    name: 'require-tags-assignment'
    policyDefinitionId: tagPolicy.outputs.id
    scope: subscription().id
    parameters: {
      effect: {
        value: 'Audit'
      }
    }
  }
}
```

## Policy Initiatives

Combine multiple policies into an initiative:

```json
{
  "properties": {
    "displayName": "Azure Governance Platform Compliance",
    "description": "Comprehensive governance and compliance standards",
    "metadata": {
      "category": "Governance"
    },
    "parameters": {},
    "policyDefinitions": [
      {
        "policyDefinitionId": "/subscriptions/{sub}/providers/Microsoft.Authorization/policyDefinitions/governance-require-tags",
        "parameters": {
          "effect": {
            "value": "Audit"
          }
        }
      },
      {
        "policyDefinitionId": "/subscriptions/{sub}/providers/Microsoft.Authorization/policyDefinitions/governance-enforce-encryption",
        "parameters": {
          "effect": {
            "value": "Deny"
          }
        }
      },
      {
        "policyDefinitionId": "/subscriptions/{sub}/providers/Microsoft.Authorization/policyDefinitions/governance-prevent-public-storage",
        "parameters": {
          "effect": {
            "value": "Deny"
          }
        }
      }
    ]
  }
}
```

## Compliance Reporting

### View Compliance Status
```bash
# Get compliance state for all policies
az policy state summarize

# Get specific policy compliance
az policy state list \
  --resource-group "rg-governance" \
  --filter "policyDefinitionName eq 'governance-require-tags'"
```

### Export Compliance Report
```bash
# Export to CSV
az policy state list \
  --output tsv \
  | tee compliance-report.tsv
```

## Best Practices

1. **Start with Audit Mode** - Begin with `Audit` to assess impact before enforcing
2. **Gradual Rollout** - Apply to single resource group first, then expand
3. **Document Exemptions** - Maintain list of approved policy exemptions
4. **Regular Review** - Quarterly review of policy effectiveness
5. **Combine with Remediation** - Use `DeployIfNotExists` for automatic fixes

## Remediation Tasks

Create remediation tasks for non-compliant resources:

```bash
# Create remediation task for tag policy
az policy remediation create \
  --name "tag-remediation" \
  --policy-assignment "require-tags-assignment" \
  --definition-reference-id "governance-require-tags"
```

## Troubleshooting

**Policy not evaluating:**
- Check policy assignment scope
- Verify resource type is supported
- Wait 15-30 minutes for evaluation

**Too many non-compliant resources:**
- Switch to `Audit` mode temporarily
- Use bulk tagging scripts
- Apply exemptions for legacy resources

**Deny blocking legitimate deployments:**
- Review parameter configurations
- Add appropriate exclusions
- Consider using `AuditIfNotExists` instead
