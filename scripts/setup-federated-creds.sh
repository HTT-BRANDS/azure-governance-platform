#!/usr/bin/env bash
# scripts/setup-federated-creds.sh
#
# Configures OIDC Federated Identity Credentials on all 5 Riverside app registrations.
# This allows the App Service Managed Identity to authenticate to each tenant without secrets.
#
# USAGE:
#   ./scripts/setup-federated-creds.sh \
#     --managing-tenant-id <HTT_tenant_id> \
#     --mi-object-id <managed_identity_object_id> \
#     [--verify-only] \
#     [--tenant HTT|BCC|FN|TLL|DCE] \
#     [--name <federated-credential-name>]
#
# PREREQUISITES:
#   - Azure CLI installed and logged in
#   - Admin access in each tenant (Global Admin or Application Administrator)
#   - The managed identity object ID from the App Service
#
# NOTE: Requires bash 3.2+ (macOS default). No associative arrays used.

set -euo pipefail

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✓${RESET} $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET} $*"; }
err()  { echo -e "  ${RED}✗${RESET} $*" >&2; }
hdr()  { echo -e "\n${BOLD}${CYAN}$*${RESET}"; }

validate_uuid() {
    local val="$1"
    local label="$2"
    if ! echo "$val" | grep -qE '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'; then
        err "$label must be a valid UUID (got: $val)"
        echo "  Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" >&2
        exit 1
    fi
}

to_upper() { echo "$1" | tr '[:lower:]' '[:upper:]'; }

# ---------------------------------------------------------------------------
# Tenant lookup functions (matches app/core/tenants_config.py)
# ---------------------------------------------------------------------------
TENANT_ORDER="HTT BCC FN TLL DCE"

get_tenant_id() {
    case "$1" in
        HTT) echo "0c0e35dc-188a-4eb3-b8ba-61752154b407" ;;
        BCC) echo "b5380912-79ec-452d-a6ca-6d897b19b294" ;;
        FN)  echo "98723287-044b-4bbb-9294-19857d4128a0" ;;
        TLL) echo "3c7d2bf3-b597-4766-b5cb-2b489c2904d6" ;;
        DCE) echo "ce62e17d-2feb-4e67-a115-8ea4af68da30" ;;
        *)   return 1 ;;
    esac
}

get_app_id() {
    case "$1" in
        HTT) echo "1e3e8417-49f1-4d08-b7be-47045d8a12e9" ;;
        BCC) echo "4861906b-2079-4335-923f-a55cc0e44d64" ;;
        FN)  echo "7648d04d-ccc4-43ac-bace-da1b68bf11b4" ;;
        TLL) echo "52531a02-78fd-44ba-9ab9-b29675767955" ;;
        DCE) echo "79c22a10-3f2d-4e6a-bddc-ee65c9a46cb0" ;;
        *)   return 1 ;;
    esac
}

is_valid_code() {
    case "$1" in
        HTT|BCC|FN|TLL|DCE) return 0 ;;
        *) return 1 ;;
    esac
}

set_status() {
    # set_status CODE VALUE — stores STATUS_<CODE>=VALUE
    eval "STATUS_${1}=\"${2}\""
}

get_status() {
    eval "echo \"\${STATUS_${1}:-SKIPPED}\""
}

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
MANAGING_TENANT_ID=""
MI_OBJECT_ID=""
VERIFY_ONLY=false
FILTER_TENANT=""
CRED_NAME="governance-platform-app-service"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --managing-tenant-id)
            MANAGING_TENANT_ID="$2"; shift 2 ;;
        --mi-object-id)
            MI_OBJECT_ID="$2"; shift 2 ;;
        --verify-only)
            VERIFY_ONLY=true; shift ;;
        --tenant)
            FILTER_TENANT=$(to_upper "$2"); shift 2 ;;
        --name)
            CRED_NAME="$2"; shift 2 ;;
        -h|--help)
            grep '^#' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *)
            err "Unknown argument: $1"
            exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
if [ -z "$MANAGING_TENANT_ID" ]; then
    err "--managing-tenant-id is required"
    exit 1
fi

if [ -z "$MI_OBJECT_ID" ]; then
    err "--mi-object-id is required"
    exit 1
fi

if [ -n "$FILTER_TENANT" ] && ! is_valid_code "$FILTER_TENANT"; then
    err "Unknown tenant code: $FILTER_TENANT. Valid: HTT BCC FN TLL DCE"
    exit 1
fi

validate_uuid "$MANAGING_TENANT_ID" "--managing-tenant-id"
validate_uuid "$MI_OBJECT_ID" "--mi-object-id"

# ---------------------------------------------------------------------------
# Build work list
# ---------------------------------------------------------------------------
if [ -n "$FILTER_TENANT" ]; then
    WORK_LIST="$FILTER_TENANT"
else
    WORK_LIST="$TENANT_ORDER"
fi

ISSUER="https://login.microsoftonline.com/${MANAGING_TENANT_ID}/v2.0"

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
hdr "=== OIDC Federated Credential Setup ==="
echo "  Managing Tenant : ${MANAGING_TENANT_ID}"
echo "  MI Object ID    : ${MI_OBJECT_ID}"
echo "  Credential Name : ${CRED_NAME}"
echo "  Issuer          : ${ISSUER}"
echo "  Verify Only     : ${VERIFY_ONLY}"
echo "  Tenants         : ${WORK_LIST}"

for CODE in $WORK_LIST; do
    TENANT_ID=$(get_tenant_id "$CODE")
    APP_ID=$(get_app_id "$CODE")

    hdr "── Tenant: ${CODE} (${TENANT_ID})"
    echo "   App ID: ${APP_ID}"

    # Log in to the target tenant
    echo "   Logging in..."
    if ! az login --tenant "$TENANT_ID" --allow-no-subscriptions --output none 2>/dev/null; then
        err "Failed to log in to tenant ${CODE} (${TENANT_ID})"
        set_status "$CODE" "FAIL"
        continue
    fi
    ok "Logged in to ${CODE}"

    # Check if federated credential already exists
    EXISTING=$(az ad app federated-credential list --id "$APP_ID" \
        --query "[?name=='${CRED_NAME}'].name" --output tsv 2>/dev/null || true)

    if [ -n "$EXISTING" ]; then
        # Credential exists — validate it
        EXISTING_ISSUER=$(az ad app federated-credential list --id "$APP_ID" \
            --query "[?name=='${CRED_NAME}'].issuer" --output tsv 2>/dev/null || true)
        EXISTING_SUBJECT=$(az ad app federated-credential list --id "$APP_ID" \
            --query "[?name=='${CRED_NAME}'].subject" --output tsv 2>/dev/null || true)

        if [ "$EXISTING_ISSUER" = "$ISSUER" ] && [ "$EXISTING_SUBJECT" = "$MI_OBJECT_ID" ]; then
            warn "Credential '${CRED_NAME}' already exists and is correctly configured"
            set_status "$CODE" "EXISTS_OK"
        else
            warn "Credential '${CRED_NAME}' exists but may be misconfigured"
            echo "     Expected issuer  : ${ISSUER}"
            echo "     Actual issuer    : ${EXISTING_ISSUER}"
            echo "     Expected subject : ${MI_OBJECT_ID}"
            echo "     Actual subject   : ${EXISTING_SUBJECT}"
            set_status "$CODE" "EXISTS_MISMATCH"
        fi
        continue
    fi

    if [ "$VERIFY_ONLY" = true ]; then
        err "Credential '${CRED_NAME}' does NOT exist in tenant ${CODE}"
        set_status "$CODE" "MISSING"
        continue
    fi

    # Create the federated credential
    echo "   Creating federated credential '${CRED_NAME}'..."
    PARAMS="{\"name\":\"${CRED_NAME}\",\"issuer\":\"${ISSUER}\",\"subject\":\"${MI_OBJECT_ID}\",\"audiences\":[\"api://AzureADTokenExchange\"]}"

    if az ad app federated-credential create --id "$APP_ID" --parameters "$PARAMS" --output none 2>/dev/null; then
        ok "Created federated credential '${CRED_NAME}' in tenant ${CODE}"
        set_status "$CODE" "CREATED"
    else
        err "Failed to create federated credential in tenant ${CODE}"
        set_status "$CODE" "FAIL"
    fi
done

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
hdr "=== Summary ==="
printf "%-6s  %-40s  %-40s  %s\n" "CODE" "TENANT_ID" "APP_ID" "STATUS"
printf "%-6s  %-40s  %-40s  %s\n" "------" "----------------------------------------" "----------------------------------------" "-------"

OVERALL_EXIT=0
for CODE in $WORK_LIST; do
    STATE=$(get_status "$CODE")
    TENANT_ID=$(get_tenant_id "$CODE")
    APP_ID=$(get_app_id "$CODE")
    case "$STATE" in
        CREATED|EXISTS_OK)
            INDICATOR="${GREEN}${STATE}${RESET}" ;;
        EXISTS_MISMATCH|MISSING)
            INDICATOR="${YELLOW}${STATE}${RESET}"
            OVERALL_EXIT=1 ;;
        FAIL)
            INDICATOR="${RED}${STATE}${RESET}"
            OVERALL_EXIT=1 ;;
        *)
            INDICATOR="$STATE" ;;
    esac
    printf "%-6s  %-40s  %-40s  " "$CODE" "$TENANT_ID" "$APP_ID"
    echo -e "${INDICATOR}"
done

echo ""
if [ $OVERALL_EXIT -eq 0 ]; then
    ok "All tenants configured successfully"
else
    err "One or more tenants failed — review output above"
fi

exit $OVERALL_EXIT
