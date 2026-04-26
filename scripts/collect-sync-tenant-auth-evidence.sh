#!/bin/bash
# =============================================================================
# Sync Tenant Auth Evidence Collector (issue 918b)
# =============================================================================
# Read-only helper that exports the Azure metadata needed to classify the
# five noisy production tenants from issue 918b.
#
# What it does:
#   - verifies Azure CLI auth
#   - creates a timestamped evidence directory
#   - exports production App Service app-settings metadata
#   - exports Key Vault secret names only (never values)
#   - writes SQL and KQL query files for manual/optional execution
#   - writes an executable classifier wrapper for the five impacted tenants
#
# What it does NOT do:
#   - mutate Azure resources
#   - fetch Key Vault secret values
#   - write to the production database
#   - pretend the issue is solved before evidence exists
#
# Usage:
#   ./scripts/collect-sync-tenant-auth-evidence.sh
#   ./scripts/collect-sync-tenant-auth-evidence.sh --output-dir artifacts/918b
#   APP_INSIGHTS_APP=<name-or-id> ./scripts/collect-sync-tenant-auth-evidence.sh
# =============================================================================

set -euo pipefail

PROD_RG="${PROD_RG:-rg-governance-production}"
PROD_APP="${PROD_APP:-app-governance-prod}"
PROD_KV="${PROD_KV:-kv-gov-prod}"
APP_INSIGHTS_APP="${APP_INSIGHTS_APP:-}"
OUTPUT_ROOT="${OUTPUT_ROOT:-artifacts/918b}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTDIR="${OUTPUT_ROOT}/${TIMESTAMP}"

TENANT_IDS=(
  "ce62e17d-2feb-4e67-a115-8ea4af68da30"
  "0c0e35dc-188a-4eb3-b8ba-61752154b407"
  "3c7d2bf3-b597-4766-b5cb-2b489c2904d6"
  "b5380912-79ec-452d-a6ca-6d897b19b294"
  "98723287-044b-4bbb-9294-19857d4128a0"
)

usage() {
  sed -n '2,25p' "$0"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

write_text_file() {
  local file_path="$1"
  shift
  cat > "$file_path" <<EOF
$*
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      if [[ -z "${2:-}" ]]; then
        echo "--output-dir requires a path" >&2
        exit 1
      fi
      OUTPUT_ROOT="$2"
      OUTDIR="${OUTPUT_ROOT}/${TIMESTAMP}"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

require_command az
require_command python

if ! az account show >/dev/null 2>&1; then
  echo "Azure CLI is not authenticated. Run: az login" >&2
  exit 1
fi

mkdir -p "$OUTDIR"

APP_SETTINGS_JSON="$OUTDIR/prod-app-settings.json"
KV_SECRET_NAMES_JSON="$OUTDIR/prod-keyvault-secret-names.json"
TENANTS_SQL="$OUTDIR/prod-tenants-export.sql"
LOG_SIGNATURES_KQL="$OUTDIR/log-signatures.kql"
TRACES_KQL="$OUTDIR/sync-traces.kql"
CLASSIFIER_CMD_SH="$OUTDIR/run-classifier.sh"
README_MD="$OUTDIR/README.md"

printf 'Collecting 918b evidence into %s\n' "$OUTDIR"

az webapp config appsettings list \
  --resource-group "$PROD_RG" \
  --name "$PROD_APP" \
  -o json | python -c "import json, sys
SAFE_VALUE_NAMES = {
    'ENVIRONMENT', 'DEBUG', 'LOG_LEVEL', 'PORT', 'WEBSITES_PORT',
    'AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'USE_UAMI_AUTH',
    'USE_OIDC_FEDERATION', 'OIDC_ALLOW_DEV_FALLBACK', 'KEY_VAULT_URL',
    'TENANTS_CONFIG_PATH', 'DEPLOY_TIMESTAMP'
}
PRESENCE_ONLY_NAMES = {
    'AZURE_CLIENT_SECRET', 'AZURE_AD_CLIENT_SECRET', 'DATABASE_URL',
    'JWT_SECRET_KEY', 'APPINSIGHTS_INSTRUMENTATIONKEY',
    'APPLICATIONINSIGHTS_CONNECTION_STRING', 'DOCKER_REGISTRY_SERVER_PASSWORD'
}
def sanitize(item):
    if not isinstance(item, dict):
        return item
    result = dict(item)
    name = str(item.get('name') or '')
    value = item.get('value')
    if name in SAFE_VALUE_NAMES:
        return result
    if name in PRESENCE_ONLY_NAMES or any(token in name for token in ('SECRET', 'PASSWORD', 'TOKEN', 'KEY')):
        result['value'] = '__PRESENT__' if value not in (None, '') else None
        return result
    result['value'] = value
    return result
payload = json.load(sys.stdin)
json.dump([sanitize(item) for item in payload], sys.stdout, indent=2)
sys.stdout.write('\\n')" > "$APP_SETTINGS_JSON"

az keyvault secret list \
  --vault-name "$PROD_KV" \
  --query '[].{name:name}' \
  -o json > "$KV_SECRET_NAMES_JSON"

write_text_file "$TENANTS_SQL" "-- Export these rows from production DB as JSON and save to:
-- $OUTDIR/prod-tenants.json
--
-- Required columns for issue 918b classification:
SELECT
    name,
    tenant_id,
    is_active,
    use_lighthouse,
    use_oidc,
    client_id,
    client_secret_ref
FROM tenants
WHERE tenant_id IN (
    'ce62e17d-2feb-4e67-a115-8ea4af68da30',
    '0c0e35dc-188a-4eb3-b8ba-61752154b407',
    '3c7d2bf3-b597-4766-b5cb-2b489c2904d6',
    'b5380912-79ec-452d-a6ca-6d897b19b294',
    '98723287-044b-4bbb-9294-19857d4128a0'
)
ORDER BY name;
"

write_text_file "$LOG_SIGNATURES_KQL" "traces
| where timestamp > ago(24h)
| where message has_any (
    'invalid_tenant',
    'Key Vault credentials not found',
    'falling back to settings credentials',
    'not configured for per-tenant Key Vault credentials'
)
| project timestamp, severityLevel, message, operation_Name, cloud_RoleName
| order by timestamp desc
"

write_text_file "$TRACES_KQL" "traces
| where timestamp > ago(24h)
| where message has_any (
    'cost sync',
    'compliance sync',
    'resource sync',
    'identity sync',
    'Error processing tenant'
)
| project timestamp, severityLevel, message, operation_Name, cloud_RoleName
| order by timestamp desc
"

cat > "$CLASSIFIER_CMD_SH" <<EOF
#!/bin/bash
set -euo pipefail

uv run python scripts/investigate_sync_tenant_auth.py \
  --tenants-json "$OUTDIR/prod-tenants.json" \
  --app-settings-json "$APP_SETTINGS_JSON" \
  --keyvault-secrets-json "$KV_SECRET_NAMES_JSON" \
  --tenant-id "${TENANT_IDS[0]}" \
  --tenant-id "${TENANT_IDS[1]}" \
  --tenant-id "${TENANT_IDS[2]}" \
  --tenant-id "${TENANT_IDS[3]}" \
  --tenant-id "${TENANT_IDS[4]}" \
  --output-json "$OUTDIR/tenant-auth-investigation-918b.json" \
  --output-md "$OUTDIR/tenant-auth-investigation-918b.md"
EOF
chmod +x "$CLASSIFIER_CMD_SH"

OPTIONAL_APP_INSIGHTS_LINES=""
if [[ -n "$APP_INSIGHTS_APP" ]]; then
  OPTIONAL_APP_INSIGHTS_LINES=$'- log-signatures.json — exported App Insights log signature query\n- sync-traces.json — exported App Insights sync traces query'
fi

cat > "$README_MD" <<EOF
# 918b evidence bundle

## Context

- UTC timestamp: $TIMESTAMP
- Resource group: $PROD_RG
- App Service: $PROD_APP
- Key Vault: $PROD_KV

## Automatically collected

- prod-app-settings.json — App Service settings metadata export
- prod-keyvault-secret-names.json — Key Vault secret names only
$OPTIONAL_APP_INSIGHTS_LINES

## Query scaffolding

- prod-tenants-export.sql — SQL to export the five impacted tenant rows
- log-signatures.kql — KQL for fallback/auth signature evidence
- sync-traces.kql — KQL for broader sync trace evidence
- run-classifier.sh — exact classifier invocation for the five tenant IDs

## Still needed manually

1. Export production tenant rows to $OUTDIR/prod-tenants.json using prod-tenants-export.sql
2. If App Insights JSON was not exported automatically, run the KQL in log-signatures.kql and sync-traces.kql
3. Run the classifier: $CLASSIFIER_CMD_SH
4. Attach the generated JSON and Markdown outputs to issue azure-governance-platform-918b

## Reference

- docs/runbooks/sync-tenant-auth-investigation-918b.md
EOF

if [[ -n "$APP_INSIGHTS_APP" ]]; then
  az monitor app-insights query \
    --app "$APP_INSIGHTS_APP" \
    --analytics-query "$(cat "$LOG_SIGNATURES_KQL")" \
    -o json > "$OUTDIR/log-signatures.json"

  az monitor app-insights query \
    --app "$APP_INSIGHTS_APP" \
    --analytics-query "$(cat "$TRACES_KQL")" \
    -o json > "$OUTDIR/sync-traces.json"
fi

cat <<EOF

Done. Evidence scaffold is ready:
  $OUTDIR

Collected automatically:
  - $APP_SETTINGS_JSON
  - $KV_SECRET_NAMES_JSON
$(if [[ -n "$APP_INSIGHTS_APP" ]]; then printf '  - %s/log-signatures.json\n  - %s/sync-traces.json\n' "$OUTDIR" "$OUTDIR"; fi)
Still needed manually:
  - $OUTDIR/prod-tenants.json   (run the SQL in $TENANTS_SQL)

Then run:
  $CLASSIFIER_CMD_SH

Reference runbook:
  docs/runbooks/sync-tenant-auth-investigation-918b.md
EOF
