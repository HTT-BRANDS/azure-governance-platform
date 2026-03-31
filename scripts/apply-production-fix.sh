#!/bin/bash
# =============================================================================
# 🔧 Azure Governance Platform - Production 503 Fix (Interactive)
# =============================================================================
# This script interactively fixes the HTTP 503 error by configuring
# GitHub Container Registry (GHCR) authentication for the production
# Azure App Service.
#
# PREREQUISITE: You must create a GitHub PAT with 'read:packages' scope first!
#
# USAGE:
#   ./scripts/apply-production-fix.sh
#
# The script will prompt for:
#   - Your GitHub username
#   - Your GitHub Personal Access Token (PAT)
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="app-governance-prod"
RESOURCE_GROUP="rg-governance-production"
HEALTH_URL="https://${APP_NAME}.azurewebsites.net/health"
MAX_RETRIES=5
RETRY_DELAY=20

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     🔧 Azure Governance Platform - Production 503 Fix          ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# =============================================================================
# Validation Functions
# =============================================================================

check_azure_login() {
    print_step "Checking Azure CLI authentication..."
    
    if ! az account show &>/dev/null; then
        print_error "Not logged into Azure CLI"
        echo ""
        echo "Please login first:"
        echo "  az login"
        exit 1
    fi
    
    local subscription_name=$(az account show --query name -o tsv)
    print_success "Logged into Azure subscription: $subscription_name"
    echo ""
}

validate_github_username() {
    local username="$1"
    
    if [[ -z "$username" ]]; then
        print_error "GitHub username cannot be empty"
        return 1
    fi
    
    if [[ ! "$username" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$ ]]; then
        print_error "Invalid GitHub username format"
        return 1
    fi
    
    return 0
}

validate_github_pat() {
    local pat="$1"
    
    if [[ -z "$pat" ]]; then
        print_error "GitHub PAT cannot be empty"
        return 1
    fi
    
    # GitHub PATs start with ghp_, ghu_, gho_, etc.
    if [[ ! "$pat" =~ ^gh[pousr]_[a-zA-Z0-9]{36,}$ ]]; then
        print_warning "PAT format looks unusual. GitHub PATs typically start with 'ghp_'"
        read -p "Continue anyway? (y/N): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    
    return 0
}

# =============================================================================
# Main Functions
# =============================================================================

show_prerequisites() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  ⚠️  PREREQUISITE: Create GitHub PAT Before Continuing         ${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "You MUST create a GitHub Personal Access Token first:"
    echo ""
    echo "  1. Visit: ${CYAN}https://github.com/settings/tokens/new${NC}"
    echo "  2. Select: ${CYAN}Classic token${NC} (not fine-grained)"
    echo "  3. Name: ${CYAN}Azure App Service GHCR Pull${NC}"
    echo "  4. Expiration: ${CYAN}90 days${NC} (recommended)"
    echo "  5. Scopes: ${GREEN}✅ ONLY check 'read:packages'${NC}"
    echo "     ${RED}❌ Do NOT select other scopes${NC}"
    echo "  6. Generate and ${YELLOW}COPY the token immediately${NC}"
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    read -p "Have you created and copied your GitHub PAT? (y/N): " ready
    if [[ ! "$ready" =~ ^[Yy]$ ]]; then
        echo ""
        print_error "Please create your PAT first, then re-run this script."
        echo ""
        echo "Quick link: https://github.com/settings/tokens/new"
        exit 1
    fi
    echo ""
}

get_github_credentials() {
    print_step "Collecting GitHub credentials..."
    echo ""
    
    # Get GitHub username
    while true; do
        read -p "Enter your GitHub username: " github_username
        if validate_github_username "$github_username"; then
            break
        fi
    done
    
    # Get GitHub PAT (hidden input)
    while true; do
        read -s -p "Enter your GitHub PAT (input hidden): " github_pat
        echo "" # New line after hidden input
        if validate_github_pat "$github_pat"; then
            break
        fi
    done
    
    echo ""
    print_success "Credentials collected"
    echo ""
}

confirm_deployment() {
    print_step "Deployment Summary"
    echo ""
    echo "  App Service:    ${CYAN}$APP_NAME${NC}"
    echo "  Resource Group: ${CYAN}$RESOURCE_GROUP${NC}"
    echo "  GitHub User:    ${CYAN}$github_username${NC}"
    echo "  Registry URL:   ${CYAN}https://ghcr.io${NC}"
    echo ""
    
    read -p "Apply this fix? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled by user"
        exit 0
    fi
    echo ""
}

apply_fix() {
    print_step "Step 1/3: Applying container registry credentials..."
    echo ""
    
    if az webapp config container set \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --docker-registry-server-url "https://ghcr.io" \
        --docker-registry-server-username "$github_username" \
        --docker-registry-server-password "$github_pat" \
        --output none; then
        print_success "Registry credentials updated successfully"
    else
        print_error "Failed to update registry credentials"
        echo ""
        echo "Troubleshooting:"
        echo "  - Verify you're logged into Azure: az login"
        echo "  - Check you have permissions on resource group: $RESOURCE_GROUP"
        echo "  - Verify the app exists: az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP"
        exit 1
    fi
    
    echo ""
    print_step "Step 2/3: Restarting App Service to pull container..."
    echo ""
    
    if az webapp restart \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --output none; then
        print_success "App Service restarted"
    else
        print_error "Failed to restart App Service"
        exit 1
    fi
    
    echo ""
}

verify_health() {
    print_step "Step 3/3: Verifying deployment health..."
    echo ""
    print_info "Waiting for container startup (this may take 60-120 seconds)..."
    echo ""
    
    local retries=0
    local http_status
    
    # Initial wait for container to start
    sleep 30
    
    while [ $retries -lt $MAX_RETRIES ]; do
        retries=$((retries + 1))
        
        http_status=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
        
        if [ "$http_status" = "200" ]; then
            echo ""
            print_success "Health check PASSED (HTTP 200)"
            echo ""
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}  🎉 SUCCESS! Production deployment is now healthy!              ${NC}"
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo "Verification URL: ${CYAN}$HEALTH_URL${NC}"
            echo ""
            echo "Response:"
            curl -s "$HEALTH_URL" | python3 -m json.tool 2>/dev/null || curl -s "$HEALTH_URL"
            echo ""
            return 0
        elif [ "$http_status" = "503" ]; then
            echo -e "   Attempt $retries/$MAX_RETRIES: ${YELLOW}HTTP 503 (container still starting...)${NC}"
        elif [ "$http_status" = "000" ]; then
            echo -e "   Attempt $retries/$MAX_RETRIES: ${YELLOW}No response (container not ready yet...)${NC}"
        else
            echo -e "   Attempt $retries/$MAX_RETRIES: ${YELLOW}HTTP $http_status${NC}"
        fi
        
        if [ $retries -lt $MAX_RETRIES ]; then
            echo "   Waiting ${RETRY_DELAY}s before retry..."
            sleep $RETRY_DELAY
        fi
    done
    
    echo ""
    print_error "Health check did not return 200 after $MAX_RETRIES attempts"
    echo ""
    echo "Current status: HTTP $http_status"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check if GitHub PAT has 'read:packages' scope"
    echo "  2. Verify PAT can access 'htt-brands/azure-governance-platform' package"
    echo "  3. Check App Service logs:"
    echo "     ${CYAN}az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP${NC}"
    echo ""
    echo "Current App Service state:"
    az webapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" \
        --query "{state:state,linuxFxVersion:linuxFxVersion,lastModifiedTimeUtc:lastModifiedTimeUtc}"
    
    return 1
}

show_alternative() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  💡 ALTERNATIVE: Make GHCR Image Public (Simpler Long-term)     ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "If managing PATs is problematic, you can make the image public:"
    echo ""
    echo "  1. Visit: ${CYAN}https://github.com/HTT-BRANDS/azure-governance-platform/pkgs/container/azure-governance-platform${NC}"
    echo "  2. Click: ${CYAN}Package settings${NC}"
    echo "  3. Change visibility to: ${CYAN}Public${NC}"
    echo ""
    echo "Pros: No authentication needed, no PAT rotation"
    echo "Cons: Anyone can pull the image (may be acceptable)"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    print_header
    
    # Check prerequisites
    check_azure_login
    show_prerequisites
    
    # Get credentials
    local github_username
    local github_pat
    get_github_credentials
    
    # Make credentials available to other functions
    export github_username
    export github_pat
    
    # Confirm and apply
    confirm_deployment
    apply_fix
    
    # Verify
    if verify_health; then
        echo ""
        echo "📋 Post-Fix Checklist:"
        echo "  ☐ Verify main site loads in browser"
        echo "  ☐ Note PAT expiration date (90 days from now)"
        echo "  ☐ Set calendar reminder for PAT rotation"
        echo ""
        show_alternative
        exit 0
    else
        exit 1
    fi
}

# Handle script interruption
trap 'echo ""; print_error "Script interrupted"; exit 130' INT TERM

# Run main function
main "$@"
