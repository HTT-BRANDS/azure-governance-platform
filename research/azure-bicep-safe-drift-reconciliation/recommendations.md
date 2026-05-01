# Recommendations

1. Use `az deployment sub what-if` only as a validation gate for reconciliation PRs; do not combine it with create/deploy in the drift path.
2. Fail the gate on unexpected `Create`, `Delete`, or security-sensitive `Modify`; review `Ignore`, `Unsupported`, and `reference()`-related noise manually.
3. For existing storage containers/file shares, model parent storage account/service scopes explicitly to avoid accidentally managing or replacing parent resources.
4. Avoid making storage account keys the long-term source of truth for application access; if retained for compatibility, treat Key Vault secret value drift as expected after key rotation and protect it from outputs/logs.
5. Seed role assignment GUIDs from stable values: assignment scope, principal object ID, and fully qualified role definition ID.
6. Keep diagnostic settings narrow and destination-valid; audit stale diagnostic settings after resource lifecycle operations.
