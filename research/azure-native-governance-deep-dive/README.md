# Azure Native Governance Tools — Deep Dive Assessment

## Research Date: 2026-03-27
## Researcher: web-puppy-bca4bd
## Sources: 12 Tier-1 Microsoft official documentation pages

---

## Executive Summary

**Question**: Can Azure's built-in governance tools replace the custom multi-tenant governance platform?

**Answer**: **No — native tools cover ~35-40% of the platform's scope.**

Three architectural blockers prevent reaching 80%:

| Blocker | Impact | Severity |
|---------|--------|----------|
| Lighthouse does NOT delegate Entra ID | Entire Identity module (10 requirements) impossible via native tools | 🔴 Critical |
| No native DMARC monitoring | Entire DMARC module has zero native coverage | 🔴 Critical |
| No cross-tenant cost aggregation/chargeback | Core cost management feature missing | 🟡 Major |

---

## Coverage Matrix

| Platform Module | Requirements | Native Coverage | Key Native Tool | Key Gap |
|----------------|-------------|----------------|-----------------|---------|
| Cost Optimization | CO-001–010 | **~45%** | Cost Management (free) | No aggregation, no chargeback |
| Compliance Monitoring | CM-001–010 | **~50%** | Defender CSPM | Can't view noncompliant details cross-tenant |
| Resource Management | RM-001–010 | **~65%** | Resource Graph (free) | Best coverage — queries span Lighthouse |
| Identity Governance | IG-001–010 | **~10%** | None via Lighthouse | Lighthouse ≠ Entra ID; per-tenant only |
| DMARC Monitoring | Custom | **0%** | None | Completely outside Azure |
| Regulatory Deadlines | Custom | **0%** | None | No deadline/countdown capability |
| Branded UX | Custom | **0%** | Azure Portal only | No branding, no non-tech UX |
| **Weighted Average** | | **~35-40%** | | |

---

## Cost Comparison (4 tenants, 50 resources, 30 users)

| Approach | Monthly Cost | Coverage |
|----------|-------------|----------|
| Native tools only | **~$2,028** | ~35% ❌ |
| Custom platform (current) | **~$577** | ~100% ✅ |
| **Hybrid (recommended)** | **~$577** | **~100% + enhanced** ✅✅ |

Native tools are **3.5× more expensive** and still leave 60%+ uncovered.

---

## Tool-by-Tool Verdicts

### 1. Azure Cost Management — ⚠️ Supplement Only
- **Free** — $0
- ✅ Per-subscription cost analysis, anomaly detection, budgets, forecasts
- ❌ No cross-tenant aggregation
- ❌ No chargeback/showback reporting
- ❌ Anomaly detection: subscription scope only, 36hr delay
- **Verdict**: Use as data source; keep custom aggregation

### 2. Microsoft Defender for Cloud — ✅ Adopt Free Tier
- **Foundational CSPM**: Free — Secure Score, basic compliance, recommendations
- **Defender CSPM**: $5.11/billable resource/month — attack path, DSPM, custom recommendations
- ✅ Cross-tenant Secure Score visibility (free)
- ✅ Cross-tenant compliance monitoring (summary level)
- ✅ Cross-tenant security recommendations
- ❌ Cannot view noncompliant resource **details** cross-tenant
- ❌ Requires full subscription delegation (not resource groups)
- ❌ No custom compliance rules, no DMARC, no deadline tracking
- **Verdict**: Enable free Foundational CSPM; skip paid Defender CSPM unless attack path analysis needed

### 3. Entra ID Governance — ❌ Does Not Solve the Problem
- **Cost**: ~$7/user/month PER TENANT → $840/month for 4 tenants × 30 users
- ✅ Per-tenant: access reviews, PIM, lifecycle workflows
- ❌ **Lighthouse does NOT delegate Entra ID** — fundamental architectural limitation
- ❌ No cross-tenant MFA compliance, stale accounts, privilege reviews
- ❌ Multi-tenant org features are B2B collaboration, NOT governance
- ❌ Cross-tenant identity governance still requires Graph API (what custom platform already does)
- **Verdict**: DO NOT purchase for cross-tenant governance; custom platform's Graph integration is the correct approach

### 4. Azure Lighthouse Portal — ⚠️ Already in Use
- **Free** — $0
- ✅ Unified subscription filter across delegated tenants
- ✅ Delegation management and activity logging
- ✅ Azure Resource Graph automatically includes delegated resources
- ❌ Not a governance dashboard — it's a subscription switcher
- ❌ No aggregated metrics, no branding, no custom reports
- ❌ Requires Azure portal expertise
- **Verdict**: Already used by custom platform via `LighthouseAzureClient`; portal itself is not a replacement

### 5. Azure Monitor Workbooks — ⚠️ Complement Only
- **Free** (workbooks) + ~$50-200/month (Log Analytics ingestion)
- ✅ Rich cross-tenant visualization via Resource Graph
- ✅ Multiple data sources, parameterized queries
- ❌ Cannot query Entra ID data (no Microsoft Graph integration)
- ❌ Requires 80-130 hours of KQL development for governance workbooks
- ❌ No DMARC, no deadlines, no branding
- ❌ Not accessible to non-technical users
- **Verdict**: Useful for IT self-service exploration; don't build governance dashboards in workbooks

---

## Recommended Action Plan

### Immediate (Free, Zero Risk)
1. Enable Foundational CSPM on all 4 tenants
2. Verify Azure Advisor is enabled across delegated subscriptions
3. Test Azure Resource Graph cross-tenant queries

### Short-Term (8-16 hours)
4. Integrate Secure Score API into custom compliance dashboard
5. Add Advisor recommendations to custom recommendations page
6. Evaluate Azure Resource Graph for richer resource queries

### Avoid
7. ❌ Do NOT purchase Entra ID Governance for cross-tenant use
8. ❌ Do NOT build governance dashboards in Azure Workbooks
9. ❌ Do NOT attempt to replace the custom platform with native tools

---

## File Index

| File | Contents |
|------|----------|
| [analysis.md](analysis.md) | Multi-dimensional analysis with per-requirement coverage tables |
| [recommendations.md](recommendations.md) | Project-specific recommendations with prioritized actions |
| [sources.md](sources.md) | 12 Tier-1 sources with credibility assessments |
| [raw-findings/01-cost-management.md](raw-findings/01-cost-management.md) | Azure Cost Management deep dive |
| [raw-findings/02-defender-for-cloud.md](raw-findings/02-defender-for-cloud.md) | Microsoft Defender for Cloud deep dive |
| [raw-findings/03-entra-id-governance.md](raw-findings/03-entra-id-governance.md) | Entra ID Governance + multi-tenant capabilities |
| [raw-findings/04-lighthouse-portal.md](raw-findings/04-lighthouse-portal.md) | Lighthouse portal experience + limitations |
| [raw-findings/05-monitor-workbooks.md](raw-findings/05-monitor-workbooks.md) | Azure Monitor Workbooks cross-tenant analysis |
