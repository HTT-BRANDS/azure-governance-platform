# Azure/Bicep Safe Drift Reconciliation Research

## Scope
Concise cautions for safe drift reconciliation without deployment in this Control Tower Azure/Bicep project.

## Key findings
- Model live Azure resources with Bicep `existing` to prevent accidental redeployment, but treat missing names/scopes as hard validation failures.
- Child resources such as blob containers and file shares should be modeled with `parent`/nested resources, not full slash-delimited names, to keep type safety and dependencies clear.
- Storage-key-derived Key Vault secrets are sensitive drift vectors: avoid secret outputs/deployment history exposure; prefer managed identity where possible; expect key rotation to surface as secret value churn.
- Role assignment names must be deterministic GUIDs seeded with scope + principal + role definition; `newGuid()` breaks idempotency and causes conflicts.
- Diagnostic settings are extension resources with destination and category constraints; watch for noisy/expensive `allLogs` and stale diagnostic settings after resource rename/delete.
- `az deployment sub what-if` is appropriate as a no-change validation gate, but requires deployment permissions, has expansion limits, may report noise for unresolved `reference()`, and must be parsed conservatively.

## Project context
Project uses Bicep under `infrastructure/`, Key Vault, storage, RBAC modules, Log Analytics/Application Insights, and GitHub Actions. `core_stack.yaml` identifies Bicep as IaC and notes scheduled Bicep drift detection.
