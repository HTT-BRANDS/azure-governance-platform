#!/bin/bash
# =============================================================================
# Production Authentication Diagnostics
# =============================================================================
# Diagnoses and fixes common production auth issues for the
# Azure Governance Platform.
#
# Usage: ./scripts/diagnose-production.sh [--fix]
#
# Options:
#   --fix    Automatically apply recommended fixes (interactive)
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Production resource names (from INFRASTRUCTURE_INVENTORY.md)
RG="rg-governance-production"
APP="app-governance-prod"
SQL_SERVER="sql-gov-prod-mylxq53d"
SQL_DB="governance"
TENANT_ID="0c0e35dc-188a-4eb3-b8ba-61752154b407"
CLIENT_ID="1e3e8417-49f1-4d08-b7be-47045d8a12e9"
PROD_URL="https://app-governance-prod.azurewebsites.net"

AUTO_FIX=false
[[ "${1:-}" == "--fix" ]] && AUTO_FIX=true

ISSUES=0
FIXES=()

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Production Authentication Diagnostics${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# ── Pre-flight: Azure CLI ──────────────────────────────────────
echo -e "${YELLOW}Checking Azure CLI...${NC}"
if ! az account show &>/dev/null; then
    echo -e "${RED}✗ Not logged into Azure CLI. Run: az login${NC}"
    exit 1
fi

SUB=$(az account show --query name -o tsv)
echo -e "${GREEN}✓ Logged in: ${SUB}${NC}"
echo ""

# ── Fetch current App Service settings ─────────────────────────
echo -e "${YELLOW}Fetching App Service settings...${NC}"
SETTINGS_JSON=$(az webapp config appsettings list \
    --name "$APP" --resource-group "$RG" -o json 2>/dev/null || echo "[]")

get_setting() {
    echo "$SETTINGS_JSON" | python3 -c "
import json, sys
settings = json.load(sys.stdin)
for s in settings:
    if s['name'] == '$1':
        print(s['value'])
        sys.exit(0)
print('')
" 2>/dev/null
}

check_setting() {
    local name="$1"
    local expected="$2"
    local is_secret="${3:-false}"
    local value
    value=$(get_setting "$name")
    
    if [[ -z "$value" ]]; then
        echo -e "  ${RED}✗ ${name}: NOT SET${NC}"
        ((ISSUES++)) || true
        return 1
    elif [[ "$is_secret" == "true" ]]; then  # pragma: allowlist secret
        echo -e "  ${GREEN}✓ ${name}: ******* (set)${NC}"
        return 0
    elif [[ -n "$expected" && "$value" != "$expected" ]]; then
        echo -e "  ${YELLOW}⚠ ${name}: ${value}${NC}"
        echo -e "    ${YELLOW}Expected: ${expected}${NC}"
        ((ISSUES++)) || true
        return 1
    else
        echo -e "  ${GREEN}✓ ${name}: ${value}${NC}"
        return 0
    fi
}

echo ""
echo -e "${BLUE}── Core Settings ──────────────────────────────────${NC}"
check_setting "ENVIRONMENT" "production"
check_setting "DEBUG" "false"

echo ""
echo -e "${BLUE}── Azure AD Authentication ────────────────────────${NC}"
if ! check_setting "AZURE_AD_TENANT_ID" "$TENANT_ID"; then
    FIXES+=("AZURE_AD_TENANT_ID=$TENANT_ID")
fi

if ! check_setting "AZURE_AD_CLIENT_ID" "$CLIENT_ID"; then
    FIXES+=("AZURE_AD_CLIENT_ID=$CLIENT_ID")
fi

check_setting "AZURE_AD_CLIENT_SECRET" "" "true" || FIXES+=("AZURE_AD_CLIENT_SECRET=<your-client-secret>")

EXPECTED_ISSUER="https://login.microsoftonline.com/${TENANT_ID}/v2.0"
if ! check_setting "AZURE_AD_ISSUER" "$EXPECTED_ISSUER"; then
    FIXES+=("AZURE_AD_ISSUER=$EXPECTED_ISSUER")
fi

EXPECTED_TOKEN_EP="https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token"
if ! check_setting "AZURE_AD_TOKEN_ENDPOINT" "$EXPECTED_TOKEN_EP"; then
    FIXES+=("AZURE_AD_TOKEN_ENDPOINT=$EXPECTED_TOKEN_EP")
fi

EXPECTED_AUTH_EP="https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/authorize"
if ! check_setting "AZURE_AD_AUTHORIZATION_ENDPOINT" "$EXPECTED_AUTH_EP"; then
    FIXES+=("AZURE_AD_AUTHORIZATION_ENDPOINT=$EXPECTED_AUTH_EP")
fi

EXPECTED_JWKS="https://login.microsoftonline.com/${TENANT_ID}/discovery/v2.0/keys"
if ! check_setting "AZURE_AD_JWKS_URI" "$EXPECTED_JWKS"; then
    FIXES+=("AZURE_AD_JWKS_URI=$EXPECTED_JWKS")
fi

echo ""
echo -e "${BLUE}── Security ───────────────────────────────────────${NC}"
check_setting "JWT_SECRET_KEY" "" "true" || FIXES+=("JWT_SECRET_KEY=<generate-with-python>")

if ! check_setting "CORS_ORIGINS" "$PROD_URL"; then
    FIXES+=("CORS_ORIGINS=$PROD_URL")
fi

echo ""
echo -e "${BLUE}── Database ───────────────────────────────────────${NC}"
DB_URL=$(get_setting "DATABASE_URL")
if [[ -z "$DB_URL" ]]; then
    echo -e "  ${RED}✗ DATABASE_URL: NOT SET${NC}"
    ((ISSUES++)) || true
    FIXES+=("DATABASE_URL=mssql+pyodbc://@${SQL_SERVER}.database.windows.net:1433/${SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Authentication=ActiveDirectoryMsi")
elif [[ "$DB_URL" == *"ActiveDirectoryMsi"* ]]; then
    echo -e "  ${GREEN}✓ DATABASE_URL: Azure SQL with Managed Identity${NC}"
elif [[ "$DB_URL" == *"mssql"* ]]; then
    echo -e "  ${YELLOW}⚠ DATABASE_URL: Azure SQL but missing Authentication=ActiveDirectoryMsi${NC}"
    ((ISSUES++)) || true
    FIXES+=("DATABASE_URL=mssql+pyodbc://@${SQL_SERVER}.database.windows.net:1433/${SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Authentication=ActiveDirectoryMsi")
elif [[ "$DB_URL" == *"sqlite"* ]]; then
    echo -e "  ${GREEN}✓ DATABASE_URL: SQLite (${DB_URL})${NC}"
else
    echo -e "  ${YELLOW}⚠ DATABASE_URL: ${DB_URL}${NC}"
fi

echo ""
echo -e "${BLUE}── OIDC / Identity ────────────────────────────────${NC}"
check_setting "USE_OIDC_FEDERATION" "true"
check_setting "OIDC_ALLOW_DEV_FALLBACK" "false"
check_setting "ADMIN_EMAILS" ""

# ── SQL Server Firewall ────────────────────────────────────────
echo ""
echo -e "${BLUE}── SQL Server Firewall ────────────────────────────${NC}"
ALLOW_AZURE=$(az sql server firewall-rule list \
    --server "$SQL_SERVER" --resource-group "$RG" -o json 2>/dev/null | \
    python3 -c "
import json, sys
rules = json.load(sys.stdin)
for r in rules:
    if r.get('startIpAddress') == '0.0.0.0' and r.get('endIpAddress') == '0.0.0.0':
        print('true')
        sys.exit(0)
print('false')
" 2>/dev/null || echo "error")

if [[ "$ALLOW_AZURE" == "true" ]]; then
    echo -e "  ${GREEN}✓ Allow Azure services: Enabled${NC}"
elif [[ "$ALLOW_AZURE" == "false" ]]; then
    echo -e "  ${RED}✗ Allow Azure services: DISABLED${NC}"
    ((ISSUES++)) || true
else
    echo -e "  ${YELLOW}⚠ Could not check firewall rules${NC}"
fi

# ── App Service Managed Identity ───────────────────────────────
echo ""
echo -e "${BLUE}── Managed Identity ───────────────────────────────${NC}"
MI_ID=$(az webapp identity show --name "$APP" --resource-group "$RG" \
    --query principalId -o tsv 2>/dev/null || echo "")
if [[ -n "$MI_ID" ]]; then
    echo -e "  ${GREEN}✓ System-assigned identity: ${MI_ID}${NC}"
else
    echo -e "  ${RED}✗ No system-assigned managed identity${NC}"
    ((ISSUES++)) || true
fi

# ── Summary ────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
if [[ $ISSUES -eq 0 ]]; then
    echo -e "${GREEN}✓ All checks passed! No issues found.${NC}"
else
    echo -e "${RED}Found ${ISSUES} issue(s)${NC}"
fi

if [[ ${#FIXES[@]} -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}Recommended fixes:${NC}"
    echo ""
    echo -e "  az webapp config appsettings set --name $APP --resource-group $RG --settings \\"
    for fix in "${FIXES[@]}"; do
        echo -e "    \"${fix}\" \\"
    done
    echo ""
    
    if [[ "$AUTO_FIX" == "true" ]]; then
        echo -e "${YELLOW}Applying fixes...${NC}"
        SAFE_FIXES=()
        for fix in "${FIXES[@]}"; do
            # Skip placeholder values
            if [[ "$fix" != *"<"* ]]; then
                SAFE_FIXES+=("$fix")
            else
                echo -e "  ${YELLOW}Skipping (needs manual value): ${fix%%=*}${NC}"
            fi
        done
        
        if [[ ${#SAFE_FIXES[@]} -gt 0 ]]; then
            az webapp config appsettings set \
                --name "$APP" --resource-group "$RG" \
                --settings "${SAFE_FIXES[@]}" \
                --output table
            echo ""
            echo -e "${GREEN}✓ Settings applied!${NC}"
            echo -e "${YELLOW}Restarting app service...${NC}"
            az webapp restart --name "$APP" --resource-group "$RG"
            echo -e "${GREEN}✓ App restarted${NC}"
        fi
    else
        echo -e "${YELLOW}Run with --fix to apply automatically, or copy the command above.${NC}"
    fi
fi

# ── Tail logs hint ─────────────────────────────────────────────
echo ""
echo -e "${BLUE}── Helpful Commands ───────────────────────────────${NC}"
echo -e "  # View live production logs:"
echo -e "  az webapp log tail --name $APP --resource-group $RG"
echo ""
echo -e "  # Check detailed health:"
echo -e "  curl -s ${PROD_URL}/health/detailed | python3 -m json.tool"
echo ""
echo -e "  # Test auth endpoint:"
echo -e "  curl -s ${PROD_URL}/api/v1/auth/health | python3 -m json.tool"
echo ""
echo -e "  # Restart after fixes:"
echo -e "  az webapp restart --name $APP --resource-group $RG"
echo ""
