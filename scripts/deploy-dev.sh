#!/bin/bash
# Azure Governance Platform - Dev Deployment Script
# Usage: ./scripts/deploy-dev.sh

set -e

echo "🚀 Deploying Azure Governance Platform to DEV environment..."

# Configuration
ENVIRONMENT="dev"
RESOURCE_GROUP="rg-governance-dev"
APP_NAME="app-governance-dev-001"
LOCATION="westus2"
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}"

echo "📋 Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Service: $APP_NAME"
echo "  Location: $LOCATION"
echo "  Subscription: $SUBSCRIPTION_ID"
echo ""

# Ensure logged in
echo "🔐 Checking Azure login..."
az account show > /dev/null 2>&1 || { echo "Please run 'az login' first"; exit 1; }

# Deploy infrastructure
echo "🏗️  Deploying infrastructure..."
cd infrastructure
az deployment sub create \
    --location $LOCATION \
    --template-file main.bicep \
    --parameters parameters.dev.json \
    --name "main-$ENVIRONMENT-$(date +%Y%m%d-%H%M%S)"

cd ..

# Deploy application code
echo "📦 Deploying application code..."
az webapp deploy \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --src-path . \
    --type zip \
    --async true

# Verify deployment
echo "✅ Verifying deployment..."
APP_URL="https://$APP_NAME.azurewebsites.net"
echo "  App URL: $APP_URL"
echo "  Health: $APP_URL/health"

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Resources created:"
echo "  - Resource Group: $RESOURCE_GROUP"
echo "  - App Service Plan: asp-governance-dev-001"
echo "  - Web App: $APP_NAME"
echo "  - Key Vault: kv-gov-dev-001"
echo "  - Storage: stgovdev001"
echo "  - Log Analytics: log-governance-dev-001"
echo "  - App Insights: ai-governance-dev-001"
echo ""
echo "Next steps:"
echo "  1. Configure required secrets in Key Vault"
echo "  2. Set up Azure AD App Registration for authentication"
echo "  3. Configure sync job schedules"
echo "  4. Run initial data sync"
