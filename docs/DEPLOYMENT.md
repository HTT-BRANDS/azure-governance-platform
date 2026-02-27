# Azure Governance Platform - Deployment Guide

> **Version:** 1.0  
> **Last Updated:** February 2025  
> **Estimated Setup Time:** 2-4 hours

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Variables Reference](#2-environment-variables-reference)
3. [Deployment Options](#3-deployment-options)
4. [Local Development Deployment](#4-local-development-deployment)
5. [Docker Deployment](#5-docker-deployment)
6. [Azure App Service Deployment](#6-azure-app-service-deployment-recommended)
7. [Database Initialization](#7-database-initialization)
8. [Azure Lighthouse Setup (Optional)](#8-azure-lighthouse-setup-optional)
9. [Post-Deployment Verification](#9-post-deployment-verification)
10. [Troubleshooting](#10-troubleshooting)
11. [Security Hardening](#11-security-hardening)
12. [Backup and Recovery](#12-backup-and-recovery)

---

## 1. Prerequisites

### 1.1 Azure Prerequisites

Before deploying, ensure you have:

| Requirement | Details | How to Verify |
|-------------|---------|---------------|
| **Azure Subscription** | Active subscription for deployment costs | Azure Portal → Subscriptions |
| **Resource Group** | Or permission to create one | Azure Portal → Resource groups |
| **App Registration** | With appropriate API permissions | Azure Portal → App registrations |
| **RBAC Roles** | Contributor or Owner on subscription | Azure Portal → Access control (IAM) |
| **Tenant Access** | Global Admin or Application Admin for each managed tenant | Azure Portal → Azure AD → Roles |

### 1.2 Local Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Application runtime |
| uv | Latest | Python package manager |
| Git | Latest | Source control |
| Azure CLI | 2.50+ | Azure deployment |
| Docker | 24.0+ | Container deployment (optional) |

### 1.3 Required Azure Permissions

Your Azure account needs:

```
📁 Subscription Level
   ├── Microsoft.Resources/subscriptions/resourceGroups/write
   ├── Microsoft.Web/serverFarms/write
   ├── Microsoft.Web/sites/write
   └── Microsoft.Insights/components/write

📁 Azure AD (for App Registration)
   ├── Application.ReadWrite.All
   └── Directory.Read.All
```

### 1.4 Cost Estimates

| Deployment Type | Monthly Cost | Notes |
|-----------------|--------------|-------|
| **Local/Dev** | Free | Run on your machine |
| **Azure App Service (B1)** | ~$13 | Recommended for production |
| **Azure App Service (S1)** | ~$35 | Better performance |
| **Azure Container Apps** | ~$30-50 | Serverless containers |
| **Azure Key Vault** | ~$1-2 | Secret storage (optional) |
| **Application Insights** | ~$5-10 | Monitoring (optional) |

---

## 2. Environment Variables Reference

### 2.1 Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_TENANT_ID` | Primary Azure AD tenant GUID | `12345678-1234-1234-1234-123456789012` |
| `AZURE_CLIENT_ID` | App Registration client ID | `abcdef12-3456-7890-abcd-ef1234567890` |
| `AZURE_CLIENT_SECRET` | App Registration secret | `your-secret-value` |

### 2.2 Application Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG` | Enable debug mode | `false` | No |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `HOST` | Server bind address | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `DATABASE_URL` | SQLite connection string | `sqlite:///./data/governance.db` | No |

### 2.3 Sync Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `COST_SYNC_INTERVAL_HOURS` | Cost sync frequency | `24` |
| `COMPLIANCE_SYNC_INTERVAL_HOURS` | Compliance sync frequency | `4` |
| `RESOURCE_SYNC_INTERVAL_HOURS` | Resource sync frequency | `1` |
| `IDENTITY_SYNC_INTERVAL_HOURS` | Identity sync frequency | `24` |

### 2.4 Alerting

| Variable | Description | Default |
|----------|-------------|---------|
| `TEAMS_WEBHOOK_URL` | Microsoft Teams webhook | - |
| `COST_ANOMALY_THRESHOLD_PERCENT` | Cost spike threshold | `20.0` |
| `COMPLIANCE_ALERT_THRESHOLD_PERCENT` | Compliance drop threshold | `5.0` |

### 2.5 Riverside Compliance (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `RIVERSIDE_COMPLIANCE_ENABLED` | Enable Riverside features | `false` |
| `RIVERSIDE_DEADLINE_DATE` | Compliance deadline | `2026-07-08` |
| `RIVERSIDE_MFA_TARGET` | Target MFA percentage | `100` |
| `RIVERSIDE_MATURITY_TARGET` | Target maturity score | `3.0` |
| `RIVERSIDE_SYNC_INTERVAL_HOURS` | Riverside sync frequency | `4` |

### 2.6 Security Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `KEY_VAULT_URL` | Azure Key Vault URL | - |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `SECRET_KEY` | Flask/FastAPI secret | Auto-generated |

### 2.7 Complete .env Example

```bash
# =============================================================================
# REQUIRED: Azure Authentication
# =============================================================================
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=abcdef12-3456-7890-abcd-ef1234567890
AZURE_CLIENT_SECRET=your-secret-value-here

# =============================================================================
# Application Settings
# =============================================================================
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# =============================================================================
# Database
# =============================================================================
DATABASE_URL=sqlite:///./data/governance.db

# =============================================================================
# Sync Intervals (hours)
# =============================================================================
COST_SYNC_INTERVAL_HOURS=24
COMPLIANCE_SYNC_INTERVAL_HOURS=4
RESOURCE_SYNC_INTERVAL_HOURS=1
IDENTITY_SYNC_INTERVAL_HOURS=24

# =============================================================================
# Alerting
# =============================================================================
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
COST_ANOMALY_THRESHOLD_PERCENT=20.0
COMPLIANCE_ALERT_THRESHOLD_PERCENT=5.0

# =============================================================================
# Riverside Compliance (Optional)
# =============================================================================
RIVERSIDE_COMPLIANCE_ENABLED=true
RIVERSIDE_DEADLINE_DATE=2026-07-08
RIVERSIDE_MFA_TARGET=100
RIVERSIDE_MATURITY_TARGET=3.0

# =============================================================================
# Security (Production)
# =============================================================================
# KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
# CORS_ORIGINS=https://your-domain.com
```

---

## 3. Deployment Options

### 3.1 Comparison Matrix

| Option | Cost | Complexity | Scalability | Best For |
|--------|------|------------|-------------|----------|
| **Local** | Free | Low | None | Development, testing |
| **Docker** | Varies | Medium | Medium | Existing infrastructure |
| **Azure App Service** | $13-35/mo | Low | High | Production, team use |
| **Azure Container Apps** | $30-50/mo | Medium | Very High | Auto-scaling needs |

### 3.2 Quick Decision Guide

```
┌─────────────────────────────────────────────────────────────┐
│  Is this for production?                                     │
│     ├─ No → Local Deployment (Section 4)                    │
│     └─ Yes → Do you need auto-scaling?                      │
│            ├─ No → Azure App Service (Section 6)            │
│            └─ Yes → Azure Container Apps                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Local Development Deployment

### 4.1 Step-by-Step Setup

#### Step 1: Clone Repository

```bash
git clone <repository-url>
cd azure-governance-platform
```

#### Step 2: Create Virtual Environment

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

#### Step 3: Install Dependencies

```bash
uv pip install -e . --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
```

#### Step 4: Configure Environment

```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

#### Step 5: Initialize Database

```bash
python -c "from app.core.database import init_db; init_db()"
```

#### Step 6: Start Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4.2 Verification

Check the application is running:

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "0.1.0"}

# Open dashboard
open http://localhost:8000
```

---

## 5. Docker Deployment

### 5.1 Using Docker (Basic)

#### Step 1: Build Image

```bash
docker build -t azure-governance-platform:latest .
```

#### Step 2: Run Container

```bash
docker run -d \
  --name governance-platform \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  azure-governance-platform:latest
```

### 5.2 Using Docker Compose (Recommended)

#### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: governance-platform
    ports:
      - "8000:8000"
    environment:
      - AZURE_TENANT_ID=${AZURE_TENANT_ID}
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
      - DEBUG=false
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### Deploy with Compose

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Update
docker-compose pull
docker-compose up -d
```

### 5.3 Production Docker Configuration

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy requirements
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv pip install --system -e .

# Copy application
COPY app/ ./app/

# Create data directory
RUN mkdir -p /app/data

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 6. Azure App Service Deployment (Recommended)

### 6.1 Prerequisites

- Azure CLI installed and logged in: `az login`
- Resource provider registered: `Microsoft.Web`

### 6.2 One-Click Deployment Script

Save this as `deploy.sh`:

```bash
#!/bin/bash

# Configuration
RESOURCE_GROUP="rg-governance-platform"
APP_NAME="governance-platform-$(date +%s)"  # Unique name
LOCATION="eastus"
SKU="B1"  # B1=$13/mo, S1=$35/mo
PYTHON_VERSION="3.11"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment...${NC}"

# Create resource group
echo -e "${YELLOW}Creating resource group...${NC}"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output none

# Create App Service plan
echo -e "${YELLOW}Creating App Service plan...${NC}"
az appservice plan create \
  --name "${APP_NAME}-plan" \
  --resource-group $RESOURCE_GROUP \
  --sku $SKU \
  --is-linux \
  --output none

# Create Web App
echo -e "${YELLOW}Creating Web App...${NC}"
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan "${APP_NAME}-plan" \
  --runtime "PYTHON:${PYTHON_VERSION}" \
  --output none

# Configure environment variables
echo -e "${YELLOW}Configuring environment variables...${NC}"
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    AZURE_TENANT_ID="$AZURE_TENANT_ID" \
    AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
    AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
    DEBUG="false" \
    LOG_LEVEL="INFO" \
  --output none

# Deploy code
echo -e "${YELLOW}Deploying application...${NC}"
az webapp up \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none

# Enable HTTPS only
echo -e "${YELLOW}Enabling HTTPS...${NC}"
az webapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --https-only true \
  --output none

# Get the URL
URL=$(az webapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "defaultHostName" \
  -o tsv)

echo -e "${GREEN}✓ Deployment complete!${NC}"
echo -e "${GREEN}Application URL: https://$URL${NC}"
echo -e "${YELLOW}Health check: https://$URL/health${NC}"
```

### 6.3 Manual Deployment Steps

#### Step 1: Login to Azure

```bash
az login
az account set --subscription "Your Subscription Name"
```

#### Step 2: Create Resources

```bash
# Variables
RESOURCE_GROUP="rg-governance-platform"
APP_NAME="your-unique-app-name"
LOCATION="eastus"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create App Service plan (B1 = ~$13/month)
az appservice plan create \
  --name "${APP_NAME}-plan" \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan "${APP_NAME}-plan" \
  --runtime "PYTHON:3.11"
```

#### Step 3: Configure Environment Variables

```bash
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    AZURE_TENANT_ID="your-tenant-id" \
    AZURE_CLIENT_ID="your-client-id" \
    AZURE_CLIENT_SECRET="your-secret" \
    DEBUG="false" \
    LOG_LEVEL="INFO"
```

#### Step 4: Deploy Code

```bash
# From project root
az webapp up --name $APP_NAME --resource-group $RESOURCE_GROUP
```

#### Step 5: Enable Security Features

```bash
# HTTPS only
az webapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --https-only true

# Enable managed identity (optional, for Key Vault access)
az webapp identity assign \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### 6.4 Post-Deployment Configuration

#### Configure Custom Domain (Optional)

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname "governance.yourcompany.com"

# Upload SSL certificate (if using custom domain)
az webapp config ssl upload \
  --certificate-file cert.pfx \
  --certificate-password $CERT_PASSWORD \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP
```

#### Configure Deployment Slots (Recommended for Production)

```bash
# Create staging slot
az webapp deployment slot create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging

# Swap slots
az webapp deployment slot swap \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --slot staging
```

---

## 7. Database Initialization

### 7.1 Automatic Initialization

The database is automatically initialized on first startup. No manual action required.

### 7.2 Manual Database Setup

If you need to manually initialize or reset the database:

```bash
# Initialize
python -c "from app.core.database import init_db; init_db()"

# Seed with sample data
python scripts/seed_data.py

# Initialize Riverside data (if enabled)
python scripts/init_riverside_db.py
```

### 7.3 Database Backup and Restore

#### Backup

```bash
# SQLite backup
cp data/governance.db "data/governance-backup-$(date +%Y%m%d).db"

# Or compress
tar -czf "backup-$(date +%Y%m%d).tar.gz" data/governance.db
```

#### Restore

```bash
# Stop application first!
cp data/governance-backup-YYYYMMDD.db data/governance.db

# Restart application
```

### 7.4 Database Migrations

If you upgrade to a version with schema changes:

```bash
# The application handles migrations automatically
# If manual intervention is needed:
python scripts/migrate_database.py
```

---

## 8. Azure Lighthouse Setup (Optional)

Azure Lighthouse allows you to manage multiple tenants with a single App Registration in your managing tenant.

### 8.1 When to Use Lighthouse

| Use Lighthouse | Don't Use Lighthouse |
|----------------|---------------------|
| Centralized IT team | Decentralized tenant ownership |
| Standardized governance | Different security requirements per tenant |
| 10+ tenants to manage | Only 2-3 tenants |
| MSP scenario | Each tenant wants full control |

### 8.2 Lighthouse Deployment

#### Step 1: Create ARM Template

Save as `lighthouse-deployment.json`:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-08-01/subscriptionDeploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "mspName": {
      "type": "string",
      "defaultValue": "Governance Platform"
    },
    "mspOfferDescription": {
      "type": "string",
      "defaultValue": "Multi-tenant governance monitoring"
    },
    "managedByTenantId": {
      "type": "string",
      "metadata": {
        "description": "Managing tenant ID"
      }
    },
    "principalId": {
      "type": "string",
      "metadata": {
        "description": "Service principal ID from managing tenant"
      }
    }
  },
  "variables": {
    "mspRegistrationName": "[guid(parameters('mspName'))]",
    "mspAssignmentName": "[guid(parameters('principalId'))]"
  },
  "resources": [
    {
      "type": "Microsoft.ManagedServices/registrationDefinitions",
      "apiVersion": "2020-02-01-preview",
      "name": "[variables('mspRegistrationName')]",
      "properties": {
        "registrationDefinitionName": "[parameters('mspName')]",
        "description": "[parameters('mspOfferDescription')]",
        "managedByTenantId": "[parameters('managedByTenantId')]",
        "authorizations": [
          {
            "principalId": "[parameters('principalId')]",
            "principalIdDisplayName": "Governance Platform Service",
            "roleDefinitionId": "acdd72a7-3385-48ef-bd42-f606fba81ae7"
          },
          {
            "principalId": "[parameters('principalId')]",
            "principalIdDisplayName": "Governance Platform Service",
            "roleDefinitionId": "72fafb9e-0641-4937-9268-a91bfd8191a3"
          }
        ]
      }
    },
    {
      "type": "Microsoft.ManagedServices/registrationAssignments",
      "apiVersion": "2020-02-01-preview",
      "name": "[variables('mspAssignmentName')]",
      "dependsOn": [
        "[resourceId('Microsoft.ManagedServices/registrationDefinitions', variables('mspRegistrationName'))]"
      ],
      "properties": {
        "registrationDefinitionId": "[resourceId('Microsoft.ManagedServices/registrationDefinitions', variables('mspRegistrationName'))]"
      }
    }
  ]
}
```

#### Step 2: Deploy to Each Managed Tenant

```bash
# For each managed tenant
az account set --subscription "Managed Tenant Subscription"

az deployment sub create \
  --name "governance-lighthouse" \
  --location eastus \
  --template-file lighthouse-deployment.json \
  --parameters \
    managedByTenantId="your-managing-tenant-id" \
    principalId="your-service-principal-id"
```

#### Step 3: Configure Platform

In your `.env`:

```bash
# Primary tenant (managing tenant)
AZURE_TENANT_ID=your-managing-tenant-id
AZURE_CLIENT_ID=your-app-id
AZURE_CLIENT_SECRET=your-secret

# Managed tenants (via Lighthouse)
MANAGED_TENANT_IDS=tenant-id-1,tenant-id-2,tenant-id-3
```

---

## 9. Post-Deployment Verification

### 9.1 Health Check Checklist

```bash
# Replace with your actual URL
BASE_URL="https://your-app.azurewebsites.net"

# 1. Basic health
curl "$BASE_URL/health"
# Expected: {"status": "healthy", "version": "0.1.0"}

# 2. Detailed health
curl "$BASE_URL/health/detailed"
# Expected: All components "healthy" or "running"

# 3. System status
curl "$BASE_URL/api/v1/status"
# Expected: Database and scheduler running

# 4. List tenants (should be empty initially)
curl "$BASE_URL/api/v1/tenants"
# Expected: [] or list of tenants
```

### 9.2 Register Test Tenant

```bash
# Add your first tenant
curl -X POST "$BASE_URL/api/v1/tenants" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Tenant",
    "tenant_id": "your-tenant-id",
    "description": "First managed tenant"
  }'

# Verify it was created
curl "$BASE_URL/api/v1/tenants"
```

### 9.3 Trigger Test Sync

```bash
# Trigger a manual sync
curl -X POST "$BASE_URL/api/v1/sync/resources"

# Check sync status
curl "$BASE_URL/api/v1/sync/status"

# View sync history (after a minute)
curl "$BASE_URL/api/v1/sync/history?limit=5"
```

### 9.4 Dashboard Verification

1. Open the dashboard in a browser
2. Verify all cards load without errors
3. Check that navigation works
4. Test a few API endpoints via the browser console

### 9.5 Final Checklist

- [ ] Application responds to health checks
- [ ] Database is accessible
- [ ] Scheduler is running
- [ ] Azure credentials are valid (`azure_configured: true`)
- [ ] At least one tenant is registered
- [ ] Manual sync completes successfully
- [ ] Dashboard loads without errors
- [ ] HTTPS is enforced (production)

---

## 10. Troubleshooting

### 10.1 Deployment Issues

#### Issue: App Service deployment fails

**Symptoms:**
```
ERROR: Failed to deploy web app
```

**Solutions:**
```bash
# Check app logs
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP

# Verify Python version
az webapp config show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "linuxFxVersion"

# Restart app
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP
```

#### Issue: Application won't start

**Symptoms:**
- 502 Bad Gateway errors
- "Service Unavailable"

**Solutions:**
```bash
# Check if SCM_DO_BUILD_DURING_DEPLOYMENT is set
az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP

# Set if missing
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true

# Redeploy
az webapp up --name $APP_NAME --resource-group $RESOURCE_GROUP
```

#### Issue: Environment variables not loading

**Symptoms:**
- `azure_configured: false` in health check
- Missing configuration errors

**Solutions:**
```bash
# Verify settings
az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP

# Restart to apply settings
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP
```

### 10.2 Runtime Issues

#### Issue: Database errors

**Symptoms:**
```
database is locked
Unable to open database file
```

**Solutions:**
```bash
# For App Service, ensure data directory is writable
# Add to startup command:
mkdir -p /home/data

# Or use Azure Files for persistent storage
az webapp config storage-account add \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --custom-id DataVolume \
  --storage-type AzureFiles \
  --account-name $STORAGE_ACCOUNT \
  --share-name data \
  --mount-path /home/data
```

#### Issue: Sync jobs failing

**Symptoms:**
- No data appearing in dashboard
- Failed sync job logs

**Solutions:**
```bash
# Check sync logs
curl "$BASE_URL/api/v1/sync/history?limit=10"

# Check for specific errors
curl "$BASE_URL/api/v1/sync/alerts"

# Verify Azure credentials are still valid
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID
```

### 10.3 Performance Issues

#### Issue: Slow dashboard loading

**Solutions:**
- Enable caching: Set `CACHE_ENABLED=true`
- Increase App Service plan: Upgrade from B1 to S1
- Optimize database queries

#### Issue: High memory usage

**Solutions:**
- Reduce sync frequency
- Enable pagination for large datasets
- Consider upgrading App Service plan

### 10.4 Getting Help

If you're stuck:

1. **Check application logs:**
   ```bash
   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```

2. **Enable debug mode temporarily:**
   ```bash
   az webapp config appsettings set \
     --name $APP_NAME \
     --resource-group $RESOURCE_GROUP \
     --settings DEBUG=true LOG_LEVEL=DEBUG
   ```

3. **Review documentation:**
   - [Common Pitfalls](./COMMON_PITFALLS.md)
   - [API Documentation](./API.md)
   - [Architecture Overview](../ARCHITECTURE.md)

---

## 11. Security Hardening

### 11.1 Required Security Measures

| Measure | Priority | How to Implement |
|---------|----------|------------------|
| HTTPS only | Critical | `--https-only true` |
| Managed Identity | High | `az webapp identity assign` |
| Key Vault integration | High | Store secrets in Key Vault |
| IP Restrictions | Medium | Configure access restrictions |
| Azure AD Auth | Medium | Enable Easy Auth |

### 11.2 Enable Azure AD Authentication

```bash
# Configure Azure AD authentication
az webapp auth update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --enabled true \
  --action LoginWithAzureActiveDirectory \
  --aad-allowed-token-audiences https://$APP_NAME.azurewebsites.net \
  --aad-client-id $AZURE_CLIENT_ID \
  --aad-client-secret $AZURE_CLIENT_SECRET \
  --aad-token-issuer-url https://login.microsoftonline.com/$AZURE_TENANT_ID/v2.0
```

### 11.3 Configure IP Restrictions

```bash
# Allow only specific IPs
az webapp config access-restriction add \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --action Allow \
  --ip-address 203.0.113.0/24 \
  --name "Office Network"

# Deny all others (implicit)
```

### 11.4 Key Vault Integration

```bash
# Create Key Vault
az keyvault create \
  --name "kv-governance-$RANDOM" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Add secrets
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "azure-client-secret" \
  --value "$AZURE_CLIENT_SECRET"

# Grant app access to Key Vault
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $APP_OBJECT_ID \
  --secret-permissions get list

# Update app settings
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    KEY_VAULT_URL="https://$KEY_VAULT_NAME.vault.azure.net/"
```

---

## 12. Backup and Recovery

### 12.1 Automated Backups

For App Service, configure automated backups:

```bash
az webapp config backup create \
  --resource-group $RESOURCE_GROUP \
  --webapp-name $APP_NAME \
  --backup-name "daily-backup" \
  --storage-account-url "https://$STORAGE_ACCOUNT.blob.core.windows.net/backups" \
  --frequency 1d \
  --retention 30
```

### 12.2 Database Backup Strategy

| Method | Frequency | Retention | Automation |
|--------|-----------|-----------|------------|
| SQLite file copy | Daily | 30 days | Cron job/script |
| Azure Files snapshot | Weekly | 12 weeks | Azure Backup |
| Export to Blob | Monthly | 1 year | Azure Function |

### 12.3 Disaster Recovery Plan

#### RTO (Recovery Time Objective): 1 hour
#### RPO (Recovery Point Objective): 24 hours

#### Recovery Steps:

```bash
# 1. Create new App Service (if region is down)
az group create --name $DR_RESOURCE_GROUP --location $DR_LOCATION

# 2. Restore from backup
az webapp config backup restore \
  --resource-group $DR_RESOURCE_GROUP \
  --webapp-name $DR_APP_NAME \
  --backup-name "daily-backup" \
  --storage-account-url "https://$STORAGE_ACCOUNT.blob.core.windows.net/backups"

# 3. Update DNS (if using custom domain)
# 4. Verify functionality
```

### 12.4 Database Recovery

```bash
# From file backup
cp governance-backup-YYYYMMDD.db governance.db

# From Azure Files
az storage file download \
  --share-name data \
  --path governance-backup.db \
  --dest governance.db \
  --account-name $STORAGE_ACCOUNT
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | February 2025 | Initial deployment guide |

---

**Related Documents:**
- [Implementation Guide](./IMPLEMENTATION_GUIDE.md)
- [API Documentation](./API.md)
- [Operations Runbook](./RUNBOOK.md)
- [Common Pitfalls](./COMMON_PITFALLS.md)
