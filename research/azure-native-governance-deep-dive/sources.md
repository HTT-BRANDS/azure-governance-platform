# Sources & Credibility Assessment

## Research Date: 2026-03-27
## Researcher: web-puppy-bca4bd

---

## Tier 1 Sources (Official Documentation — Highest Credibility)

### 1. Azure Cost Management Overview
- **URL**: https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/overview-cost-management
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Actively maintained, part of current product documentation
- **Validation**: Cross-referenced with pricing page and Lighthouse docs
- **Bias**: Vendor documentation — naturally highlights capabilities
- **Primary/Secondary**: Primary source

### 2. Azure Lighthouse — Cross-Tenant Management Experiences
- **URL**: https://learn.microsoft.com/en-us/azure/lighthouse/concepts/cross-tenant-management-experience
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current — includes latest service integrations and limitations
- **Validation**: Cross-referenced with individual service docs
- **Bias**: Vendor documentation — lists both capabilities AND limitations transparently
- **Primary/Secondary**: Primary source — definitive list of supported/unsupported scenarios
- **KEY CREDIBILITY NOTE**: The "Current limitations" section is unusually transparent about what doesn't work

### 3. Azure Cost Management — Anomaly Detection
- **URL**: https://learn.microsoft.com/en-us/azure/cost-management-billing/understand/analyze-unexpected-charges
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current, includes Insights feature and smart views
- **Validation**: Confirmed subscription-scope limitation via multiple doc pages
- **Bias**: Vendor documentation
- **Primary/Secondary**: Primary source

### 4. Microsoft Defender for Cloud — Cross-Tenant Management
- **URL**: https://learn.microsoft.com/en-us/azure/defender-for-cloud/cross-tenant-management
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current
- **Validation**: Cross-referenced with CSPM overview and pricing page
- **Bias**: Vendor documentation
- **Primary/Secondary**: Primary source

### 5. Defender for Cloud — CSPM Overview
- **URL**: https://learn.microsoft.com/en-us/azure/defender-for-cloud/concept-cloud-security-posture-management
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current — includes April 2026 Serverless billing change
- **Validation**: Cross-referenced with pricing page
- **Bias**: Vendor documentation
- **Primary/Secondary**: Primary source — definitive feature comparison table

### 6. Defender for Cloud Pricing
- **URL**: https://azure.microsoft.com/en-us/pricing/details/defender-for-cloud/
- **Authority**: Official Microsoft Azure pricing page
- **Currency**: Current (Central US, USD pricing as of 2026-03-27)
- **Validation**: Pricing from Azure official pricing page
- **Bias**: Vendor pricing — authoritative
- **Primary/Secondary**: Primary source

### 7. Microsoft Entra ID Governance Overview
- **URL**: https://learn.microsoft.com/en-us/entra/id-governance/identity-governance-overview
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current — includes Access Review Agent (Preview) and Security Copilot
- **Validation**: Cross-referenced with licensing fundamentals page
- **Bias**: Vendor documentation — focuses on per-tenant capabilities
- **Primary/Secondary**: Primary source

### 8. Entra ID Governance Licensing Fundamentals
- **URL**: https://learn.microsoft.com/en-us/entra/id-governance/licensing-fundamentals
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current — includes Entra Suite and latest license types
- **Validation**: Cross-referenced with Microsoft commercial pricing
- **Bias**: Vendor pricing documentation
- **Primary/Secondary**: Primary source

### 9. Multitenant Organization Capabilities in Microsoft Entra ID
- **URL**: https://learn.microsoft.com/en-us/entra/identity/multi-tenant-organizations/overview
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current
- **Validation**: Confirms multi-tenant features are B2B-focused, not governance
- **Bias**: Vendor documentation — clearly describes collaboration use cases
- **Primary/Secondary**: Primary source — definitive for cross-tenant Entra capabilities

### 10. Azure Lighthouse — View and Manage Customers
- **URL**: https://learn.microsoft.com/en-us/azure/lighthouse/how-to/view-manage-customers
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current
- **Validation**: Verified portal UI descriptions match current portal
- **Bias**: Vendor documentation
- **Primary/Secondary**: Primary source for portal experience

### 11. Azure Monitor Workbooks Overview
- **URL**: https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/workbooks-overview
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current — includes Dashboard Preview features
- **Validation**: Cross-referenced with data sources and access control docs
- **Bias**: Vendor documentation
- **Primary/Secondary**: Primary source

### 12. Azure Resource Graph — Query Language
- **URL**: https://learn.microsoft.com/en-us/azure/governance/resource-graph/concepts/query-language
- **Authority**: Official Microsoft Learn documentation
- **Currency**: Current — API version 2021-06-01-preview referenced
- **Validation**: Confirmed cross-tenant scope includes Lighthouse delegations
- **Bias**: Vendor documentation
- **Primary/Secondary**: Primary source — critical for cross-tenant query capabilities

---

## Source Quality Summary

| Metric | Assessment |
|--------|-----------|
| Total sources consulted | 12 |
| Tier 1 (Official docs) | 12 (100%) |
| Tier 2 (Tech publications) | 0 |
| Tier 3 (Community) | 0 |
| Tier 4 (Blogs) | 0 |
| Cross-referenced findings | All key limitations verified across 2+ sources |
| Publication dates | All current (2025-2026 updates) |
| Potential bias noted | Vendor documentation — limitations section explicitly checked |

## Methodology Notes
- All findings are from official Microsoft documentation only — Tier 1 sources
- Every capability claim was verified against the Lighthouse cross-tenant management page
- Every limitation was checked against both the specific tool's docs AND the Lighthouse limitations page
- Pricing was captured from the official Azure pricing page (Central US, USD, monthly)
- The critical Lighthouse/Entra ID separation was confirmed across multiple independent documentation pages
