#!/bin/bash
# =============================================================================
# Azure Governance Platform - Azure Setup Script
# =============================================================================
# This script helps set up the initial Azure configuration including:
# - Service Principal creation
# - Resource providers registration
# - Initial credentials generation
#
# Usage:
#   ./scripts/setup-azure.sh
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Azure Governance Platform - Azure Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI not found. Please install it:${NC}"
    echo "https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Check login
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Logging in to Azure...${NC}"
    az login
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo -e "Subscription: ${GREEN}${SUBSCRIPTION_NAME}${NC}"
echo -e "Subscription ID: ${GREEN}${SUBSCRIPTION_ID}${NC}"
echo -e "Tenant ID: ${GREEN}${TENANT_ID}${NC}"
echo ""

# Register resource providers
echo -e "${YELLOW}Registering resource providers...${NC}"
az provider register --namespace Microsoft.Web --wait
az provider register --namespace Microsoft.Insights --wait
az provider register --namespace Microsoft.KeyVault --wait
az provider register --namespace Microsoft.Storage --wait
az provider register --namespace Microsoft.Sql --wait
az provider register --namespace Microsoft.OperationalInsights --wait
echo -e "${GREEN}✓ Resource providers registered${NC}"
echo ""

# Create service principal
echo -e "${YELLOW}Creating Service Principal...${NC}"
SP_NAME="azure-governance-platform-sp"

# Check if SP already exists
EXISTING_SP=$(az ad sp list --display-name "$SP_NAME" --query "[0].appId" -o tsv 2>/dev/null || echo "")

if [[ -n "$EXISTING_SP" ]]; then
    echo -e "${YELLOW}Service Principal already exists: ${EXISTING_SP}${NC}"
    read -p "Delete and recreate? (yes/no): " confirm
    if [[ "$confirm" == "yes" ]]; then
        az ad sp delete --id "$EXISTING_SP" 2>/dev/null || true
        az ad app delete --id "$EXISTING_SP" 2>/dev/null || true
    else
        echo -e "${YELLOW}Using existing Service Principal${NC}"
        CLIENT_ID="$EXISTING_SP"
        # Can't get existing secret, user needs to create new one
        echo -e "${YELLOW}Note: You'll need to create a new client secret in Azure Portal${NC}"
    fi
fi

if [[ -z "${CLIENT_ID:-}" ]]; then
    echo -e "${YELLOW}Creating new Service Principal...${NC}"
    SP_OUTPUT=$(az ad sp create-for-rbac \
        --name "$SP_NAME" \
        --role "Reader" \
        --scopes "/subscriptions/${SUBSCRIPTION_ID}" \
        --years 2 \
        --sdk-auth)
    
    CLIENT_ID=$(echo "$SP_OUTPUT" | grep "clientId" | cut -d'"' -f4)
    CLIENT_SECRET=$(echo "$SP_OUTPUT" | grep "clientSecret" | cut -d'"' -f4)
    
    echo -e "${GREEN}✓ Service Principal created${NC}"
fi

# Generate JWT secret
echo -e "${YELLOW}Generating JWT secret...${NC}"
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || openssl rand -base64 48)
echo -e "${GREEN}✓ JWT secret generated${NC}"
echo ""

# Create .env file
echo -e "${YELLOW}Creating .env file...${NC}"
cat > .env << EOF
# =============================================================================
# Azure Governance Platform - Environment Configuration
# Generated on $(date)
# =============================================================================

# Azure Credentials (REQUIRED)
AZURE_TENANT_ID=${TENANT_ID}
AZURE_CLIENT_ID=${CLIENT_ID}
AZURE_CLIENT_SECRET=${CLIENT_SECRET:-YOUR_CLIENT_SECRET_HERE}

# Azure AD OAuth (optional - for user authentication)
AZURE_AD_TENANT_ID=${TENANT_ID}
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=

# Security
JWT_SECRET_KEY=${JWT_SECRET}
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Environment
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO

# Database (SQLite for development)
DATABASE_URL=sqlite:///./data/governance.db

# Sync Configuration
COST_SYNC_INTERVAL_HOURS=24
COMPLIANCE_SYNC_INTERVAL_HOURS=4
RESOURCE_SYNC_INTERVAL_HOURS=1
IDENTITY_SYNC_INTERVAL_HOURS=24
EOF

echo -e "${GREEN}✓ .env file created${NC}"
echo ""

# Display summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Azure Configuration:${NC}"
echo -e "  Tenant ID: ${TENANT_ID}"
echo -e "  Client ID: ${CLIENT_ID}"
if [[ -n "${CLIENT_SECRET:-}" ]]; then
    echo -e "  Client Secret: ${CLIENT_SECRET:0:10}... (saved in .env)"
else
    echo -e "  ${YELLOW}Client Secret: Create in Azure Portal > App Registrations > ${SP_NAME}${NC}"
fi
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Review the .env file and update any settings"
echo "2. Run: source .env (to load environment variables)"
echo "3. Run: ./infrastructure/deploy.sh development"
echo "4. Or start locally: uv run uvicorn app.main:app --reload"
echo ""
echo -e "${BLUE}Azure Portal:${NC} https://portal.azure.com"
echo ""
