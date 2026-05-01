# Multi-dimensional analysis

## Security
- Prefer managed identities over storage keys when possible.
- Do not output `listKeys()` results or Key Vault secret values; outputs land in deployment history.
- Use smallest RBAC scope and set `principalType`, especially for managed identities/service principals.

## Stability / idempotency
- `existing` references do not redeploy resources but fail if name/scope is wrong.
- Role assignments require deterministic GUID names; `newGuid()` causes non-repeatable deployments and `RoleAssignmentExists` conflicts.
- Child resources are safer with `parent`/nested declarations; full names require explicit dependencies and are less type-safe.

## Maintenance
- Diagnostic settings must be removed when resources are renamed/deleted/moved to avoid unexpected reuse if resource names are recreated.
- Category groups can change as Microsoft updates service categories; this is convenient but can change ingestion volume.

## Cost
- Diagnostic settings can materially affect Log Analytics/storage/event hub costs; collect only required categories and avoid platform metrics unless log-query use is needed.

## Validation / operations
- Use subscription-scope what-if as a no-deploy gate; parse JSON/no-pretty output if automating.
- Treat what-if as predictive, not authoritative: expansion limits yield `Ignore`; `reference()` can create false `Modify` noise; Azure defaults may appear as deletes but not actually change.
