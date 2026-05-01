# Sources and credibility

All sources are Microsoft Learn / Azure CLI official documentation: Tier 1, current enough for 2025-2026 Azure/Bicep behavior.

| Topic | Source | Currency observed | Credibility notes |
|---|---|---:|---|
| Existing resources | https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/existing-resource | Last updated 2025-10-30 | Official Bicep guidance; states `existing` doesn't redeploy and NotFound fails deployment. |
| Child resources | https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/child-resource-name-type | Last updated 2025-12-22 | Official Bicep child resource syntax; recommends parent property over full names for type safety. |
| Resource/list/getSecret functions | https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/bicep-functions-resource | Last updated 2026-04-17 | Official function behavior, including `list*`, secret output cautions, conditional evaluation risks. |
| Secrets in Bicep | https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/scenarios-secrets | Last updated 2025-12-22 | Official secret-management guidance; covers secure params, avoiding outputs, Key Vault. |
| RBAC with Bicep | https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/scenarios-rbac | Last updated 2025-12-22 | Official Bicep RBAC guidance; deterministic GUID, smallest scope, principalType. |
| Role assignments templates | https://learn.microsoft.com/en-us/azure/role-based-access-control/role-assignments-template | Last updated 2025-03-30 | Official Azure RBAC guidance; warns `newGuid()` role assignment name is not idempotent. |
| Diagnostic settings | https://learn.microsoft.com/en-us/azure/azure-monitor/platform/diagnostic-settings | Last updated 2026-03-31 | Official Azure Monitor guidance; covers constraints, costs, stale settings, destinations. |
| CLI what-if | https://learn.microsoft.com/en-us/cli/azure/deployment/sub#az-deployment-sub-what-if | Azure CLI latest | Official CLI reference for subscription what-if flags, validation level, result format. |
| ARM what-if behavior | https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/deploy-what-if | Last updated 2025-04-28 | Official what-if limitations, permissions, noise, parsing, change types. |
