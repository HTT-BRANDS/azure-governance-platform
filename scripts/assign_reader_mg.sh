#!/usr/bin/env bash
#
# assign_reader_mg.sh — grant Reader on root management group to the
# HTT Brands multi-tenant app's service principal in every active tenant
# listed in config/tenants.yaml.
#
# Prereqs:
#   - az CLI logged in (az login) with an identity that is Global Admin or
#     has Microsoft.Authorization/roleAssignments/write on each tenant's
#     root management group.
#   - yq installed (https://mikefarah.gitbook.io/yq) for YAML parsing.
#   - The multi-tenant app is already consented in each tenant (run
#     scripts/verify_consent_status.py first).
#
# Idempotent — `az role assignment create` returns a conflict status if
# the assignment already exists; this script suppresses that specific case
# and continues.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/config/tenants.yaml"
if [[ ! -f "${CONFIG_FILE}" ]]; then
  CONFIG_FILE="${ROOT_DIR}/config/tenants.yaml.example"
  echo "WARN: using example config — placeholder IDs will fail. Copy to config/tenants.yaml first." >&2
fi

APP_ID="${HTT_APP_ID:-}"
if [[ -z "${APP_ID}" ]]; then
  # Try to extract from the first tenant entry's multi_tenant_app_id.
  APP_ID="$(yq eval '.multi_tenant_app_id // (.tenants | to_entries | .[0].value.multi_tenant_app_id // .[0].value.app_id)' "${CONFIG_FILE}" || true)"
fi

if [[ -z "${APP_ID}" || "${APP_ID}" == "null" ]]; then
  echo "ERROR: Unable to resolve HTT app ID. Set HTT_APP_ID or add multi_tenant_app_id to config/tenants.yaml." >&2
  exit 2
fi

echo "Using multi-tenant app id: ${APP_ID}"

TENANT_CODES=$(yq eval '.tenants | keys | .[]' "${CONFIG_FILE}")

for code in ${TENANT_CODES}; do
  tenant_id=$(yq eval ".tenants.${code}.tenant_id" "${CONFIG_FILE}")
  is_active=$(yq eval ".tenants.${code}.is_active // true" "${CONFIG_FILE}")
  if [[ "${is_active}" != "true" ]]; then
    echo "• ${code}: inactive, skipping"
    continue
  fi

  echo
  echo "=== ${code} (${tenant_id}) ==="

  # Switch az context to this tenant.
  if ! az login --tenant "${tenant_id}" --only-show-errors >/dev/null 2>&1; then
    echo "  ✗ az login failed for tenant ${tenant_id}" >&2
    continue
  fi

  # Resolve SP objectId in this tenant.
  sp_object_id=$(az ad sp show --id "${APP_ID}" --query id -o tsv 2>/dev/null || true)
  if [[ -z "${sp_object_id}" ]]; then
    echo "  ✗ Service principal for ${APP_ID} not found in ${code} — consent the app first"
    continue
  fi

  # Assign Reader on the root management group (which is named the same as
  # the tenant id by default).
  scope="/providers/Microsoft.Management/managementGroups/${tenant_id}"
  if az role assignment create \
      --assignee-object-id "${sp_object_id}" \
      --assignee-principal-type ServicePrincipal \
      --role "Reader" \
      --scope "${scope}" \
      --only-show-errors 2>/tmp/assign.err; then
    echo "  ✓ Reader assigned at ${scope}"
  else
    if grep -qi "already exists" /tmp/assign.err; then
      echo "  ✓ Reader already present at ${scope}"
    else
      echo "  ✗ Failed: $(cat /tmp/assign.err)" >&2
    fi
  fi
done

echo
echo "Done. Re-run scripts/verify_consent_status.py to confirm."
