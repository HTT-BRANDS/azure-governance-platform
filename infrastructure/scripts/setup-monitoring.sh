#!/bin/bash
# Azure Governance Platform - Phase 2 Monitoring Setup
# This script sets up Application Insights and Log Analytics for production monitoring

set -e

# Configuration
RESOURCE_GROUP="rg-governance-production"
LOCATION="westus2"
APP_INSIGHTS_NAME="governance-appinsights"
LOG_ANALYTICS_NAME="governance-logs"
KEY_VAULT_NAME="kv-gov-prod"
APP_SERVICE_NAME="app-governance-prod"

echo "============================================"
echo "Azure Governance Platform - Monitoring Setup"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if Application Insights already exists
print_status "Checking if Application Insights exists..."
if az monitor app-insights component show \
    --app "$APP_INSIGHTS_NAME" \
    --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo "Application Insights '$APP_INSIGHTS_NAME' already exists."
else
    print_status "Creating Application Insights..."
    az monitor app-insights component create \
        --app "$APP_INSIGHTS_NAME" \
        --location "$LOCATION" \
        --resource-group "$RESOURCE_GROUP" \
        --application-type web \
        --output table
    print_success "Application Insights created"
fi

# Get connection string
APP_INSIGHTS_CONN=$(az monitor app-insights component show \
    --app "$APP_INSIGHTS_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query connectionString -o tsv)

APP_INSIGHTS_KEY=$(az monitor app-insights component show \
    --app "$APP_INSIGHTS_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query instrumentationKey -o tsv)

# Store connection string in Key Vault
print_status "Storing connection string in Key Vault..."
az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name app-insights-connection \
    --value "$APP_INSIGHTS_CONN" \
    --output none
print_success "Connection string stored in Key Vault"

# Configure App Service
print_status "Configuring App Service for Application Insights..."
az webapp config appsettings set \
    --name "$APP_SERVICE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        APPINSIGHTS_INSTRUMENTATIONKEY="$APP_INSIGHTS_KEY" \
        APPLICATIONINSIGHTS_CONNECTION_STRING="$APP_INSIGHTS_CONN" \
        ApplicationInsightsAgent_EXTENSION_VERSION="~2" \
    --output none
print_success "App Service configured"

# Enable diagnostic logging
print_status "Enabling diagnostic logging on App Service..."
az webapp log config \
    --name "$APP_SERVICE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --application-logging filesystem \
    --detailed-error-messages true \
    --failed-request-tracing true \
    --level verbose \
    --output none
print_success "Diagnostic logging enabled"

# Create Log Analytics workspace
print_status "Checking if Log Analytics workspace exists..."
if az monitor log-analytics workspace show \
    --name "$LOG_ANALYTICS_NAME" \
    --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo "Log Analytics workspace '$LOG_ANALYTICS_NAME' already exists."
else
    print_status "Creating Log Analytics workspace..."
    az monitor log-analytics workspace create \
        --name "$LOG_ANALYTICS_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output table
    print_success "Log Analytics workspace created"
fi

# Link App Insights to Log Analytics
print_status "Linking Application Insights to Log Analytics workspace..."
WORKSPACE_ID=$(az monitor log-analytics workspace show \
    --name "$LOG_ANALYTICS_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query id -o tsv)

az monitor app-insights component update \
    --app "$APP_INSIGHTS_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --workspace "$WORKSPACE_ID" \
    --output none
print_success "Application Insights linked to Log Analytics"

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Monitoring URLs:"
echo "  Application Insights:"
echo "    https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Insights/components/$APP_INSIGHTS_NAME/overview"
echo ""
echo "  Log Analytics Workspace:"
echo "    https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.OperationalInsights/workspaces/$LOG_ANALYTICS_NAME/logs"
echo ""
echo "Instrumentation Key: $APP_INSIGHTS_KEY"
echo ""
echo "To verify the setup, visit your application and check the monitoring portals."
