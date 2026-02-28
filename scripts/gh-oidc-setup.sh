#!/bin/bash
# =============================================================================
# Azure Governance Platform - OIDC Setup via GitHub CLI
# =============================================================================
# Automates OIDC federation setup using gh CLI and Azure CLI
# Creates federated credentials in Azure AD and configures GitHub secrets
#
# Usage:
#   ./scripts/gh-oidc-setup.sh [options]
#
# Options:
#   -e, --environment    Environment (dev|staging|prod) [default: dev]
#   -g, --resource-group Resource group name [default: rg-governance-<env>]
#   -r, --repo           GitHub repo (owner/repo) [auto-detected]
#   -s, --subscription   Azure subscription ID [auto-detected]
#   --create-rg          Create resource group if it doesn't exist
#   --skip-gh-secrets    Skip setting GitHub secrets (Azure only)
#   --skip-azure         Skip Azure setup (GitHub secrets only)
#   -h, --help           Show help
#
# Examples:
#   ./scripts/gh-oidc-setup.sh
#   ./scripts/gh-oidc-setup.sh -e prod -g rg-governance-prod
#   ./scripts/gh-oidc-setup.sh --create-rg -e staging
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
RESOURCE_GROUP=""
GITHUB_REPO=""
SUBSCRIPTION_ID=""
CREATE_RG=false
SKIP_GH_SECRETS=false
SKIP_AZURE=false

# Help function
show_help() {
    cat << 'EOF'
Azure Governance Platform - OIDC Setup

Usage: ./scripts/gh-oidc-setup.sh [options]

Options:
  -e, --environment    Environment (dev|staging|prod) [default: dev]
  -g, --resource-group Resource group name [default: rg-governance-<env>]
  -r, --repo           GitHub repo (owner/repo) [auto-detected]
  -s, --subscription   Azure subscription ID [auto-detected]
  --create-rg          Create resource group if it doesn't exist
  --skip-gh-secrets    Skip setting GitHub secrets
  --skip-azure         Skip Azure setup (GitHub secrets only)
  -h, --help           Show this help

Examples:
  ./scripts/gh-oidc-setup.sh                    # Full setup for dev
  ./scripts/gh-oidc-setup.sh -e prod            # Setup for production
  ./scripts/gh-oidc-setup.sh --create-rg -e staging

Prerequisites:
  - gh CLI: https://cli.github.com
  - Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli
  - jq: https://stedolan.github.io/jq/
  - Owner or User Access Admin on Azure subscription
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
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
        -s|--subscription)
            SUBSCRIPTION_ID="$2"
            shift 2
            ;;
        --create-rg)
            CREATE_RG=true
            shift
            ;;
        --skip-gh-secrets)
            SKIP_GH_SECRETS=true
            shift
            ;;
        --skip-azure)
            SKIP_AZURE=true
            shift
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

# Normalize environment
ENVIRONMENT=$(echo "$ENVIRONMENT" | tr '[:upper:]' '[:lower:]')
case "$ENVIRONMENT" in
    development) ENVIRONMENT="dev" ;;
    production) ENVIRONMENT="prod" ;;
esac

# Set default resource group
if [[ -z "$RESOURCE_GROUP" ]]; then
    RESOURCE_GROUP="rg-governance-${ENVIRONMENT}"
fi

# Header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔐 OIDC Federation Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Environment: ${CYAN}${ENVIRONMENT}${NC}"
echo -e "Resource Group: ${CYAN}${RESOURCE_GROUP}${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ gh CLI not found. Install: https://cli.github.com/${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} gh CLI found"

# Check gh auth
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not logged in to GitHub. Run: gh auth login${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} GitHub authenticated"

# Get GitHub repo
if [[ -z "$GITHUB_REPO" ]]; then
    GITHUB_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
fi

if [[ -z "$GITHUB_REPO" ]]; then
    echo -e "${RED}❌ Could not detect GitHub repository${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Repository: ${CYAN}${GITHUB_REPO}${NC}"

# Check Azure CLI (if not skipping Azure)
if [[ "$SKIP_AZURE" == false ]]; then
    if ! command -v az &> /dev/null; then
        echo -e "${RED}❌ Azure CLI not found. Install: https://docs.microsoft.com/cli/azure/install-azure-cli${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Azure CLI found"
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq not found. Install: https://stedolan.github.io/jq/download/${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} jq found"
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        echo -e "${YELLOW}⚠️  Not logged in to Azure. Running az login...${NC}"
        az login
    fi
    echo -e "  ${GREEN}✓${NC} Azure authenticated"
    
    # Get subscription info
    if [[ -z "$SUBSCRIPTION_ID" ]]; then
        SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    fi
    SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
    TENANT_ID=$(az account show --query tenantId -o tsv)
    
    echo -e "  ${GREEN}✓${NC} Subscription: ${CYAN}${SUBSCRIPTION_NAME}${NC}"
fi

# ============================================================================
# Azure Setup
# ============================================================================
if [[ "$SKIP_AZURE" == false ]]; then
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}Step 1: Azure AD App Registration${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Create resource group if requested
    if [[ "$CREATE_RG" == true ]]; then
        echo "Ensuring resource group exists..."
        if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
            echo "  Creating resource group: $RESOURCE_GROUP"
            az group create --name "$RESOURCE_GROUP" --location westus2 --output none
            echo -e "  ${GREEN}✓${NC} Resource group created"
        else
            echo -e "  ${GREEN}✓${NC} Resource group exists"
        fi
    fi
    
    # App registration name
    APP_NAME="azure-governance-platform-oidc-${ENVIRONMENT}"
    
    echo "Creating App Registration: $APP_NAME"
    
    # Check if app already exists
    EXISTING_APP=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || echo "")
    
    if [[ -n "$EXISTING_APP" ]]; then
        echo -e "  ${YELLOW}⚠${NC} App registration already exists: ${EXISTING_APP}"
        APP_ID="$EXISTING_APP"
        APP_OBJECT_ID=$(az ad app show --id "$APP_ID" --query "id" -o tsv)
    else
        # Create app registration
        APP_CREATE_OUTPUT=$(az ad app create \
            --display-name "$APP_NAME" \
            --sign-in-audience AzureADMyOrg \
            --query "{appId: appId, id: id}" \
            -o json)
        
        APP_ID=$(echo "$APP_CREATE_OUTPUT" | jq -r '.appId')
        APP_OBJECT_ID=$(echo "$APP_CREATE_OUTPUT" | jq -r '.id')
        
        echo -e "  ${GREEN}✓${NC} App Registration created: ${CYAN}${APP_ID}${NC}"
    fi
    
    # Create service principal
    echo ""
    echo -e "Creating Service Principal..."
    EXISTING_SP=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv 2>/dev/null || echo "")
    
    if [[ -n "$EXISTING_SP" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Service principal already exists"
        SP_ID="$EXISTING_SP"
    else
        SP_ID=$(az ad sp create --id "$APP_ID" --query "id" -o tsv)
        echo -e "  ${GREEN}✓${NC} Service Principal created: ${CYAN}${SP_ID}${NC}"
    fi
    
    # Configure federated credentials
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}Step 2: Federated Credentials${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Configuring OIDC federation for: ${CYAN}${GITHUB_REPO}${NC}"
    echo ""
    
    # Define federated credentials
    declare -A FEDERATED_CREDS
    FEDERATED_CREDS["main-branch"]="repo:${GITHUB_REPO}:ref:refs/heads/main"
    FEDERATED_CREDS["dev-branch"]="repo:${GITHUB_REPO}:ref:refs/heads/dev"
    FEDERATED_CREDS["pr-validation"]="repo:${GITHUB_REPO}:pull_request"
    FEDERATED_CREDS["tag-deploy"]="repo:${GITHUB_REPO}:ref:refs/tags/v*"
    FEDERATED_CREDS["environment-prod"]="repo:${GITHUB_REPO}:environment:production"
    FEDERATED_CREDS["environment-staging"]="repo:${GITHUB_REPO}:environment:staging"
    FEDERATED_CREDS["environment-dev"]="repo:${GITHUB_REPO}:environment:development"
    
    for CRED_NAME in "${!FEDERATED_CREDS[@]}"; do
        SUBJECT="${FEDERATED_CREDS[$CRED_NAME]}"
        
        # Check if credential already exists
        EXISTING_CRED=$(az ad app federated-credential list \
            --id "$APP_ID" \
            --query "[?name=='$CRED_NAME'].name" \
            -o tsv 2>/dev/null || echo "")
        
        if [[ -n "$EXISTING_CRED" ]]; then
            echo -e "  ${YELLOW}⚠${NC} Credential exists: ${CRED_NAME}"
            continue
        fi
        
        echo "  Creating: ${CRED_NAME}"
        
        # Build credential JSON
        if [[ "$SUBJECT" == *"pull_request"* ]]; then
            CRED_JSON=$(cat <<EOF
{
    "name": "${CRED_NAME}",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "${SUBJECT}",
    "description": "GitHub Actions PR authentication for ${GITHUB_REPO}",
    "audiences": ["api://AzureADTokenExchange"]
}
EOF
)
        else
            CRED_JSON=$(cat <<EOF
{
    "name": "${CRED_NAME}",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "${SUBJECT}",
    "description": "GitHub Actions ${CRED_NAME} authentication for ${GITHUB_REPO}",
    "audiences": ["api://AzureADTokenExchange"]
}
EOF
)
        fi
        
        # Create credential
        if az ad app federated-credential create \
            --id "$APP_ID" \
            --parameters "$CRED_JSON" \
            --output none 2>/dev/null; then
            echo -e "    ${GREEN}✓${NC} Created"
        else
            echo -e "    ${YELLOW}⚠${NC} Failed (may already exist)"
        fi
    done
    
    # Assign Azure RBAC roles
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}Step 3: Azure RBAC Roles${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Define roles based on environment
    case "$ENVIRONMENT" in
        dev)
            ROLES=("Website Contributor" "Web Plan Contributor")
            ;;
        staging)
            ROLES=("Website Contributor" "Web Plan Contributor" "Monitoring Contributor")
            ;;
        prod)
            ROLES=("Website Contributor" "Web Plan Contributor" "Monitoring Contributor" "Key Vault Secrets User")
            ;;
    esac
    
    RG_SCOPE="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"
    
    for ROLE in "${ROLES[@]}"; do
        echo "  Assigning: ${ROLE}"
        
        # Check if role assignment exists
        EXISTING_ROLE=$(az role assignment list \
            --assignee "$APP_ID" \
            --role "$ROLE" \
            --scope "$RG_SCOPE" \
            --query "[0].id" \
            -o tsv 2>/dev/null || echo "")
        
        if [[ -n "$EXISTING_ROLE" ]]; then
            echo -e "    ${YELLOW}⚠${NC} Already assigned"
            continue
        fi
        
        # Assign role
        if az role assignment create \
            --role "$ROLE" \
            --assignee "$APP_ID" \
            --scope "$RG_SCOPE" \
            --output none 2>/dev/null; then
            echo -e "    ${GREEN}✓${NC} Assigned"
        else
            echo -e "    ${RED}✗${NC} Failed (trying with SP ID)"
            az role assignment create \
                --role "$ROLE" \
                --assignee-object-id "$SP_ID" \
                --assignee-principal-type ServicePrincipal \
                --scope "$RG_SCOPE" \
                --output none 2>/dev/null || true
        fi
    done
    
    # Wait for propagation
    echo ""
    echo -e "${YELLOW}Waiting for role propagation (30 seconds)...${NC}"
    sleep 30
fi

# ============================================================================
# GitHub Secrets
# ============================================================================
if [[ "$SKIP_GH_SECRETS" == false ]]; then
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}Step 4: GitHub Secrets${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    if [[ "$SKIP_AZURE" == true ]]; then
        # Manual input mode
        echo -e "${YELLOW}Enter Azure configuration:${NC}"
        read -p "Azure Client ID (App Registration): " APP_ID
        read -p "Azure Tenant ID: " TENANT_ID
        read -p "Azure Subscription ID: " SUBSCRIPTION_ID
    fi
    
    # Set repository secrets
    echo "Setting repository secrets..."
    
    echo "  - AZURE_CLIENT_ID"
    echo "$APP_ID" | gh secret set AZURE_CLIENT_ID --repo "$GITHUB_REPO"
    
    echo "  - AZURE_TENANT_ID"
    echo "$TENANT_ID" | gh secret set AZURE_TENANT_ID --repo "$GITHUB_REPO"
    
    echo "  - AZURE_SUBSCRIPTION_ID"
    echo "$SUBSCRIPTION_ID" | gh secret set AZURE_SUBSCRIPTION_ID --repo "$GITHUB_REPO"
    
    echo "  - AZURE_RESOURCE_GROUP"
    echo "$RESOURCE_GROUP" | gh secret set AZURE_RESOURCE_GROUP --repo "$GITHUB_REPO"
    
    # Set app service name (derived from environment)
    APP_SERVICE_NAME="app-governance-${ENVIRONMENT}-001"
    echo "  - AZURE_APP_SERVICE_NAME"
    echo "$APP_SERVICE_NAME" | gh secret set AZURE_APP_SERVICE_NAME --repo "$GITHUB_REPO"
    
    echo -e "  ${GREEN}✓${NC} Repository secrets set"
    
    # Set environment-specific secrets
    echo ""
    echo "Setting environment secrets..."
    
    # Map environment names
    case "$ENVIRONMENT" in
        dev) GH_ENV="development" ;;
        staging) GH_ENV="staging" ;;
        prod) GH_ENV="production" ;;
    esac
    
    echo "  - ${GH_ENV} environment"
    echo "$APP_ID" | gh secret set AZURE_CLIENT_ID \
        --env "$GH_ENV" --repo "$GITHUB_REPO" 2>/dev/null || \
        echo -e "    ${YELLOW}⚠${NC} Failed (environment may not exist)"
    
    echo -e "  ${GREEN}✓${NC} Environment secrets set"
fi

# ============================================================================
# Save Configuration
# ============================================================================
if [[ "$SKIP_AZURE" == false ]]; then
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}Saving Configuration${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    CONFIG_FILE="${PROJECT_ROOT}/infrastructure/.oidc-config-${ENVIRONMENT}.json"
    
    cat > "$CONFIG_FILE" << EOF
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
        "objectId": "${APP_OBJECT_ID}"
    },
    "servicePrincipal": {
        "id": "${SP_ID}"
    },
    "githubSecrets": {
        "AZURE_CLIENT_ID": "${APP_ID}",
        "AZURE_TENANT_ID": "${TENANT_ID}",
        "AZURE_SUBSCRIPTION_ID": "${SUBSCRIPTION_ID}",
        "AZURE_RESOURCE_GROUP": "${RESOURCE_GROUP}",
        "AZURE_APP_SERVICE_NAME": "${APP_SERVICE_NAME}"
    },
    "setupTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    echo -e "  ${GREEN}✓${NC} Configuration saved: ${CYAN}${CONFIG_FILE}${NC}"
fi

# ============================================================================
# Completion
# ============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 OIDC Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [[ "$SKIP_AZURE" == false ]]; then
    echo -e "${CYAN}Azure Configuration:${NC}"
    echo -e "  App Registration: ${APP_NAME}"
    echo -e "  Client ID: ${APP_ID}"
    echo -e "  Tenant ID: ${TENANT_ID}"
    echo -e "  Subscription: ${SUBSCRIPTION_NAME}"
    echo ""
    echo -e "${CYAN}Azure Portal Links:${NC}"
    echo -e "  App Registration: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Overview/appId/${APP_ID}"
    echo -e "  Resource Group: https://portal.azure.com/#@/resource/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"
    echo ""
fi

echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Verify GitHub secrets:"
echo -e "     ${CYAN}gh secret list${NC}"
echo ""
echo "  2. Test the deployment:"
echo -e "     ${CYAN}./scripts/gh-deploy-dev.sh${NC}"
echo ""
echo "  3. Monitor workflow runs:"
echo -e "     ${CYAN}gh run list${NC}"
echo ""
echo "  4. Configure environment protection:"
echo -e "     ${CYAN}https://github.com/${GITHUB_REPO}/settings/environments${NC}"
echo ""
