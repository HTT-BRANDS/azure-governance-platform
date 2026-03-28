# Azure Native Multi-Tenant Governance Tools vs Custom Platform

## Executive Summary

**Research Question**: Can Azure's built-in multi-tenant governance tools replace the custom Azure Governance Platform?

**Bottom Line**: Native Azure tools can replace approximately **35-45% of the custom platform** for Azure resource governance (costs, compliance, resources), but only **10-15% for identity governance**. The overall replacement potential is roughly **30-40%**, leaving significant gaps that require custom development or significant Kusto/workbook expertise.

**Critical Finding**: Azure Lighthouse delegates **Azure resource management**, NOT **Microsoft Entra ID (identity) management**. This fundamental architectural limitation means the entire Identity Governance module (IG-001 through IG-010) cannot be replicated with native tools via Lighthouse.

---

## Quick Comparison Matrix

| Custom Platform Module | Native Tool Coverage | Key Gap |
|------------------------|---------------------|---------|
| Cost Optimization (CO-001–CO-010) | ~45% | No cross-tenant aggregation, no chargeback |
| Compliance Monitoring (CM-001–CM-010) | ~55% | Can't view non-compliant resource details cross-tenant |
| Resource Management (RM-001–RM-010) | ~65% | Best coverage via Azure Resource Graph |
| Identity Governance (IG-001–IG-010) | ~10% | Entra ID Governance is per-tenant only |
| Unified Dashboard | ~40% | Workbooks require deep Kusto expertise |

## Verdict by Scenario

### ✅ Consider native tools if:
- You ONLY need resource-level governance (no identity)
- You have Kusto/KQL expertise to build custom workbooks
- You can tolerate per-subscription views (no aggregation)
- You don't need chargeback/showback reporting
- You don't need custom branding per tenant

### ❌ Keep the custom platform if:
- You need cross-tenant identity governance (MFA, stale accounts, access reviews)
- You need unified cost aggregation across tenants
- You need chargeback/showback reporting
- You need a branded, non-technical user experience
- You need compliance detail drill-down across tenants

## Pricing Summary (10-30 users, 4+ tenants)

| Tool | Annual Cost Estimate |
|------|---------------------|
| Azure Lighthouse | **$0** (free) |
| Azure Cost Management | **$0** (free for Azure subscriptions) |
| Defender for Cloud (Foundational CSPM) | **$0** (free - Secure Score + basic compliance) |
| Defender for Cloud (Advanced CSPM) | **~$200-2,000/mo** (depends on resource count) |
| Entra ID Governance add-on | **~$7/user/mo per tenant** = $280-840/mo for 10-30 users × 4 tenants |
| Azure Monitor Workbooks | **$0** (free, but Log Analytics ingestion costs apply) |
| Azure Monitor Logs ingestion | **~$50-200/mo** (depends on volume, first 5GB/day free) |
| **Custom Platform (App Service B2)** | **~$55-110/mo** (hosting) + dev/maintenance time |

## Key Research Files
- [analysis.md](analysis.md) - Detailed tool-by-tool analysis with coverage percentages
- [sources.md](sources.md) - All sources with credibility assessments
- [recommendations.md](recommendations.md) - Project-specific recommendations
- [raw-findings/](raw-findings/) - Extracted data from each source
