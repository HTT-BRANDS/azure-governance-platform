#!/bin/bash
# =============================================================================
# Full Redeploy Dev Environment
# =============================================================================
# Completely redeploys the dev infrastructure with correct container configuration
#
# This script:
#   1. Deletes existing App Service (keeps other resources)
#   2. Updates Bicep template for container deployment
#   3. Redeploys infrastructure with correct settings
#   4. Verifies the deployment
#
# Usage: ./scripts/redeploy-dev.sh
# Prerequisites: Azure CLI, jq, Contributor access to subscription
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="app-governance-dev-001"
RESOURCE_GROUP="rg-governance-dev"
PLAN_NAME="plan-governance-dev-001"
LOCATION="westus2"
CONTAINER_IMAGE="ghcr.io/tygranlund/azure-governance-platform:dev"
REGISTRY_URL="https://ghcr.io"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not found. Please install: https://aka.ms/installazurecli"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Please install: brew install jq (or apt-get install jq)"
        exit 1
    fi
    
    # Check if logged in
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure. Run: az login"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Confirm destructive operation
confirm_destructive() {
    echo ""
    echo -e "${RED}⚠️  WARNING: DESTRUCTIVE OPERATION${NC}"
    echo ""
    echo "This script will:"
    echo "  1. DELETE the existing App Service: $APP_NAME"
    echo "  2. RECREATE it with correct container configuration"
    echo "  3. Other resources (Key Vault, Storage, etc.) will be preserved"
    echo ""
    echo "This will cause DOWNTIME for the dev environment."
    echo ""
    read -p "Are you sure you want to continue? [y/N]: " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Aborted by user"
        exit 0
    fi
}

# Delete existing App Service
delete_app_service() {
    log_info "Checking if App Service exists..."
    
    if az webapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_warn "App Service exists. Deleting..."
        az webapp delete \
            --name "$APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --keep-empty-plan \
            --yes \
            --output none
        log_success "App Service deleted"
        
        # Wait for deletion to propagate
        log_info "Waiting for deletion to propagate..."
        sleep 30
    else
        log_info "App Service does not exist, continuing..."
    fi
}

# Update Bicep for container deployment
update_bicep_template() {
    log_info "Checking Bicep template for container configuration..."
    
    local bicep_file="infrastructure/modules/app-service.bicep"
    
    # Check if already configured for containers
    if grep -q "kind: 'app,linux,container'" "$bicep_file"; then
        log_success "Bicep template already configured for containers"
        return 0
    fi
    
    log_warn "Bicep template needs update for container deployment"
    log_info "Please update infrastructure/modules/app-service.bicep to support containers"
    echo ""
    echo "The template should:"
    echo "  1. Change kind from 'app,linux' to 'app,linux,container'"
    echo "  2. Change linuxFxVersion from 'PYTHON|3.11' to 'DOCKER|\${containerImage}'"
    echo "  3. Remove appCommandLine (handled by Dockerfile)"
    echo ""
    
    read -p "Have you updated the Bicep template? [y/N]: " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Please update the Bicep template and re-run this script"
        exit 0
    fi
}

# Deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure..."
    
    local deployment_name="redeploy-dev-$(date +%Y%m%d-%H%M%S)"
    
    log_info "Running deployment: $deployment_name"
    
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$deployment_name" \
        --template-file infrastructure/main.bicep \
        --parameters infrastructure/parameters.dev.json \
        --parameters containerImage="$CONTAINER_IMAGE" \
        --output json \
        > /tmp/deployment-output.json || {
            log_error "Deployment failed. Check: az deployment group show --name $deployment_name --resource-group $RESOURCE_GROUP"
            exit 1
        }
    
    log_success "Infrastructure deployment completed"
}

# Configure container settings directly
configure_container_settings() {
    log_info "Configuring container settings..."
    
    # Set container configuration
    az webapp config container set \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --docker-custom-image-name "$CONTAINER_IMAGE" \
        --docker-registry-server-url "$REGISTRY_URL" \
        --output none
    
    log_success "Container settings configured"
    
    # Enable managed identity
    log_info "Configuring managed identity..."
    az webapp identity assign \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --output none 2>/dev/null || log_warn "Identity may already be assigned"
    
    log_success "Managed identity configured"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Get App Service details
    local app_state
    app_state=$(az webapp show \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "state" \
        --output tsv)
    
    log_info "App Service state: $app_state"
    
    # Check container configuration
    local linux_fx
    linux_fx=$(az webapp config show \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "linuxFxVersion" \
        --output tsv)
    
    log_info "linuxFxVersion: $linux_fx"
    
    if [[ "$linux_fx" == DOCKER* ]]; then
        log_success "✅ Container runtime configured correctly"
    else
        log_error "❌ Container runtime NOT configured. Value: $linux_fx"
        return 1
    fi
    
    # Wait for startup and test
    log_info "Waiting for app to start (2 minutes)..."
    sleep 60
    
    local app_url
    app_url=$(az webapp show \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostName" \
        --output tsv)
    
    log_info "Testing health endpoint..."
    
    for i in {1..6}; do
        if curl -sf "https://${app_url}/health" &>/dev/null; then
            log_success "✅ Health check PASSED!"
            return 0
        fi
        log_warn "Health check attempt $i/6 failed, retrying in 20s..."
        sleep 20
    done
    
    log_warn "⚠️  Health check did not pass. App may still be starting."
    return 1
}

# Print final summary
print_summary() {
    local app_url
    app_url=$(az webapp show \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "defaultHostName" \
        --output tsv)
    
    echo ""
    echo "=========================================="
    echo "    REDEPLOYMENT COMPLETE"
    echo "=========================================="
    echo ""
    echo "Resource Group:     $RESOURCE_GROUP"
    echo "App Service:        $APP_NAME"
    echo "Container Image:    $CONTAINER_IMAGE"
    echo ""
    echo "URLs:"
    echo "  Application: https://${app_url}"
    echo "  Health:      https://${app_url}/health"
    echo "  API Status:  https://${app_url}/api/v1/status"
    echo ""
    echo "Useful commands:"
    echo "  View logs:   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "  SSH access:  az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "  Config:      az webapp config show --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo ""
}

# Main execution
main() {
    echo "=========================================="
    echo "    REDEPLOY DEV ENVIRONMENT"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    confirm_destructive
    delete_app_service
    update_bicep_template
    deploy_infrastructure
    configure_container_settings
    verify_deployment
    print_summary
}

# Run main
main "$@"
