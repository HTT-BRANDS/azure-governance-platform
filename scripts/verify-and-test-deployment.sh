#!/bin/bash
# =============================================================================
# Azure Governance Platform - Comprehensive Deployment Verification & Testing
# =============================================================================
# Usage: ./scripts/verify-and-test-deployment.sh [OPTIONS]
#
# This script performs comprehensive deployment verification and testing:
# 1. Verify Azure resources are deployed (SQL, App Service, Redis if applicable)
# 2. Check App Service is running and responding
# 3. Run database migrations (Alembic)
# 4. Seed test data if needed
# 5. Run health checks
# 6. Run basic API tests
# 7. Generate detailed deployment report
#
# Options:
#   --environment ENV      Environment (dev, staging, prod) [default: dev]
#   --url URL              App Service URL to test
#   --skip-migrations      Skip database migrations
#   --skip-seeding         Skip test data seeding
#   --skip-api-tests       Skip API smoke tests
#   --verbose, -v          Enable verbose output
#   --generate-report      Generate JSON report file
#   --report-path PATH     Custom report path
#
# Exit Codes:
#   0 - All checks passed (deployment healthy)
#   1 - Critical checks failed (deployment unhealthy)
#   2 - Configuration or runtime error
#
# Examples:
#   ./scripts/verify-and-test-deployment.sh --environment dev --verbose
#   ./scripts/verify-and-test-deployment.sh --environment prod --url https://app-governance-prod.azurewebsites.net
#   ./scripts/verify-and-test-deployment.sh --environment staging --skip-migrations --generate-report
# =============================================================================

set -euo pipefail

# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

# Environment settings
ENVIRONMENT="${ENVIRONMENT:-dev}"
VERBOSE=false
SKIP_MIGRATIONS=false
SKIP_SEEDING=false
SKIP_API_TESTS=false
GENERATE_REPORT=false
REPORT_PATH=""

# Azure resource names (will be auto-detected or set via env vars)
RESOURCE_GROUP="${RESOURCE_GROUP:-}"
APP_SERVICE="${APP_SERVICE:-}"
SQL_SERVER="${SQL_SERVER:-}"
SQL_DB="${SQL_DB:-governance}"
REDIS_CACHE="${REDIS_CACHE:-}"
KEY_VAULT="${KEY_VAULT:-}"

# App URL (auto-detected from App Service if not provided)
APP_URL="${APP_URL:-}"

# Test configuration
TIMEOUT="${TIMEOUT:-30}"
MAX_RETRIES="${MAX_RETRIES:-3}"
RETRY_DELAY="${RETRY_DELAY:-5}"
EXPECTED_TENANT_COUNT="${EXPECTED_TENANT_COUNT:-5}"

# Database migration settings
ALEMBIC_INI="${ALEMBIC_INI:-alembic.ini}"

# Report settings
REPORT_TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
REPORT_DIR="${REPORT_DIR:-./reports}"

# =============================================================================
# COLOR OUTPUT
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# =============================================================================
# STATE TRACKING
# =============================================================================

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0
WARNINGS=0
START_TIME=$(date +%s)

# Report data structure
REPORT_DATA='{"timestamp":"","environment":"","url":"","tests":[],"summary":{},"azure_resources":{},"database":{},"health_checks":{},"api_tests":{}}'

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    if [[ "$VERBOSE" == true ]]; then
        verbose_log "$1"
    fi
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++)) || true
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++)) || true
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++)) || true
}

log_skip() {
    echo -e "${CYAN}[SKIP]${NC} $1"
    ((TESTS_SKIPPED++)) || true
}

log_section() {
    echo ""
    echo -e "${MAGENTA}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}══════════════════════════════════════════════════════════════${NC}"
}

verbose_log() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${CYAN}[VERBOSE]${NC} $1"
    fi
}

# =============================================================================
# PRINT FUNCTIONS
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${BOLD}     Azure Governance Platform - Deployment Verification${NC}${BLUE}        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BOLD}Environment:${NC}     ${CYAN}${ENVIRONMENT}${NC}"
    echo -e "  ${BOLD}Target URL:${NC}      ${CYAN}${APP_URL:-"(auto-detect)"}${NC}"
    echo -e "  ${BOLD}Timestamp:${NC}       ${CYAN}$(date -u +"%Y-%m-%d %H:%M:%S UTC")${NC}"
    echo -e "  ${BOLD}Script Version:${NC}  ${CYAN}1.0.0${NC}"
    echo ""
}

print_configuration() {
    [[ "$VERBOSE" != true ]] && return
    
    echo -e "${CYAN}┌─ Configuration ─────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} Resource Group:  ${RESOURCE_GROUP:-"(auto-detect)"}"
    echo -e "${CYAN}│${NC} App Service:     ${APP_SERVICE:-"(auto-detect)"}"
    echo -e "${CYAN}│${NC} SQL Server:      ${SQL_SERVER:-"(auto-detect/none)"}"
    echo -e "${CYAN}│${NC} SQL Database:    ${SQL_DB}"
    echo -e "${CYAN}│${NC} Redis Cache:     ${REDIS_CACHE:-"(auto-detect/none)"}"
    echo -e "${CYAN}│${NC} Key Vault:       ${KEY_VAULT:-"(auto-detect/none)"}"
    echo -e "${CYAN}│${NC} Skip Migrations: ${SKIP_MIGRATIONS}"
    echo -e "${CYAN}│${NC} Skip Seeding:    ${SKIP_SEEDING}"
    echo -e "${CYAN}│${NC} Skip API Tests:  ${SKIP_API_TESTS}"
    echo -e "${CYAN}│${NC} Generate Report: ${GENERATE_REPORT}"
    echo -e "${CYAN}└────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

check_dependency() {
    local cmd=$1
    local name=${2:-$1}
    local required=${3:-false}
    
    if check_command "$cmd"; then
        verbose_log "$name is available"
        return 0
    else
        if [[ "$required" == true ]]; then
            log_failure "$name is required but not installed"
            exit 2
        else
            log_warning "$name is not installed. Some checks will be skipped."
            return 1
        fi
    fi
}

make_request() {
    local url=$1
    local method=${2:-GET}
    local headers=${3:-}
    local data=${4:-}
    local follow_redirects=${5:-false}
    
    local curl_args=(
        -s -w "\n%{http_code}\n%{time_total}"
        --max-time "$TIMEOUT"
        -X "$method"
    )
    
    [[ "$follow_redirects" == true ]] && curl_args+=(-L)
    
    if [[ -n "$headers" ]]; then
        IFS='|' read -ra HEADER_ARRAY <<< "$headers"
        for header in "${HEADER_ARRAY[@]}"; do
            curl_args+=(-H "$header")
        done
    fi
    
    if [[ -n "$data" ]]; then
        curl_args+=(-d "$data")
    fi
    
    curl_args+=("$url")
    
    local response
    response=$(curl "${curl_args[@]}" 2>/dev/null || echo -e "\n000\n0")
    echo "$response"
}

retry_request() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3
    local max_attempts=${4:-$MAX_RETRIES}
    local follow_redirects=${5:-false}
    
    local attempt=0
    local http_code="000"
    local response=""
    local body=""
    local response_time="0"
    
    while [[ $attempt -lt $max_attempts ]]; do
        response=$(make_request "$url" "GET" "" "" "$follow_redirects")
        http_code=$(echo "$response" | tail -n2 | head -n1)
        response_time=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d' | sed '$d')
        
        if [[ "$http_code" == "$expected_status" ]]; then
            echo -e "${body}\n${http_code}\n${response_time}"
            return 0
        fi
        
        ((attempt++)) || true
        if [[ $attempt -lt $max_attempts ]]; then
            log_info "Retry $attempt/$max_attempts for $description..."
            sleep "$RETRY_DELAY"
        fi
    done
    
    echo -e "${body}\n${http_code}\n${response_time}"
    return 1
}

parse_json() {
    local json=$1
    local query=$2
    echo "$json" | jq -r "$query" 2>/dev/null || echo "null"
}

format_duration() {
    local seconds=$1
    if (( $(echo "$seconds < 1" | bc -l) )); then
        printf "%.0fms" "$(echo "$seconds * 1000" | bc)"
    else
        printf "%.2fs" "$seconds"
    fi
}

# =============================================================================
# AZURE RESOURCE DETECTION
# =============================================================================

detect_azure_resources() {
    log_section "AZURE RESOURCE DETECTION"
    
    if ! check_command az; then
        log_skip "Azure CLI not available - skipping Azure resource detection"
        return
    fi
    
    # Check if logged in with timeout (prevents hanging on browser-based auth)
    local azure_logged_in=false
    if timeout 3 az account show &>/dev/null; then
        azure_logged_in=true
    fi
    
    if [[ "$azure_logged_in" != true ]]; then
        log_skip "Not logged into Azure - skipping Azure resource detection"
        log_info "Run 'az login' to enable Azure resource verification"
        return
    fi
    
    log_info "Detecting Azure resources for environment: $ENVIRONMENT"
    
    # Detect resource group
    if [[ -z "$RESOURCE_GROUP" ]]; then
        RESOURCE_GROUP=$(az group list --query "[?contains(name, 'governance') && contains(name, '$ENVIRONMENT')].name | [0]" -o tsv 2>/dev/null || echo "")
        if [[ -z "$RESOURCE_GROUP" ]]; then
            RESOURCE_GROUP=$(az group list --query "[?contains(name, 'governance')].name | [0]" -o tsv 2>/dev/null || echo "")
        fi
        if [[ -n "$RESOURCE_GROUP" ]]; then
            log_success "Detected Resource Group: $RESOURCE_GROUP"
        else
            log_warning "Could not detect Resource Group"
        fi
    else
        log_success "Using configured Resource Group: $RESOURCE_GROUP"
    fi
    
    # Detect App Service
    if [[ -z "$APP_SERVICE" && -n "$RESOURCE_GROUP" ]]; then
        APP_SERVICE=$(az webapp list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'governance')].name | [0]" -o tsv 2>/dev/null || echo "")
        if [[ -n "$APP_SERVICE" ]]; then
            log_success "Detected App Service: $APP_SERVICE"
        else
            log_warning "Could not detect App Service"
        fi
    elif [[ -n "$APP_SERVICE" ]]; then
        log_success "Using configured App Service: $APP_SERVICE"
    fi
    
    # Detect SQL Server
    if [[ -z "$SQL_SERVER" && -n "$RESOURCE_GROUP" ]]; then
        SQL_SERVER=$(az sql server list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'gov') || contains(name, 'governance')].name | [0]" -o tsv 2>/dev/null || echo "")
        if [[ -n "$SQL_SERVER" ]]; then
            log_success "Detected SQL Server: $SQL_SERVER"
        else
            log_info "No SQL Server detected (may use SQLite)"
        fi
    elif [[ -n "$SQL_SERVER" ]]; then
        log_success "Using configured SQL Server: $SQL_SERVER"
    fi
    
    # Detect Redis Cache
    if [[ -z "$REDIS_CACHE" && -n "$RESOURCE_GROUP" ]]; then
        REDIS_CACHE=$(az redis list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
        if [[ -n "$REDIS_CACHE" ]]; then
            log_success "Detected Redis Cache: $REDIS_CACHE"
        else
            log_info "No Redis Cache detected"
        fi
    elif [[ -n "$REDIS_CACHE" ]]; then
        log_success "Using configured Redis Cache: $REDIS_CACHE"
    fi
    
    # Detect Key Vault
    if [[ -z "$KEY_VAULT" && -n "$RESOURCE_GROUP" ]]; then
        KEY_VAULT=$(az keyvault list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'gov') || contains(name, 'governance')].name | [0]" -o tsv 2>/dev/null || echo "")
        if [[ -n "$KEY_VAULT" ]]; then
            log_success "Detected Key Vault: $KEY_VAULT"
        else
            log_info "No Key Vault detected"
        fi
    elif [[ -n "$KEY_VAULT" ]]; then
        log_success "Using configured Key Vault: $KEY_VAULT"
    fi
    
    # Detect App URL
    if [[ -z "$APP_URL" && -n "$APP_SERVICE" && -n "$RESOURCE_GROUP" ]]; then
        APP_URL=$(az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "defaultHostName" -o tsv 2>/dev/null || echo "")
        if [[ -n "$APP_URL" ]]; then
            APP_URL="https://$APP_URL"
            log_success "Detected App URL: $APP_URL"
        else
            log_warning "Could not detect App URL"
        fi
    elif [[ -n "$APP_URL" ]]; then
        log_success "Using configured App URL: $APP_URL"
    fi
}

# =============================================================================
# AZURE RESOURCE VERIFICATION
# =============================================================================

verify_app_service() {
    log_section "VERIFYING APP SERVICE"
    
    if ! check_command az; then
        log_skip "Azure CLI not available"
        return
    fi
    
    # Quick login check with timeout
    if ! timeout 3 az account show &>/dev/null; then
        log_skip "Not logged into Azure - skipping App Service verification"
        return
    fi
    
    if [[ -z "$APP_SERVICE" || -z "$RESOURCE_GROUP" ]]; then
        log_skip "App Service or Resource Group not configured"
        return
    fi
    
    log_info "Checking App Service: $APP_SERVICE"
    
    # Check App Service exists
    local app_exists
    app_exists=$(az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "name" -o tsv 2>/dev/null || echo "")
    
    if [[ -z "$app_exists" ]]; then
        log_failure "App Service $APP_SERVICE not found in resource group $RESOURCE_GROUP"
        return 1
    fi
    log_success "App Service exists"
    
    # Check App Service state
    local app_state
    app_state=$(az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "state" -o tsv 2>/dev/null || echo "unknown")
    
    if [[ "$app_state" == "Running" ]]; then
        log_success "App Service is Running"
    else
        log_failure "App Service state: $app_state (expected: Running)"
    fi
    
    # Check HTTPS Only
    local https_only
    https_only=$(az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "httpsOnly" -o tsv 2>/dev/null || echo "false")
    
    if [[ "$https_only" == "true" ]]; then
        log_success "HTTPS Only is enabled"
    else
        log_warning "HTTPS Only is not enabled"
    fi
    
    # Check Managed Identity
    local identity
    identity=$(az webapp identity show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "principalId" -o tsv 2>/dev/null || echo "")
    
    if [[ -n "$identity" ]]; then
        log_success "Managed Identity configured: ${identity:0:20}..."
    else
        log_warning "No Managed Identity configured"
    fi
    
    # Check Min TLS Version
    local min_tls
    min_tls=$(az webapp config show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "minTlsVersion" -o tsv 2>/dev/null || echo "")
    
    if [[ "$min_tls" == "1.2" ]]; then
        log_success "Minimum TLS version is 1.2"
    else
        log_warning "Minimum TLS version: $min_tls (recommended: 1.2)"
    fi
    
    verbose_log "Fetching App Service configuration details..."
    local sku
    sku=$(az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "sku.name" -o tsv 2>/dev/null || echo "unknown")
    log_info "App Service SKU: $sku"
    
    local linux_fx
    linux_fx=$(az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "siteConfig.linuxFxVersion" -o tsv 2>/dev/null || echo "unknown")
    log_info "Runtime Stack: $linux_fx"
}

verify_sql_server() {
    log_section "VERIFYING SQL SERVER"
    
    if ! check_command az; then
        log_skip "Azure CLI not available"
        return
    fi
    
    # Quick login check with timeout
    if ! timeout 3 az account show &>/dev/null; then
        log_skip "Not logged into Azure - skipping SQL Server verification"
        return
    fi
    
    if [[ -z "$SQL_SERVER" ]]; then
        log_skip "SQL Server not configured - may be using SQLite"
        return
    fi
    
    log_info "Checking SQL Server: $SQL_SERVER"
    
    # Check SQL Server exists
    local server_exists
    server_exists=$(az sql server show --name "$SQL_SERVER" --resource-group "$RESOURCE_GROUP" --query "name" -o tsv 2>/dev/null || echo "")
    
    if [[ -z "$server_exists" ]]; then
        log_failure "SQL Server $SQL_SERVER not found"
        return 1
    fi
    log_success "SQL Server exists"
    
    # Check SQL Server state
    local server_state
    server_state=$(az sql server show --name "$SQL_SERVER" --resource-group "$RESOURCE_GROUP" --query "state" -o tsv 2>/dev/null || echo "unknown")
    
    if [[ "$server_state" == "Ready" ]]; then
        log_success "SQL Server is Ready"
    else
        log_warning "SQL Server state: $server_state"
    fi
    
    # Check database exists
    log_info "Checking database: $SQL_DB"
    local db_exists
    db_exists=$(az sql db show --server "$SQL_SERVER" --name "$SQL_DB" --resource-group "$RESOURCE_GROUP" --query "name" -o tsv 2>/dev/null || echo "")
    
    if [[ -n "$db_exists" ]]; then
        log_success "Database $SQL_DB exists"
        
        # Check database status
        local db_status
        db_status=$(az sql db show --server "$SQL_SERVER" --name "$SQL_DB" --resource-group "$RESOURCE_GROUP" --query "status" -o tsv 2>/dev/null || echo "unknown")
        log_info "Database status: $db_status"
        
        # Check database edition
        local db_edition
        db_edition=$(az sql db show --server "$SQL_SERVER" --name "$SQL_DB" --resource-group "$RESOURCE_GROUP" --query "sku.tier" -o tsv 2>/dev/null || echo "unknown")
        log_info "Database edition: $db_edition"
    else
        log_failure "Database $SQL_DB not found"
    fi
    
    # Check firewall rules
    log_info "Checking SQL Server firewall rules..."
    local allow_azure
    allow_azure=$(az sql server firewall-rule list --server "$SQL_SERVER" --resource-group "$RESOURCE_GROUP" --query "[?startIpAddress=='0.0.0.0' && endIpAddress=='0.0.0.0'].name | [0]" -o tsv 2>/dev/null || echo "")
    
    if [[ -n "$allow_azure" ]]; then
        log_success "Azure services allowed through firewall"
    else
        log_warning "Azure services may not be allowed through firewall"
    fi
}

verify_redis_cache() {
    log_section "VERIFYING REDIS CACHE"
    
    if ! check_command az; then
        log_skip "Azure CLI not available"
        return
    fi
    
    # Quick login check with timeout
    if ! timeout 3 az account show &>/dev/null; then
        log_skip "Not logged into Azure - skipping Redis Cache verification"
        return
    fi
    
    if [[ -z "$REDIS_CACHE" ]]; then
        log_skip "Redis Cache not configured"
        return
    fi
    
    log_info "Checking Redis Cache: $REDIS_CACHE"
    
    # Check Redis exists
    local redis_exists
    redis_exists=$(az redis show --name "$REDIS_CACHE" --resource-group "$RESOURCE_GROUP" --query "name" -o tsv 2>/dev/null || echo "")
    
    if [[ -z "$redis_exists" ]]; then
        log_failure "Redis Cache $REDIS_CACHE not found"
        return 1
    fi
    log_success "Redis Cache exists"
    
    # Check Redis provisioning state
    local redis_state
    redis_state=$(az redis show --name "$REDIS_CACHE" --resource-group "$RESOURCE_GROUP" --query "provisioningState" -o tsv 2>/dev/null || echo "unknown")
    
    if [[ "$redis_state" == "Succeeded" ]]; then
        log_success "Redis Cache provisioning: Succeeded"
    else
        log_warning "Redis Cache provisioning state: $redis_state"
    fi
    
    # Check Redis SKU
    local redis_sku
    redis_sku=$(az redis show --name "$REDIS_CACHE" --resource-group "$RESOURCE_GROUP" --query "sku.name" -o tsv 2>/dev/null || echo "unknown")
    log_info "Redis SKU: $redis_sku"
    
    # Check SSL requirement
    local enable_ssl
    enable_ssl=$(az redis show --name "$REDIS_CACHE" --resource-group "$RESOURCE_GROUP" --query "enableNonSslPort" -o tsv 2>/dev/null || echo "")
    
    if [[ "$enable_ssl" == "false" ]]; then
        log_success "SSL/TLS is required for Redis"
    else
        log_warning "Non-SSL port is enabled on Redis"
    fi
}

verify_key_vault() {
    log_section "VERIFYING KEY VAULT"
    
    if ! check_command az; then
        log_skip "Azure CLI not available"
        return
    fi
    
    # Quick login check with timeout
    if ! timeout 3 az account show &>/dev/null; then
        log_skip "Not logged into Azure - skipping Key Vault verification"
        return
    fi
    
    if [[ -z "$KEY_VAULT" ]]; then
        log_skip "Key Vault not configured"
        return
    fi
    
    log_info "Checking Key Vault: $KEY_VAULT"
    
    # Check Key Vault exists
    local kv_exists
    kv_exists=$(az keyvault show --name "$KEY_VAULT" --resource-group "$RESOURCE_GROUP" --query "name" -o tsv 2>/dev/null || echo "")
    
    if [[ -z "$kv_exists" ]]; then
        log_warning "Key Vault $KEY_VAULT not found"
        return 1
    fi
    log_success "Key Vault exists"
    
    # Check Key Vault purge protection
    local purge_protection
    purge_protection=$(az keyvault show --name "$KEY_VAULT" --resource-group "$RESOURCE_GROUP" --query "properties.enablePurgeProtection" -o tsv 2>/dev/null || echo "")
    
    if [[ "$purge_protection" == "true" ]]; then
        log_success "Purge protection is enabled"
    else
        log_warning "Purge protection is not enabled"
    fi
    
    # Check soft-delete
    local soft_delete
    soft_delete=$(az keyvault show --name "$KEY_VAULT" --resource-group "$RESOURCE_GROUP" --query "properties.enableSoftDelete" -o tsv 2>/dev/null || echo "")
    
    if [[ "$soft_delete" == "true" ]]; then
        log_success "Soft-delete is enabled"
    else
        log_warning "Soft-delete is not enabled"
    fi
    
    # Count secrets (if access allows)
    local secret_count
    secret_count=$(az keyvault secret list --vault-name "$KEY_VAULT" --query "length(@)" -o tsv 2>/dev/null || echo "0")
    log_info "Secrets in Key Vault: $secret_count"
}

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

run_migrations() {
    log_section "DATABASE MIGRATIONS"
    
    if [[ "$SKIP_MIGRATIONS" == true ]]; then
        log_skip "Migrations skipped (--skip-migrations)"
        return
    fi
    
    if [[ ! -f "$ALEMBIC_INI" ]]; then
        log_warning "Alembic configuration not found at $ALEMBIC_INI"
        return 1
    fi
    
    log_info "Checking database migration status..."
    
    # Check if we're using SQLite or Azure SQL
    local db_url
    db_url=$(grep -E "^sqlalchemy\.url\s*=" "$ALEMBIC_INI" | cut -d'=' -f2- | xargs || echo "")
    
    if [[ -z "$db_url" ]]; then
        log_warning "Could not determine database URL from alembic.ini"
        return 1
    fi
    
    verbose_log "Database URL pattern: ${db_url%%://*}"
    
    # Run alembic current to check current revision
    log_info "Current database revision:"
    local current_rev
    current_rev=$(alembic current 2>/dev/null | grep "Current" || echo "unknown")
    log_info "  $current_rev"
    
    # Check if there are pending migrations
    log_info "Checking for pending migrations..."
    local pending
    pending=$(alembic history --verbose 2>/dev/null | grep -c "(head)" || echo "0")
    
    # Run migrations
    log_info "Running database migrations..."
    if alembic upgrade head 2>&1; then
        log_success "Database migrations completed successfully"
        
        # Verify new revision
        local new_rev
        new_rev=$(alembic current 2>/dev/null | grep "Current" || echo "unknown")
        log_info "  New revision: $new_rev"
    else
        log_failure "Database migrations failed"
        return 1
    fi
}

seed_test_data() {
    log_section "SEEDING TEST DATA"
    
    if [[ "$SKIP_SEEDING" == true ]]; then
        log_skip "Seeding skipped (--skip-seeding)"
        return
    fi
    
    if [[ ! -f "scripts/seed_data.py" ]]; then
        log_warning "Seed script not found at scripts/seed_data.py"
        return 1
    fi
    
    log_info "Running database seed script..."
    
    if python scripts/seed_data.py 2>&1; then
        log_success "Test data seeded successfully"
    else
        log_failure "Failed to seed test data"
        return 1
    fi
}

# =============================================================================
# APP SERVICE HEALTH CHECKS
# =============================================================================

check_app_running() {
    log_section "APP SERVICE HEALTH CHECKS"
    
    if [[ -z "$APP_URL" ]]; then
        log_failure "App URL not configured - cannot perform health checks"
        return 1
    fi
    
    log_info "Testing App Service at: $APP_URL"
    
    # Test basic connectivity
    log_info "Testing basic connectivity..."
    local result
    result=$(retry_request "$APP_URL" "200" "basic connectivity" "$MAX_RETRIES" true)
    local http_code=$(echo "$result" | tail -n2 | head -n1)
    local response_time=$(echo "$result" | tail -n1)
    
    if [[ "$http_code" == "200" || "$http_code" == "307" || "$http_code" == "302" ]]; then
        log_success "App Service is responding (HTTP $http_code, $(format_duration "$response_time"))"
    else
        log_failure "App Service not responding (HTTP $http_code)"
        return 1
    fi
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    local health_url="${APP_URL}/health"
    result=$(retry_request "$health_url" "200" "health endpoint")
    http_code=$(echo "$result" | tail -n2 | head -n1)
    local body=$(echo "$result" | sed '$d' | sed '$d')
    
    if [[ "$http_code" == "200" ]]; then
        local status
        status=$(parse_json "$body" ".status")
        local version
        version=$(parse_json "$body" ".version")
        
        if [[ "$status" == "healthy" ]]; then
            log_success "Health endpoint: healthy (version: $version)"
        else
            log_warning "Health status: $status"
        fi
    else
        log_failure "Health endpoint returned HTTP $http_code"
    fi
    
    # Test detailed health endpoint
    log_info "Testing detailed health endpoint..."
    local detailed_url="${APP_URL}/health/detailed"
    result=$(retry_request "$detailed_url" "200" "detailed health endpoint")
    http_code=$(echo "$result" | tail -n2 | head -n1)
    body=$(echo "$result" | sed '$d' | sed '$d')
    
    if [[ "$http_code" == "200" ]]; then
        local db_status
        db_status=$(parse_json "$body" ".components.database")
        local cache_status
        cache_status=$(parse_json "$body" ".components.cache")
        local scheduler_status
        scheduler_status=$(parse_json "$body" ".components.scheduler")
        
        log_info "  Database: $db_status"
        log_info "  Cache: $cache_status"
        log_info "  Scheduler: $scheduler_status"
        
        if [[ "$db_status" == "healthy" || "$db_status" == "sqlite" ]]; then
            log_success "Database connectivity confirmed"
        else
            log_warning "Database status: $db_status"
        fi
        
        log_success "Detailed health endpoint responding"
    else
        log_warning "Detailed health endpoint returned HTTP $http_code"
    fi
}

# =============================================================================
# API TESTS
# =============================================================================

run_api_tests() {
    log_section "API TESTS"
    
    if [[ "$SKIP_API_TESTS" == true ]]; then
        log_skip "API tests skipped (--skip-api-tests)"
        return
    fi
    
    if [[ ! -f "scripts/smoke_test.py" ]]; then
        log_warning "Smoke test script not found at scripts/smoke_test.py"
        return 1
    fi
    
    log_info "Running API smoke tests..."
    log_info "Target URL: $APP_URL"
    
    local smoke_test_args=(
        "--url" "$APP_URL"
        "--skip-azure"
    )
    
    [[ "$VERBOSE" == true ]] && smoke_test_args+=("--verbose")
    
    if python scripts/smoke_test.py "${smoke_test_args[@]}" 2>&1; then
        log_success "API smoke tests passed"
    else
        log_failure "API smoke tests failed"
        return 1
    fi
}

# =============================================================================
# REPORT GENERATION
# =============================================================================

generate_report() {
    if [[ "$GENERATE_REPORT" != true ]]; then
        return
    fi
    
    log_section "GENERATING DEPLOYMENT REPORT"
    
    local end_time
    end_time=$(date +%s)
    local total_duration=$((end_time - START_TIME))
    local total_tests=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
    
    # Create reports directory
    mkdir -p "$REPORT_DIR"
    
    # Determine report path
    local report_file
    if [[ -n "$REPORT_PATH" ]]; then
        report_file="$REPORT_PATH"
    else
        report_file="${REPORT_DIR}/deployment_report_${ENVIRONMENT}_${REPORT_TIMESTAMP}.json"
    fi
    
    # Calculate success rate
    local success_rate="100"
    if [[ $((total_tests - TESTS_SKIPPED)) -gt 0 ]]; then
        success_rate=$((TESTS_PASSED * 100 / (total_tests - TESTS_SKIPPED)))
    fi
    
    # Determine deployment status
    local deployment_status="unhealthy"
    if [[ $TESTS_FAILED -eq 0 ]]; then
        deployment_status="healthy"
    fi
    
    log_info "Generating report: $report_file"
    
    # Build JSON report
    cat > "$report_file" << EOF
{
    "metadata": {
        "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "environment": "$ENVIRONMENT",
        "url": "$APP_URL",
        "duration_seconds": $total_duration,
        "script_version": "1.0.0"
    },
    "azure_resources": {
        "resource_group": "$RESOURCE_GROUP",
        "app_service": "$APP_SERVICE",
        "sql_server": "$SQL_SERVER",
        "sql_database": "$SQL_DB",
        "redis_cache": "$REDIS_CACHE",
        "key_vault": "$KEY_VAULT"
    },
    "test_summary": {
        "total": $total_tests,
        "passed": $TESTS_PASSED,
        "failed": $TESTS_FAILED,
        "skipped": $TESTS_SKIPPED,
        "warnings": $WARNINGS,
        "success_rate": $success_rate
    },
    "deployment_status": "$deployment_status",
    "flags": {
        "skip_migrations": $SKIP_MIGRATIONS,
        "skip_seeding": $SKIP_SEEDING,
        "skip_api_tests": $SKIP_API_TESTS,
        "verbose": $VERBOSE
    }
}
EOF
    
    log_success "Report generated: $report_file"
    
    # Also generate a human-readable summary
    local summary_file="${report_file%.json}.txt"
    {
        echo "================================================================================"
        echo "AZURE GOVERNANCE PLATFORM - DEPLOYMENT VERIFICATION REPORT"
        echo "================================================================================"
        echo ""
        echo "Generated:    $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo "Environment:  $(echo "$ENVIRONMENT" | tr '[:lower:]' '[:upper:]')"
        echo "URL:          $APP_URL"
        echo "Duration:     ${total_duration}s"
        echo ""
        echo "================================================================================"
        echo "AZURE RESOURCES"
        echo "================================================================================"
        echo "Resource Group:  ${RESOURCE_GROUP:-"N/A"}"
        echo "App Service:     ${APP_SERVICE:-"N/A"}"
        echo "SQL Server:      ${SQL_SERVER:-"N/A (SQLite)"}"
        echo "SQL Database:    ${SQL_DB:-"N/A"}"
        echo "Redis Cache:     ${REDIS_CACHE:-"N/A"}"
        echo "Key Vault:       ${KEY_VAULT:-"N/A"}"
        echo ""
        echo "================================================================================"
        echo "TEST RESULTS"
        echo "================================================================================"
        echo "Total Tests:    $total_tests"
        echo "Passed:         $TESTS_PASSED"
        echo "Failed:         $TESTS_FAILED"
        echo "Skipped:        $TESTS_SKIPPED"
        echo "Warnings:       $WARNINGS"
        echo ""
        echo "Success Rate:   ${success_rate}%"
        echo ""
        echo "================================================================================"
        if [[ $TESTS_FAILED -eq 0 ]]; then
            echo "DEPLOYMENT STATUS: HEALTHY"
        else
            echo "DEPLOYMENT STATUS: UNHEALTHY"
        fi
        echo "================================================================================"
        echo ""
        if [[ $TESTS_FAILED -eq 0 ]]; then
            echo "All critical checks passed. Deployment is ready for use."
        else
            echo "Some checks failed. Review the output above for details."
        fi
        echo ""
        echo "================================================================================"
    } > "$summary_file"
    
    log_success "Summary report: $summary_file"
}

# =============================================================================
# SUMMARY
# =============================================================================

print_summary() {
    local end_time
    end_time=$(date +%s)
    local total_duration=$((end_time - START_TIME))
    local total_tests=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
    
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                     VERIFICATION COMPLETE                      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${BOLD}Environment:${NC}     ${CYAN}${ENVIRONMENT}${NC}"
    echo -e "${BOLD}URL:${NC}            ${CYAN}${APP_URL:-"N/A"}${NC}"
    echo -e "${BOLD}Duration:${NC}        ${CYAN}${total_duration}s${NC}"
    echo ""
    
    echo -e "  ${GREEN}✓ Tests Passed:   $TESTS_PASSED${NC}"
    echo -e "  ${RED}✗ Tests Failed:   $TESTS_FAILED${NC}"
    echo -e "  ${CYAN}⊘ Tests Skipped:  $TESTS_SKIPPED${NC}"
    echo -e "  ${YELLOW}! Warnings:       $WARNINGS${NC}"
    echo -e "  ─────────────────────────────────────────"
    echo -e "  ${BOLD}Total Tests:      $total_tests${NC}"
    echo ""
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "  ${GREEN}✅ DEPLOYMENT VERIFICATION PASSED${NC}"
        echo -e "  ${GREEN}   All critical checks passed successfully.${NC}"
        echo ""
        
        if [[ "$GENERATE_REPORT" == true ]]; then
            echo -e "  Report saved to: ${CYAN}${REPORT_DIR}${NC}"
        fi
        
        return 0
    else
        echo -e "  ${RED}❌ DEPLOYMENT VERIFICATION FAILED${NC}"
        echo -e "  ${RED}   $TESTS_FAILED critical check(s) failed.${NC}"
        echo ""
        echo -e "  ${YELLOW}Recommended actions:${NC}"
        
        if [[ -n "$APP_SERVICE" && -n "$RESOURCE_GROUP" ]]; then
            echo -e "  • View app logs: ${CYAN}az webapp log tail --name $APP_SERVICE --resource-group $RESOURCE_GROUP${NC}"
        fi
        
        if [[ -n "$APP_URL" ]]; then
            echo -e "  • Check health: ${CYAN}curl -s ${APP_URL}/health/detailed${NC}"
        fi
        
        echo -e "  • Review Azure Portal for resource health"
        echo ""
        
        return 1
    fi
}

print_next_steps() {
    [[ $TESTS_FAILED -eq 0 ]] || return
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo ""
    
    if [[ -n "$APP_URL" ]]; then
        echo -e "  1. Access the application:"
        echo -e "     ${CYAN}${APP_URL}${NC}"
        echo ""
    fi
    
    if [[ -n "$APP_SERVICE" && -n "$RESOURCE_GROUP" ]]; then
        echo -e "  2. Monitor application logs:"
        echo -e "     ${CYAN}az webapp log tail --name $APP_SERVICE --resource-group $RESOURCE_GROUP${NC}"
        echo ""
    fi
    
    echo -e "  3. Run preflight checks (requires auth):"
    echo -e "     ${CYAN}curl -X POST ${APP_URL}/api/v1/preflight/run${NC}"
    echo ""
    
    if [[ "$SKIP_API_TESTS" == true ]]; then
        echo -e "  4. Run smoke tests:"
        echo -e "     ${CYAN}python scripts/smoke_test.py --url ${APP_URL}${NC}"
        echo ""
    fi
    
    echo ""
}

# =============================================================================
# COMMAND LINE PARSING
# =============================================================================

show_help() {
    cat << 'EOF'
Azure Governance Platform - Deployment Verification & Testing Script

Usage: ./scripts/verify-and-test-deployment.sh [OPTIONS]

Options:
  --environment ENV      Environment name: dev, staging, prod (default: dev)
  --url URL              App Service URL to test (auto-detected if not set)
  --resource-group NAME  Azure Resource Group name (auto-detected if not set)
  --app-service NAME     Azure App Service name (auto-detected if not set)
  --sql-server NAME      Azure SQL Server name (auto-detected if not set)
  --skip-migrations      Skip database migrations
  --skip-seeding         Skip test data seeding
  --skip-api-tests       Skip API smoke tests
  --verbose, -v          Enable verbose output
  --generate-report      Generate JSON and text report files
  --report-path PATH     Custom path for report files
  --help                 Show this help message

Environment Variables:
  ENVIRONMENT            Environment name
  APP_URL                Application URL
  RESOURCE_GROUP         Azure Resource Group
  APP_SERVICE            Azure App Service name
  SQL_SERVER             Azure SQL Server name
  SQL_DB                 SQL Database name (default: governance)
  REDIS_CACHE            Azure Redis Cache name
  KEY_VAULT              Azure Key Vault name
  EXPECTED_TENANT_COUNT  Number of tenants expected (default: 5)
  TIMEOUT                HTTP request timeout in seconds (default: 30)
  MAX_RETRIES            Number of retries for failed requests (default: 3)
  REPORT_DIR             Directory for generated reports (default: ./reports)

Examples:
  # Test development deployment with verbose output
  ./scripts/verify-and-test-deployment.sh --environment dev --verbose

  # Test production deployment with specific URL
  ./scripts/verify-and-test-deployment.sh --environment prod --url https://app-governance-prod.azurewebsites.net

  # Run with all verification steps but skip migrations
  ./scripts/verify-and-test-deployment.sh --environment staging --skip-migrations --generate-report

  # Run quick check without migrations, seeding, or API tests
  ./scripts/verify-and-test-deployment.sh --environment dev --skip-migrations --skip-seeding --skip-api-tests

Exit Codes:
  0 - All checks passed (deployment healthy)
  1 - Critical checks failed (deployment unhealthy)
  2 - Configuration or runtime error

Dependencies:
  - Azure CLI (az) for Azure resource verification
  - curl for HTTP health checks
  - jq for JSON parsing
  - Python 3 with alembic for database migrations
  - bc for calculations
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --url)
                APP_URL="$2"
                shift 2
                ;;
            --resource-group)
                RESOURCE_GROUP="$2"
                shift 2
                ;;
            --app-service)
                APP_SERVICE="$2"
                shift 2
                ;;
            --sql-server)
                SQL_SERVER="$2"
                shift 2
                ;;
            --skip-migrations)
                SKIP_MIGRATIONS=true
                shift
                ;;
            --skip-seeding)
                SKIP_SEEDING=true
                shift
                ;;
            --skip-api-tests)
                SKIP_API_TESTS=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --generate-report)
                GENERATE_REPORT=true
                shift
                ;;
            --report-path)
                REPORT_PATH="$2"
                GENERATE_REPORT=true
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Run with --help for usage information"
                exit 2
                ;;
        esac
    done
    
    # Validate environment
    case "$ENVIRONMENT" in
        dev|development|staging|prod|production)
            # Valid environment
            ;;
        *)
            echo -e "${YELLOW}Warning: Unusual environment name '$ENVIRONMENT'${NC}"
            ;;
    esac
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    parse_args "$@"
    
    print_header
    print_configuration
    
    # Check required dependencies
    check_dependency "curl" "curl" true
    check_dependency "jq" "jq" false
    check_dependency "az" "Azure CLI" false
    check_dependency "python3" "Python 3" false
    check_dependency "bc" "bc calculator" false
    
    echo ""
    
    # Phase 1: Detect Azure Resources
    detect_azure_resources
    
    # Phase 2: Verify Azure Resources (continue on failure to collect all results)
    verify_app_service || true
    verify_sql_server || true
    verify_redis_cache || true
    verify_key_vault || true
    
    # Phase 3: Run Migrations
    run_migrations || true
    
    # Phase 4: Seed Test Data
    seed_test_data || true
    
    # Phase 5: Check App Service Health
    check_app_running || true
    
    # Phase 6: Run API Tests
    run_api_tests || true
    
    # Phase 7: Generate Report
    generate_report
    
    # Print Summary
    print_summary
    local exit_code=$?
    
    # Print Next Steps (only on success)
    print_next_steps
    
    exit $exit_code
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
