# Project-Specific Recommendations

## Research Date: 2026-03-27
## Context: azure-governance-platform (4-tenant multi-brand governance)

---

## Executive Verdict

### Can Azure native tools replace the custom platform?

# **No. Native tools cover ~35-40% of the platform's scope.**

The platform cannot reach 80% native coverage due to three **architectural blockers**:

1. **Azure Lighthouse does NOT delegate Entra ID** — the entire Identity Governance module (IG-001 through IG-010) requires Microsoft Graph API with per-tenant app registrations, which is exactly what the custom platform already does
2. **No native DMARC monitoring** — completely outside Azure tool ecosystem
3. **No native cross-tenant cost aggregation with chargeback** — Cost Management provides per-subscription views, not unified tenant-level allocation

---

## Recommended Strategy: Selective Hybrid

### Tier 1: Use Native Tools NOW (Free, Zero Risk)

These native tools can be adopted immediately to supplement (not replace) the custom platform:

| Native Tool | What It Adds | Integration With Custom Platform |
|-------------|-------------|--------------------------------|
| Foundational CSPM (Free) | Secure Score + basic compliance baseline | Surface Secure Score data in custom dashboard via API |
| Azure Resource Graph | Richer cross-tenant resource queries | Replace ARM-based queries in `resource_service.py` with ARG |
| Azure Advisor | Right-sizing + idle VM recommendations | Pull Advisor recommendations into custom recommendations page |
| Azure Cost Management Exports | Scheduled cost data exports | Use exports as data source instead of direct API calls |

**Effort**: ~8-16 hours to integrate
**Cost**: $0
**Risk**: Low — additive, no breaking changes

### Tier 2: Consider for Future (Conditional Value)

| Native Tool | When It Makes Sense | When It Doesn't |
|-------------|--------------------|--------------------|
| Defender CSPM ($5.11/resource/mo) | If you need attack path analysis or DSPM | Not worth it for just compliance monitoring |
| Azure Monitor Workbooks | If IT-savvy users want self-service exploration | Don't build governance dashboards in workbooks — maintain custom UI |
| Entra ID Governance ($7/user/tenant/mo) | If you need PIM/access reviews within individual tenants | Does NOT solve cross-tenant governance — don't buy for this purpose |

### Tier 3: DO NOT Adopt (Anti-Patterns)

| Approach | Why Not |
|----------|---------|
| Replace custom platform with native tools entirely | Only covers ~35% of scope; identity, DMARC, deadlines still need custom |
| Build governance dashboards in Azure Workbooks | Requires advanced KQL, no branding, no Entra ID data, maintenance burden |
| Buy Entra ID Governance for cross-tenant identity | Per-tenant only; cross-tenant still requires Graph API integration (what you already have) |
| Use Lighthouse portal as governance UI | It's a subscription switcher, not a governance dashboard; requires Azure expertise |

---

## Detailed Recommendation per Module

### Cost Management (CO-001–CO-010)
**Recommendation**: Keep custom platform, enhance with native data

**Keep Custom**:
- Cross-tenant cost aggregation (CO-001) — native can't do this
- Chargeback/showback reporting (CO-010) — no native equivalent
- Unified cost trending across tenants (CO-002)

**Enhance with Native**:
- Use Azure Advisor API for idle resource detection (CO-005) and right-sizing (CO-006)
- Use Cost Management anomaly alerts as a supplement to custom anomaly detection (CO-003)
- Consider Cost Management Exports for more efficient data ingestion

### Compliance Monitoring (CM-001–CM-010)
**Recommendation**: Supplement with free Foundational CSPM

**Keep Custom**:
- Custom compliance rule engine (CM-002) — Azure Policy can't replicate JSON Schema rules
- Regulatory framework mapping (CM-003) — built-in benchmarks are too generic
- Non-compliant resource details (CM-007) — Lighthouse can't show cross-tenant detail

**Supplement with Native**:
- Pull Secure Score from Defender for Cloud API (free) to enhance CM-006
- Use Azure Policy compliance states via Resource Graph for CM-001 data
- Leverage Defender recommendations for CM-005

### Resource Management (RM-001–RM-010)
**Recommendation**: Strongest native coverage — consider partial migration

**Consider Migrating to Native**:
- Cross-tenant resource inventory (RM-001) — Azure Resource Graph is excellent
- Resource change history (RM-010) — Resource Graph Change Analysis
- Tag enforcement reporting (RM-009) — Azure Policy cross-tenant

**Keep Custom**:
- Resource provisioning standards (RM-008) — no native equivalent
- Orphaned resource detection (RM-003) — needs custom logic beyond Advisor
- Quota monitoring (RM-007) — custom aggregation needed

### Identity Governance (IG-001–IG-010)
**Recommendation**: Keep 100% custom — no native alternative exists

**Rationale**: Azure Lighthouse does not delegate Entra ID. There is no native way to:
- Query user MFA status across tenants
- Detect stale accounts across tenants
- Review privileged access across tenants
- Inventory guest users across tenants

The custom platform's `graph_client.py` (44.6 KB) with per-tenant app registrations is the ONLY viable approach for cross-tenant identity governance. Even Microsoft's own multi-tenant organization features (B2B, cross-tenant sync) are designed for collaboration, not governance.

### DMARC Monitoring
**Recommendation**: Keep 100% custom — zero native coverage

No Azure service provides DMARC monitoring. The custom `dmarc_service.py` (22.0 KB) is the only option.

### Regulatory Deadline Tracking (Riverside)
**Recommendation**: Keep 100% custom — zero native coverage

No Azure service provides date-driven compliance deadline tracking with countdown timers. The custom Riverside compliance module is unique to this platform's requirements.

---

## Prioritized Action Items

### Immediate (This Sprint)
1. **[FREE]** Enable Foundational CSPM on all 4 tenants if not already done
2. **[FREE]** Verify Azure Advisor is enabled across all delegated subscriptions
3. **[FREE]** Test Azure Resource Graph queries across Lighthouse-delegated tenants

### Next Sprint
4. **[8 hours]** Add Secure Score API integration to `compliance_service.py`
5. **[4 hours]** Add Azure Advisor recommendations to `recommendation_service.py`
6. **[8 hours]** Evaluate replacing ARM resource queries with Azure Resource Graph

### Future Consideration
7. **[When needed]** Evaluate Defender CSPM if attack path analysis becomes a requirement
8. **[When needed]** Build Azure Monitor Workbooks for IT self-service exploration (complement, not replace)
9. **[Never]** Do not purchase Entra ID Governance add-on for cross-tenant governance

---

## Cost Impact Summary

| Action | Monthly Cost Impact | Value |
|--------|-------------------|-------|
| Enable Foundational CSPM | +$0 | Adds Secure Score + basic compliance |
| Integrate Azure Advisor | +$0 | Better idle resource & right-sizing data |
| Use Azure Resource Graph | +$0 | Richer cross-tenant resource queries |
| Keep custom platform | $577 (unchanged) | Full governance coverage |
| **Hybrid total** | **~$577/month** | **Enhanced coverage at same cost** |

vs.

| Alternative | Monthly Cost | Coverage |
|-------------|-------------|----------|
| Native tools only | ~$2,028/month | ~35% of requirements |
| Custom platform only | ~$577/month | ~100% of requirements |
| **Hybrid (recommended)** | **~$577/month** | **~100% + enhanced data** |

---

## Risk Assessment

### Risk of Staying Custom
- **Low**: Platform is built and tested (~170 test files)
- **Medium**: Ongoing maintenance burden (Python/FastAPI/Azure SDK updates)
- **Low**: Vendor lock-in is minimal — uses standard Azure APIs

### Risk of Migrating to Native
- **High**: Would lose 60-65% of current functionality (identity, DMARC, deadlines)
- **High**: Would require $840/month for Entra ID Governance that still doesn't solve cross-tenant
- **Medium**: Workbook development is specialized and fragile
- **High**: Non-technical users would lose branded, accessible interface

### Recommended Risk Mitigation
- Adopt free native tools as data sources (Foundational CSPM, Resource Graph, Advisor)
- Keep custom platform as the governance UI and aggregation layer
- Monitor Azure roadmap for Lighthouse → Entra ID delegation (if Microsoft ever adds this, reassess)
