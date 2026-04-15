# Source Credibility Assessment

## Sources Used

### 1. Azure Retail Prices REST API
- **URL**: `https://prices.azure.com/api/retail/prices`
- **Tier**: 🟢 **Tier 1 (Highest)** — Official Microsoft API
- **Authority**: Official Microsoft Azure pricing API, publicly accessible, no authentication required
- **Currency**: Real-time pricing data; reflects current retail prices
- **Validation**: This is the same data source that powers the Azure Pricing Calculator
- **Bias**: None — raw pricing data from Microsoft
- **Queries executed**:
  - `serviceName eq 'Azure App Service' and armRegionName eq 'westus2' and skuName eq 'B1' and productName eq 'Azure App Service Basic Plan - Linux'`
  - `serviceName eq 'Azure App Service' and armRegionName eq 'westus2' and skuName eq 'S1' and productName eq 'Azure App Service Standard Plan - Linux'`
  - `serviceName eq 'Azure App Service' and armRegionName eq 'westus2' and skuName eq 'P1 v3' and productName eq 'Azure App Service Premium v3 Plan - Linux'`
  - `serviceName eq 'SQL Database' and armRegionName eq 'westus2' and skuName eq 'S0'`
  - `serviceName eq 'SQL Database' and armRegionName eq 'westus2' and contains(skuName, 'Free')`
  - `serviceName eq 'Container Registry' and armRegionName eq 'westus2' and skuName eq 'Basic'`
  - `serviceName eq 'Container Registry' and armRegionName eq 'westus2' and skuName eq 'Standard'`
  - `serviceName eq 'Key Vault' and armRegionName eq 'westus2' and skuName eq 'Standard'`
  - `serviceName eq 'Log Analytics' and armRegionName eq 'westus2'`
  - `serviceName eq 'Azure Monitor' and armRegionName eq 'westus2' and contains(meterName, 'Data Ingestion')`

### 2. Azure Pricing Web Pages
- **URLs**:
  - `https://azure.microsoft.com/en-us/pricing/details/app-service/linux/`
  - `https://azure.microsoft.com/en-us/pricing/details/azure-sql-database/single/`
  - `https://azure.microsoft.com/en-us/pricing/details/monitor/`
- **Tier**: 🟢 **Tier 1 (Highest)** — Official Microsoft pricing pages
- **Authority**: Official Azure documentation
- **Currency**: Updated continuously; region-specific pricing confirmed
- **Usage**: Cross-verification of API results; visual confirmation of pricing tables
- **Note**: Web pages showed $2.30/GB for Log Analytics Pay-As-You-Go, matching API data

### 3. Microsoft Learn — Deployment Slots Documentation
- **URL**: `https://learn.microsoft.com/en-us/azure/app-service/deploy-staging-slots`
- **Tier**: 🟢 **Tier 1 (Highest)** — Official Microsoft documentation
- **Authority**: Official Azure App Service documentation
- **Key Quote**: "This approach is available if you run in the Standard, Premium, or Isolated tier of an App Service plan."
- **Key Quote**: "The Standard tier supports only five deployment slots."
- **Key Quote**: "There's no extra charge for using deployment slots."

### 4. GitHub Pricing Page
- **URL**: `https://github.com/pricing`
- **Tier**: 🟢 **Tier 1 (Highest)** — Official GitHub/Microsoft pricing page
- **Authority**: Official GitHub pricing page
- **Currency**: Accessed April 15, 2026
- **Price confirmed**: Enterprise Cloud at $21/user/month (shown as "Starting at")

## Cross-Validation Summary

| Data Point | API Price | Web Page | Status |
|-----------|----------|----------|--------|
| App Service B1 Linux | $0.017/hr | Confirmed | ✅ Match |
| App Service S1 Linux | $0.080/hr | Confirmed | ✅ Match |
| App Service P1v3 Linux | $0.155/hr | Confirmed | ✅ Match |
| SQL DB S0 | $0.4839/day | Confirmed | ✅ Match |
| SQL DB Free | $0.00 | Confirmed | ✅ Match |
| ACR Basic | $0.1666/day (~$5/mo) | Confirmed | ✅ Match |
| ACR Standard | $0.6666/day (~$20/mo) | Confirmed | ✅ Match |
| Key Vault ops | $0.03/10K | Confirmed | ✅ Match |
| Log Analytics ingestion | $2.30/GB | $2.30/GB on web | ✅ Match |
| GitHub Enterprise | $21/user/mo | $21/user/mo on web | ✅ Match |
