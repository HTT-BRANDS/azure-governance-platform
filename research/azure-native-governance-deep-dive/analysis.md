# Multi-Dimensional Analysis: Azure Native Governance Tools vs Custom Platform

## Research Date: 2026-03-27

---

## 1. Feature Coverage Analysis — By Custom Platform Module

### CO-001–CO-010: Cost Optimization Module (Native Coverage: ~45%)

| Req ID | Requirement | Native Coverage | Native Tool | Gap |
|--------|-------------|----------------|-------------|-----|
| CO-001 | Aggregate costs across 4 tenants | ❌ Partial | Cost Management | Per-subscription only, no aggregation |
| CO-002 | Daily/weekly/monthly trending | ✅ Partial | Cost Analysis | Per-subscription, not cross-tenant |
| CO-003 | Cost anomaly detection & alerting | ✅ Partial | Cost Analysis | Per-subscription scope only, 36hr delay |
| CO-004 | Resource cost attribution by tags | ✅ Yes | Cost Analysis | Works via Lighthouse RBAC |
| CO-005 | Idle resource identification | ⚠️ Separate | Azure Advisor | Not in Cost Mgmt, requires Advisor |
| CO-006 | Right-sizing recommendations | ✅ Yes | Azure Advisor | Works via Lighthouse |
| CO-007 | Reserved instance utilization | ✅ Yes | Cost Management | Per-subscription view |
| CO-008 | Budget tracking per tenant/sub | ✅ Yes | Cost Management | Per-subscription budgets work |
| CO-009 | Savings opportunities dashboard | ✅ Yes | Azure Advisor | Works via Lighthouse |
| CO-010 | Chargeback/showback reporting | ❌ No | None | No native capability |

### CM-001–CM-010: Compliance Monitoring Module (Native Coverage: ~50%)

| Req ID | Requirement | Native Coverage | Native Tool | Gap |
|--------|-------------|----------------|-------------|-----|
| CM-001 | Azure Policy compliance across tenants | ⚠️ Partial | Defender + Lighthouse | Summary only, no detail drill-down |
| CM-002 | Custom compliance rule definitions | ❌ No | Azure Policy | Azure Policy only, no JSON Schema rules |
| CM-003 | Regulatory framework mapping | ⚠️ Limited | Defender CSPM | Built-in benchmarks only, no custom |
| CM-004 | Compliance drift detection | ✅ Yes | Defender for Cloud | Continuous assessment works cross-tenant |
| CM-005 | Automated remediation suggestions | ✅ Yes | Defender for Cloud | Recommendations work cross-tenant |
| CM-006 | Secure Score aggregation | ✅ Yes | Defender for Cloud | Cross-tenant visibility (free) |
| CM-007 | Non-compliant resource inventory | ⚠️ Partial | Resource Graph | Cross-tenant query but detail gap |
| CM-008 | Compliance trend reporting | ⚠️ Limited | Defender for Cloud | Per-subscription trends only |
| CM-009 | Policy exemption management | ✅ Yes | Azure Policy | Works via Lighthouse |
| CM-010 | Audit log aggregation | ⚠️ Partial | Azure Monitor | Per-subscription logs, manual aggregation |

### RM-001–RM-010: Resource Management Module (Native Coverage: ~65%)

| Req ID | Requirement | Native Coverage | Native Tool | Gap |
|--------|-------------|----------------|-------------|-----|
| RM-001 | Cross-tenant resource inventory | ✅ Yes | Resource Graph | Best native capability — automatic Lighthouse |
| RM-002 | Resource tagging compliance | ✅ Yes | Azure Policy + Graph | Cross-tenant tag auditing works |
| RM-003 | Orphaned resource detection | ⚠️ Partial | Advisor + Graph | Requires custom KQL queries |
| RM-004 | Resource lifecycle tracking | ⚠️ Partial | Resource Graph Changes | Change detection available |
| RM-005 | Subscription/RG organization view | ✅ Yes | Azure Portal | Lighthouse subscription filter |
| RM-006 | Resource health aggregation | ✅ Yes | Service Health | Cross-tenant via Lighthouse |
| RM-007 | Quota utilization monitoring | ⚠️ Partial | Compute quotas | Per-subscription, no aggregation |
| RM-008 | Resource provisioning standards | ❌ No | None | No native equivalent |
| RM-009 | Tag enforcement reporting | ✅ Yes | Azure Policy | Deny/audit policies work cross-tenant |
| RM-010 | Resource change history | ✅ Yes | Resource Graph Changes | Change Analysis works |

### IG-001–IG-010: Identity Governance Module (Native Coverage: ~10%)

| Req ID | Requirement | Native Coverage | Native Tool | Gap |
|--------|-------------|----------------|-------------|-----|
| IG-001 | Cross-tenant user inventory | ❌ No | None via Lighthouse | Lighthouse ≠ Entra ID delegation |
| IG-002 | Privileged access reporting | ❌ No | PIM (per-tenant) | Per-tenant only, no aggregation |
| IG-003 | Guest user management | ❌ No | Entra ID (per-tenant) | Per-tenant only |
| IG-004 | Stale account detection | ❌ No | Entra ID (per-tenant) | Per-tenant only |
| IG-005 | MFA compliance reporting | ❌ No | Entra ID (per-tenant) | Per-tenant only |
| IG-006 | Conditional Access policy audit | ❌ No | Entra ID (per-tenant) | Per-tenant only |
| IG-007 | Role assignment analysis | ❌ No | PIM (per-tenant) | Per-tenant only |
| IG-008 | Service principal inventory | ❌ No | Entra ID (per-tenant) | Per-tenant only |
| IG-009 | License utilization tracking | ❌ No | M365 Admin (per-tenant) | Per-tenant only |
| IG-010 | Access review facilitation | ❌ No | ID Governance (per-tenant) | Per-tenant only, requires add-on |

### Specialized Modules (Native Coverage: 0%)

| Module | Native Coverage | Gap |
|--------|----------------|-----|
| DMARC Monitoring | ❌ 0% | Completely outside Azure native tools |
| Regulatory Deadline Tracking (Riverside) | ❌ 0% | No native deadline/countdown capability |
| Multi-Brand Design System | ❌ 0% | Azure portal has no branding customization |
| Custom Compliance Rule Engine | ❌ 0% | Azure Policy only, no JSON Schema rules |

---

## 2. Security Analysis

### Native Tools Security Advantages
- **No custom code to maintain** — Microsoft manages patches and updates
- **Built-in RBAC** — Azure role-based access control
- **SOC 2/ISO certified** — Microsoft manages certifications for their tools
- **Automatic security updates** — no dependency management needed
- **Encryption at rest/transit** by default

### Native Tools Security Concerns
- **Lighthouse resource locks don't prevent managing tenant actions** — documented limitation
- **No Owner role delegation** — limits some administrative actions
- **Broad access**: Lighthouse delegates at subscription level for Defender — may be overly permissive
- **No custom audit trail** — limited to Azure Activity Log

### Custom Platform Security Advantages
- **Fine-grained access control** — custom RBAC tailored to governance roles
- **Tenant isolation** — custom platform enforces strict tenant boundaries
- **Custom audit trail** — tamper-evident audit log with full filtering
- **Minimal permissions** — uses only the specific Graph/ARM API permissions needed

---

## 3. Cost Analysis

### Monthly Cost Comparison (4 tenants, ~50 billable Azure resources, 30 users)

#### Option A: Native Azure Tools Only
| Tool | Monthly Cost | Notes |
|------|-------------|-------|
| Azure Lighthouse | $0 | Free |
| Azure Cost Management | $0 | Free |
| Foundational CSPM | $0 | Free — Secure Score + basic compliance |
| Defender CSPM | $255 | $5.11 × 50 billable resources |
| Entra ID Governance | $840 | ~$7/user/mo × 30 users × 4 tenants |
| Log Analytics ingestion | $100 | ~5-10 GB/day across tenants |
| KQL Development (amortized) | $833 | ~100 hours × $100/hr ÷ 12 months |
| **Total** | **~$2,028/month** | |

#### Option B: Custom Platform (Current)
| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| App Service B2 | $55 | Current hosting plan |
| Azure SQL S0 | $15 | Database |
| Redis Cache C0 | $0 | Free tier |
| Key Vault | $5 | Secrets management |
| Storage Account | $2 | Backups |
| Dev maintenance (amortized) | $500 | ~6 hours/month × ~$83/hr |
| **Total** | **~$577/month** | |

#### Option C: Hybrid (Native for Azure resources + Custom for identity/DMARC)
| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Foundational CSPM | $0 | Free — replaces some compliance tracking |
| App Service B2 | $55 | Custom platform for identity + DMARC |
| Azure SQL S0 | $15 | Database |
| Dev maintenance (amortized) | $400 | Reduced scope |
| **Total** | **~$470/month** | |

### Cost Verdict
The custom platform is **~3.5× cheaper** than full native tools deployment, and native tools still leave identity governance, DMARC, and deadline tracking uncovered.

---

## 4. Implementation Complexity Analysis

### Native Tools: Implementation Effort
| Task | Effort | Expertise Required |
|------|--------|-------------------|
| Lighthouse delegation setup (4 tenants) | 4-8 hours | Azure RBAC, ARM templates |
| Defender CSPM configuration | 4-8 hours | Defender for Cloud, Azure Policy |
| Cost Management budget/alert setup | 2-4 hours | Cost Management basics |
| KQL workbook development (cross-tenant) | 80-120 hours | **Advanced KQL/Kusto** |
| Entra ID Governance setup (4 tenants) | 16-32 hours | Entra admin, PIM |
| Ongoing KQL maintenance | 4-8 hours/month | KQL expertise |
| **Total initial** | **~106-172 hours** | |

### Custom Platform: Already Built
| Component | Status | Notes |
|-----------|--------|-------|
| Lighthouse integration | ✅ Complete | `lighthouse_client.py` — 32.3 KB |
| Cost aggregation | ✅ Complete | `cost_service.py` + `chargeback_service.py` |
| Compliance monitoring | ✅ Complete | `compliance_service.py` + custom rules |
| Identity governance | ✅ Complete | `identity_service.py` + `graph_client.py` |
| DMARC monitoring | ✅ Complete | `dmarc_service.py` |
| Multi-brand UI | ✅ Complete | 5 branded themes |
| Regulatory deadlines | ✅ Complete | Riverside compliance module |

---

## 5. Stability & Maintenance Analysis

### Native Tools
- **Pro**: Microsoft manages all infrastructure, updates, and patches
- **Pro**: No custom code maintenance for Azure resource queries
- **Con**: Breaking changes in Azure Policy definitions, KQL syntax updates
- **Con**: Workbook queries require maintenance when Azure APIs change
- **Con**: Entra ID Governance features frequently change (preview → GA → deprecated)
- **Con**: Multi-tenant workbook development is niche — limited community resources

### Custom Platform
- **Pro**: Full control over feature changes and deprecation timeline
- **Pro**: Well-tested codebase (~170 unit test files)
- **Con**: Python dependency updates (FastAPI, Azure SDK, etc.)
- **Con**: Must track Azure API changes in custom integration code
- **Con**: Single developer dependency risk

---

## 6. Compatibility Analysis

### Native Tools + Current Platform
The custom platform already uses Azure Lighthouse via `LighthouseAzureClient`. Native tools can complement rather than replace:

- **Resource Graph**: Platform already uses ARM queries; could use Resource Graph for richer resource data
- **Foundational CSPM**: Free Secure Score data could supplement `compliance_service.py`
- **Defender Recommendations**: Could be surfaced in custom dashboard alongside custom compliance rules

### Integration Points
- Azure Cost Management API → already used via `CostManagementClient` in `lighthouse_client.py`
- Azure Resource Graph → could enhance `resource_service.py`
- Microsoft Graph API → already used via `graph_client.py` for identity governance
- Defender for Cloud API → could supplement compliance data

---

## 7. Optimization Analysis

### Best Use of Native Tools (Hybrid Strategy)
1. **USE** Foundational CSPM ($0) for Secure Score + basic compliance
2. **USE** Azure Resource Graph for cross-tenant resource queries
3. **USE** Azure Advisor for right-sizing recommendations
4. **USE** Lighthouse for delegation management
5. **KEEP** Custom platform for: cost aggregation, chargeback, identity governance, DMARC, regulatory deadlines, branded UX
6. **SKIP** Defender CSPM ($255/mo) — marginal value over Foundational
7. **SKIP** Entra ID Governance add-on ($840/mo) — doesn't solve cross-tenant problem
