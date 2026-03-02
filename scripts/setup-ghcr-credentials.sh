#!/bin/bash
# Setup GHCR credentials for Azure App Service
# This script guides users through creating a GitHub PAT and configuring Azure

set -e

echo "🔐 GitHub Container Registry Setup for Azure"
echo "============================================"
echo ""
echo "Since the container is private, we need a GitHub PAT with 'read:packages' scope."
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v az &> /dev/null; then
  echo "❌ Error: Azure CLI (az) is not installed."
  echo "   Install: https://aka.ms/azure-cli"
  exit 1
fi

if ! az account show &> /dev/null; then
  echo "❌ Error: Not logged into Azure. Run: az login"
  exit 1
fi

echo "✓ Azure CLI is ready"

# Step 1: Get GitHub username
echo ""
echo "Step 1: Getting your GitHub username..."
GITHUB_USER=$(gh api /user -q .login 2>/dev/null || echo "")
if [ -z "$GITHUB_USER" ]; then
  read -p "Enter your GitHub username: " GITHUB_USER
else
  echo "✓ Found: $GITHUB_USER"
fi

# Step 2: Instructions for PAT
echo ""
echo "Step 2: Create GitHub Personal Access Token"
echo "--------------------------------------------"
echo "1. Open: https://github.com/settings/tokens/new"
echo "2. Token name: Azure-Governance-Dev-Container-Access"
echo "3. Expiration: 90 days (recommended)"
echo "4. Scopes:"
echo "   ☑ read:packages (required to pull containers)"
echo "   ☐ write:packages (optional, for pushing)"
echo "5. Click 'Generate token'"
echo ""
read -p "Paste your PAT here (input will be hidden): " -s GITHUB_PAT
echo ""
echo "✓ Token received"

# Step 3: Validate token
echo ""
echo "Step 3: Validating token..."
VALID=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $GITHUB_PAT" \
  https://api.github.com/user/packages?package_type=container)

if [ "$VALID" == "200" ] || [ "$VALID" == "403" ]; then
  echo "✓ Token appears valid (may need packages scope verification)"
else
  echo "⚠ Token validation returned: $VALID"
  echo "   Continuing anyway - Azure will verify the token"
fi

# Step 4: Configure Azure
echo ""
echo "Step 4: Configuring Azure App Service..."
echo "----------------------------------------"
echo "App: app-governance-dev-001"
echo "Resource Group: rg-governance-dev"
echo ""

az webapp config appsettings set \
  --name app-governance-dev-001 \
  --resource-group rg-governance-dev \
  --settings \
    DOCKER_REGISTRY_SERVER_USERNAME="$GITHUB_USER" \
    DOCKER_REGISTRY_SERVER_PASSWORD="$GITHUB_PAT" \
  --output table

echo ""
echo "✅ Azure configured with GHCR credentials!"

# Step 5: Restart app
echo ""
echo "Step 5: Restarting App Service to pull container..."
az webapp restart \
  --name app-governance-dev-001 \
  --resource-group rg-governance-dev

echo "✅ App Service restarted!"
echo ""
echo "Waiting 60 seconds for container startup..."
sleep 60

# Step 6: Verify
echo ""
echo "Step 6: Verifying deployment..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" \
  https://app-governance-dev-001.azurewebsites.net/health 2>/dev/null || echo "000")

if [ "$HEALTH" == "200" ]; then
  echo "✅ SUCCESS! Dev environment is ONLINE!"
  curl -s https://app-governance-dev-001.azurewebsites.net/health | jq . 2>/dev/null || \
    curl -s https://app-governance-dev-001.azurewebsites.net/health
else
  echo "⏳ Health check: HTTP $HEALTH"
  echo "Container may still be starting. Run './scripts/monitor-dev.sh' to watch."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Notes:"
echo "- The PAT has been stored in Azure App Service settings"
echo "- When the PAT expires, run this script again to update it"
echo "- Monitor with: ./scripts/monitor-dev.sh"
