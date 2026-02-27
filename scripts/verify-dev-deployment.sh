#!/bin/bash
# =============================================================================
# Azure Governance Platform - Dev Deployment Verification Script
# =============================================================================
# Usage: ./scripts/verify-dev-deployment.sh
# Requires: curl, jq, azure-cli (optional, for Azure resource checks)
#
# This script verifies the dev deployment by:
# 1. Testing health endpoints
# 2. Checking API accessibility
# 3. Validating dashboard loads
# 4. Verifying Azure resources (if logged in)
# =============================================================================

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-https://app-governance-dev-001.azurewebsites.net}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-governance-dev}"
APP_SERVICE="${APP_SERVICE:-app-governance-dev-001}"
TIMEOUT=30
MAX_RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_section() {
    echo -e "\n${BLUE}--- $1 ---${NC}"
}

check_command() {
    command -v "$1" &> /dev/null || { log_warning "$1 is not installed. Some checks will be skipped."; return 1; }
    return 0
}

# =============================================================================
# Test Functions
# =============================================================================

test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    local method=${4:-GET}
    local require_json=${5:-false}

    print_section "Testing: $description"
    log_info "URL: $url"

    local http_code
    local response
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        response=$(curl -s -w "\n%{http_code}" \
            --max-time $TIMEOUT \
            -X "$method" \
            -H "Accept: application/json" \
            "$url" 2>/dev/null || echo -e "\n000")

        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')

        if [ "$http_code" == "$expected_status" ]; then
            break
        fi

        ((retry_count++)) || true
        if [ $retry_count -lt $MAX_RETRIES ]; then
            log_info "Retry $retry_count/$MAX_RETRIES..."
            sleep 5
        fi
    done

    if [ "$http_code" == "$expected_status" ]; then
        log_success "$description (HTTP $http_code)"

        if [ "$require_json" == true ]; then
            if echo "$body" | jq -e . &>/dev/null; then
                log_success "Response is valid JSON"
                echo "$body" | jq . 2>/dev/null || true
            else
                log_failure "Response is not valid JSON"
                echo "$body" | head -20 || true
            fi
        else
            if [ -n "$body" ]; then
                echo "$body" | head -20 || true
            fi
        fi
        return 0
    else
        log_failure "$description (Expected HTTP $expected_status, got $http_code)"
        if [ -n "$body" ]; then
            echo "Response: $body" | head -50 || true
        fi
        return 1
    fi
}

test_health_endpoint() {
    print_header "Health Endpoint Test"
    test_endpoint "$BASE_URL/health" "Basic Health Check" 200 true
}

test_detailed_health() {
    print_header "Detailed Health Check"
    test_endpoint "$BASE_URL/health/detailed" "Detailed Health Check" 200 true
}

test_api_status() {
    print_header "API Status Endpoint"
    test_endpoint "$BASE_URL/api/v1/status" "System Status API" 200 true
}

test_dashboard() {
    print_header "Dashboard Load Test"
    test_endpoint "$BASE_URL/" "Dashboard Root" 307 false
    
    # Follow redirect to /dashboard
    local response
    response=$(curl -s -L --max-time $TIMEOUT "$BASE_URL/" 2>/dev/null | head -100 || true)
    
    if [ -n "$response" ]; then
        if echo "$response" | grep -q "<!DOCTYPE\|<html\|<body"; then
            log_success "Dashboard returns HTML content"
        else
            log_warning "Dashboard response doesn't appear to be HTML"
        fi
    else
        log_failure "Dashboard returned empty response"
    fi
}

test_static_files() {
    print_header "Static Files Test"
    local static_url="$BASE_URL/static/css/dashboard.css"
    
    # Check if static files are accessible (may not exist, so we're flexible)
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$static_url" 2>/dev/null || echo "000")
    
    if [ "$http_code" == "200" ]; then
        log_success "Static CSS files accessible"
    elif [ "$http_code" == "404" ]; then
        log_info "Static CSS not found (may be normal for dev)"
    else
        log_warning "Static files returned HTTP $http_code"
    fi
}

# =============================================================================
# Azure Resource Verification (if az CLI is available)
# =============================================================================

test_azure_resources() {
    print_header "Azure Resource Verification"

    if ! check_command az; then
        log_warning "Azure CLI not available. Skipping Azure resource checks."
        return
    fi

    # Check if logged in
    if ! az account show &>/dev/null; then
        log_warning "Not logged into Azure. Skipping Azure resource checks."
        log_info "Run 'az login' to enable Azure resource verification"
        return
    fi

    print_section "Checking App Service Status"
    local app_status
    app_status=$(az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "state" -o tsv 2>/dev/null || echo "unknown")
    
    if [ "$app_status" == "Running" ]; then
        log_success "App Service is Running"
    elif [ "$app_status" == "unknown" ]; then
        log_warning "Could not retrieve App Service status"
    else
        log_failure "App Service status: $app_status"
    fi

    print_section "Checking App Service Configuration"
    local https_only
    https_only=$(az webapp show --name "$APP_SERVICE" --resource-group "$RESOURCE_GROUP" --query "httpsOnly" -o tsv 2>/dev/null || echo "unknown")
    
    if [ "$https_only" == "true" ]; then
        log_success "HTTPS Only is enabled"
    elif [ "$https_only" == "unknown" ]; then
        log_warning "Could not retrieve HTTPS configuration"
    else
        log_warning "HTTPS Only is not enabled (recommended for production)"
    fi

    print_section "Checking Application Insights"
    local ai_name
    ai_name=$(az monitor app-insights component list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
    
    if [ -n "$ai_name" ]; then
        log_success "Application Insights configured: $ai_name"
    else
        log_warning "Application Insights not found or not accessible"
    fi

    print_section "Checking Key Vault"
    local kv_name
    kv_name=$(az keyvault list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
    
    if [ -n "$kv_name" ]; then
        log_success "Key Vault configured: $kv_name"
    else
        log_warning "Key Vault not found or not accessible"
    fi
}

# =============================================================================
# Summary
# =============================================================================

print_summary() {
    print_header "Verification Summary"
    
    echo ""
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All critical tests passed!${NC}"
        echo -e "${GREEN}Dev deployment appears to be healthy.${NC}"
    else
        echo -e "${RED}❌ Some tests failed. Review the output above.${NC}"
    fi
    
    echo ""
    echo "Environment Details:"
    echo "  Base URL: $BASE_URL"
    echo "  Resource Group: $RESOURCE_GROUP"
    echo "  App Service: $APP_SERVICE"
    echo ""
    echo "Next Steps:"
    echo "  - Review any failed tests above"
    echo "  - Check Azure Portal for resource health"
    echo "  - Review Application Insights logs"
    echo "  - Run: az webapp log tail --name $APP_SERVICE --resource-group $RESOURCE_GROUP"
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    print_header "Azure Governance Platform - Dev Deployment Verification"
    
    log_info "Target Environment: Dev"
    log_info "Base URL: $BASE_URL"
    log_info "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    
    # Run all tests
    test_health_endpoint
    test_detailed_health
    test_api_status
    test_dashboard
    test_static_files
    test_azure_resources
    
    # Print summary
    print_summary
    
    # Exit with appropriate code
    if [ $TESTS_FAILED -gt 0 ]; then
        exit 1
    fi
    exit 0
}

# Allow sourcing for testing, but run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
