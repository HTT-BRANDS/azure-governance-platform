#!/bin/bash
# =============================================================================
# Azure Governance Platform - OIDC Federation Setup Script
# =============================================================================
# This script configures Azure AD OIDC federation with GitHub Actions.
# Run this ONCE to establish trust between Azure AD and GitHub.
#
# What this does:
#   1. Creates an Azure AD App Registration for GitHub Actions
#   2. Creates a Service Principal
#   3. Configures federated credentials for GitHub OIDC
#   4. Assigns appropriate Azure RBAC roles
#   5. Outputs GitHub secrets to configure
#
# NO LONG-LIVED SECRETS ARE CREATED - Everything uses OIDC tokens!
#
# Usage:
#   ./setup-oidc.sh [options]
#
# Options:
#   -e, --environment    Environment (dev|staging|prod) [default: dev]
#   -s, --subscription   Azure subscription ID [auto-detected]
#   -g, --resource-group Resource group name [required]
#   -r, --repo           GitHub repo (owner/repo) [auto-detected from git]
#   -h, --help           Show help
#
# Examples:
#   ./setup-oidc.sh -e dev -g rg-governance-dev
#   ./setup-oidc.sh -e prod -g rg-governance-prod -r myorg/azure-governance
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="dev"
SUBSCRIPTION_ID=""
RESOURCE_GROUP=""
GITHUB_REPO=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -r|--repo)
            GITHUB_REPO="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Help function
show_help() {
    cat << 'EOF'
Azure Governance Platform - OIDC Federation Setup

Usage: ./setup-oidc.sh [options]

Options:
  -e, --environment    Environment (dev|staging|prod) [default: dev]
  -s, --subscription   Azure subscription ID [auto-detected]
  -g, --resource-group Resource group name [required]
  -r, --repo           GitHub repo (owner/repo) [auto-detected from git]
  -h, --help           Show this help

Examples:
  ./setup-oidc.sh -e dev -g rg-governance-dev
  ./setup-oidc.sh -e prod -g rg-governance-prod -r myorg/azure-governance
EOF
}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|development|staging|prod|production)$ ]]; then
    echo -e "${RED}Error: Environment must be one of: dev, staging, prod${NC}"
    exit 1
fi

# Normalize environment names
case "$ENVIRONMENT" in
    development) ENVIRONMENT="dev" ;;
    production) ENVIRONMENT="prod" ;;
esac

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Azure OIDC Federation Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Environment: ${GREEN}${ENVIRONMENT}${NC}"

# Check prerequisites
echo ""
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    echo "Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Azure CLI found"

# Check jq
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed${NC}"
    echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} jq found"

# Check Azure login
echo ""
echo -e "${YELLOW}Checking Azure login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Please login to Azure:${NC}"
    az login
fi

# Get subscription info
if [[ -z "$SUBSCRIPTION_ID" ]]; then
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
fi
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo -e "  Subscription: ${CYAN}${SUBSCRIPTION_NAME}${NC}"
echo -e "  Subscription ID: ${CYAN}${SUBSCRIPTION_ID}${NC}"
echo -e "  Tenant ID: ${CYAN}${TENANT_ID}${NC}"

# Get GitHub repo from git remote if not provided
if [[ -z "$GITHUB_REPO" ]]; then
    if git remote get-url origin &> /dev/null; then
        REMOTE_URL=$(git remote get-url origin)
        # Parse owner/repo from various URL formats
        if [[ "$REMOTE_URL" =~ github.com[:/]([^/]+)/([^/.]+) ]]; then
            GITHUB_REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
        fi
    fi
fi

if [[ -z "$GITHUB_REPO" ]]; then
    echo -e "${RED}Error: Could not detect GitHub repo. Please specify with -r flag.${NC}"
    exit 1
fi

echo -e "  GitHub Repo: ${CYAN}${GITHUB_REPO}${NC}"

# Get resource group
if [[ -z "$RESOURCE_GROUP" ]]; then
    echo ""
    echo -e "${YELLOW}Fetching resource groups...${NC}"
    az group list --query "[?contains(name, 'governance')].name" -o tsv | head -5
    echo ""
    read -p "Enter resource group name: " RESOURCE_GROUP
fi

if [[ -z "$RESOURCE_GROUP" ]]; then
    echo -e "${RED}Error: Resource group is required${NC}"
    exit 1
fi

# Verify resource group exists
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo -e "${RED}Error: Resource group '$RESOURCE_GROUP' not found${NC}"
    exit 1
fi

echo -e "  Resource Group: ${CYAN}${RESOURCE_GROUP}${NC}"

# Generate app name
APP_NAME="azure-governance-platform-oidc-${ENVIRONMENT}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Step 1: Creating Azure AD App Registration${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if app already exists
EXISTING_APP=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || echo "")

if [[ -n "$EXISTING_APP" ]]; then
    echo -e "${YELLOW}App registration already exists: ${EXISTING_APP}${NC}"
    APP_ID="$EXISTING_APP"
else
    echo "Creating app registration: $APP_NAME"
    APP_CREATE_OUTPUT=$(az ad app create \
        --display-name "$APP_NAME" \
        --sign-in-audience AzureADMyOrg \
        --query "{appId: appId, id: id}" \
        -o json)
    
    APP_ID=$(echo "$APP_CREATE_OUTPUT" | jq -r '.appId')
    APP_OBJECT_ID=$(echo "$APP_CREATE_OUTPUT" | jq -r '.id')
    
    echo -e "  ${GREEN}✓${NC} App Registration created: ${CYAN}${APP_ID}${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Step 2: Creating Service Principal${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if service principal already exists
EXISTING_SP=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv 2>/dev/null || echo "")

if [[ -n "$EXISTING_SP" ]]; then
    echo -e "${YELLOW}Service principal already exists${NC}"
    SP_ID="$EXISTING_SP"
else
    echo "Creating service principal..."
    SP_CREATE_OUTPUT=$(az ad sp create --id "$APP_ID" --query "id" -o tsv)
    SP_ID="$SP_CREATE_OUTPUT"
    echo -e "  ${GREEN}✓${NC} Service Principal created: ${CYAN}${SP_ID}${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Step 3: Configuring Federated Credentials${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "This establishes trust between Azure AD and GitHub Actions.${NC}"
echo -e "GitHub's OIDC provider will be trusted for:${NC}"
echo "  - Main branch deployments (production)"
echo "  - Dev branch deployments (development)"
echo "  - Pull request validation"
echo ""

# Define federated credentials
FEDERATED_CREDENTIALS=(
    "main-branch:repo:${GITHUB_REPO}:ref:refs/heads/main"
    "dev-branch:repo:${GITHUB_REPO}:ref:refs/heads/dev"
    "pr-branch:repo:${GITHUB_REPO}:pull_request"
    "tag-deploy:repo:${GITHUB_REPO}:ref:refs/tags/v*"
    "environment-prod:repo:${GITHUB_REPO}:environment:production"
    "environment-staging:repo:${GITHUB_REPO}:environment:staging"
)

for cred in "${FEDERATED_CREDENTIALS[@]}"; do
    IFS=':' read -r CRED_NAME CRED_TYPE CRED_REPO CRED_CLAIM CRED_VALUE <<< "$cred"
    
    # Check if credential already exists
    EXISTING_CRED=$(az ad app federated-credential list \
        --id "$APP_ID" \
        --query "[?name=='$CRED_NAME'].name" \
        -o tsv 2>/dev/null || echo "")
    
    if [[ -n "$EXISTING_CRED" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Federated credential exists: ${CRED_NAME}"
        continue
    fi
    
    echo "  Creating: ${CRED_NAME}"
    
    # Create credential parameters JSON
    if [[ "$CRED_CLAIM" == "pull_request" ]]; then
        CREDENTIAL_PARAMS=$(cat <<EOF
{
    "name": "${CRED_NAME}",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "${CRED_TYPE}:${CRED_REPO}:${CRED_CLAIM}",
    "description": "GitHub Actions PR authentication for ${GITHUB_REPO}",
    "audiences": ["api://AzureADTokenExchange"]
}
EOF
)
    else
        CREDENTIAL_PARAMS=$(cat <<EOF
{
    "name": "${CRED_NAME}",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "${CRED_TYPE}:${CRED_REPO}:${CRED_CLAIM}:${CRED_VALUE}",
    "description": "GitHub Actions ${CRED_NAME} authentication for ${GITHUB_REPO}",
    "audiences": ["api://AzureADTokenExchange"]
}
EOF
)
    fi
    
    # Create the federated credential
    az ad app federated-credential create \
        --id "$APP_ID" \
        --parameters "$CREDENTIAL_PARAMS" \
        --output none 2>/dev/null || {
            echo -e "    ${YELLOW}⚠${NC} Failed to create ${CRED_NAME} (may already exist)"
            continue
        }
    
    echo -e "    ${GREEN}✓${NC} Created: ${CRED_NAME}"
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Step 4: Assigning Azure RBAC Roles${NC}"
echo -e "${BLUE}========================================${NC}"

# Define roles based on environment
case "$ENVIRONMENT" in
    dev|development)
        ROLES=("Website Contributor" "Web Plan Contributor")
        ;;
    staging)
        ROLES=("Website Contributor" "Web Plan Contributor" "Monitoring Contributor")
        ;;
    prod|production)
        ROLES=("Website Contributor" "Web Plan Contributor" "Monitoring Contributor" "Key Vault Secrets User")
        ;;
esac

for ROLE in "${ROLES[@]}"; do
    echo "  Assigning role: ${ROLE}"
    
    # Check if role assignment already exists
    EXISTING_ROLE=$(az role assignment list \
        --assignee "$APP_ID" \
        --role "$ROLE" \
        --scope "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
        --query "[0].id" \
        -o tsv 2>/dev/null || echo "")
    
    if [[ -n "$EXISTING_ROLE" ]]; then
        echo -e "    ${YELLOW}⚠${NC} Role already assigned"
        continue
    fi
    
    az role assignment create \
        --role "$ROLE" \
        --assignee "$APP_ID" \
        --scope "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
        --output none 2>/dev/null || {
            echo -e "    ${RED}✗${NC} Failed to assign role (retrying with SP ID)"
            az role assignment create \
                --role "$ROLE" \
                --assignee-object-id "$SP_ID" \
                --assignee-principal-type ServicePrincipal \
                --scope "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
                --output none
        }
    
    echo -e "    ${GREEN}✓${NC} Assigned: ${ROLE}"
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Step 5: Waiting for role propagation...${NC}"
echo -e "${BLUE}========================================${NC}"
echo "This may take 30-60 seconds..."
sleep 30

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ OIDC Federation Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}GitHub Secrets to Configure:${NC}"
echo ""
echo -e "  ${YELLOW}AZURE_CLIENT_ID${NC}=${APP_ID}"
echo -e "  ${YELLOW}AZURE_TENANT_ID${NC}=${TENANT_ID}"
echo -e "  ${YELLOW}AZURE_SUBSCRIPTION_ID${NC}=${SUBSCRIPTION_ID}"
echo -e "  ${YELLOW}AZURE_RESOURCE_GROUP${NC}=${RESOURCE_GROUP}"
echo -e "  ${YELLOW}AZURE_APP_SERVICE_NAME${NC}=app-governance-${ENVIRONMENT}-<suffix>"
echo ""
echo -e "${CYAN}Add these secrets to your GitHub repository:${NC}"
echo "  Settings → Secrets and variables → Actions → New repository secret"
echo ""
echo -e "${CYAN}Configure GitHub Environments:${NC}"
echo "  Settings → Environments → New environment"
echo "  Create: development, staging, production"
echo ""
echo -e "${CYAN}Verification:${NC}"
echo "  Test with: gh workflow run deploy-oidc.yml --ref dev"
echo ""
echo -e "${CYAN}Azure Portal Links:${NC}"
echo "  App Registration: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Overview/appId/${APP_ID}"
echo "  Resource Group: https://portal.azure.com/#@/resource/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"
echo ""

# Save configuration
cat > "${SCRIPT_DIR}/.oidc-config-${ENVIRONMENT}.json" << EOF
{
    "environment": "${ENVIRONMENT}",
    "subscriptionId": "${SUBSCRIPTION_ID}",
    "subscriptionName": "${SUBSCRIPTION_NAME}",
    "tenantId": "${TENANT_ID}",
    "resourceGroup": "${RESOURCE_GROUP}",
    "githubRepo": "${GITHUB_REPO}",
    "appRegistration": {
        "name": "${APP_NAME}",
        "clientId": "${APP_ID}",
        "objectId": "${APP_OBJECT_ID:-}"
    },
    "servicePrincipal": {
        "id": "${SP_ID}"
    },
    "githubSecrets": {
        "AZURE_CLIENT_ID": "${APP_ID}",
        "AZURE_TENANT_ID": "${TENANT_ID}",
        "AZURE_SUBSCRIPTION_ID": "${SUBSCRIPTION_ID}",
        "AZURE_RESOURCE_GROUP": "${RESOURCE_GROUP}",
        "AZURE_APP_SERVICE_NAME": "app-governance-${ENVIRONMENT}"
    },
    "setupTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "${GREEN}Configuration saved to: ${SCRIPT_DIR}/.oidc-config-${ENVIRONMENT}.json${NC}"
echo ""
