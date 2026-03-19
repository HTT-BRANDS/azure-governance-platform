# Multi-Dimensional Analysis: SOC 2 TSC & NIST CSF 2.0 for Azure Governance Platform

**Agent**: web-puppy-d1a2ac | **Date**: March 2026

---

## 1. Security Analysis

### SOC 2 TSC — Security Posture
The TSC framework is **audit-centric**: it defines WHAT controls must exist (not HOW to implement them). For your Azure Governance Platform:

**High-Impact Controls for Azure Cloud:**
- **CC6.1–CC6.8** (Logical/Physical Access) — 100% coverage in Azure built-in policy. Maps directly to Entra ID, Defender, NSGs, WAF.
- **CC7.1–CC7.5** (System Operations) — Maps to Log Analytics, Sentinel, Defender for Cloud, incident response.
- **CC8.1** (Change Management) — Maps to Azure DevOps, CI/CD pipeline policies, ARM/Bicep deployment gates.
- **A1.1–A1.3** (Availability) — Maps to Azure Backup, Site Recovery, Monitor, Quota service.

**Security Gaps in Framework Coverage:**
- CC1–CC5 largely cover *organizational* controls (governance, risk culture) that are not automatable via Azure Policy → require manual evidence collection (policies, procedures, org charts)
- P1–P8 (Privacy) requires supplemental privacy impact assessments and consent frameworks

### NIST CSF 2.0 — Security Posture
CSF 2.0 is **risk-management-centric** and more prescriptive than TSC. The new GOVERN function explicitly addresses organizational strategy.

**Key Security Observations:**
- **PR.AA** family (Identity Mgmt + Auth + Access Control) is the most densely mapped in Azure built-ins — 8+ Azure policies map to PR.AA-01 and PR.AA-05
- **DE.CM** (Continuous Monitoring) has excellent Azure coverage — NSG flow logs, Defender for Cloud, container monitoring
- **RS.CO** (Response Communications) — alert notification policies are present (email alerts, Security Center contact) but incident communication workflows require orchestration
- **GV.SC** (Supply Chain Risk) — only GV.SC-07 is in Azure's built-in; third-party risk management requires supplemental process controls

---

## 2. Implementation Complexity Analysis

### Option A: Leverage Azure's Existing Built-In Initiatives
**Complexity**: LOW  
**Approach**: Use existing `SOC_2.json` and `NIST_CSF_v2.0.json` policy set definitions; parse `policyDefinitionGroups` to extract control mappings.

```python
# Your existing PolicyState model already captures group names:
# policy_definition_group_names → e.g., "SOC_2_CC6.1,SOC_2_CC6.6"

def extract_control_ids(group_names_csv: str) -> list[str]:
    """Parse Azure group names to control IDs."""
    groups = group_names_csv.split(",") if group_names_csv else []
    controls = []
    for g in groups:
        # "SOC_2_CC6.1" → "CC6.1"
        # "NIST_CSF_v2.0_PR.AA_01" → "PR.AA-01"
        if g.startswith("SOC_2_"):
            controls.append(g.replace("SOC_2_", ""))
        elif g.startswith("NIST_CSF_v2.0_"):
            raw = g.replace("NIST_CSF_v2.0_", "")
            controls.append(raw.replace("_", "-", 1))  # PR.AA_01 → PR.AA-01
    return controls
```

**Limitation**: Only covers controls that have Azure Policy mappings; organizational/governance controls (CC1-CC5, GV.RM, etc.) require separate tracking.

---

### Option B: Static Control Registry (Database-Driven)
**Complexity**: MEDIUM  
**Approach**: Store all controls from both frameworks in a database table; link PolicyState records to controls via the group name convention.

**Schema** (extending existing models):
```python
# New model: ComplianceControl
class ComplianceControl(Base):
    __tablename__ = "compliance_controls"
    
    id: Mapped[str] = Column(String(50), primary_key=True)     # "CC6.1", "PR.AA-01"
    framework: Mapped[str] = Column(String(20))                  # "SOC2", "NIST_CSF_2"
    category: Mapped[str] = Column(String(20))                   # "CC6", "PR.AA"
    category_name: Mapped[str] = Column(String(200))             # "Logical and Physical Access Controls"
    description: Mapped[str] = Column(Text)
    azure_group_name: Mapped[str | None] = Column(String(200))  # "SOC_2_CC6.1"
    cloud_relevance: Mapped[str] = Column(String(10))            # "HIGH", "MEDIUM", "LOW"
    automatable: Mapped[bool] = Column(Boolean, default=True)    # False for org controls
```

---

### Option C: Full Custom Framework Engine
**Complexity**: HIGH  
**Approach**: Build a configurable rule engine that maps Azure Policy categories to any compliance framework. Referenced in `adr-0005-custom-compliance-rules.md`.

**Already partially built**: The `CustomRuleService` and `compliance_rules` route suggest this direction is in progress.

---

## 3. Cost Analysis

### Azure Policy Costs
- Azure Policy regulatory compliance: **FREE** — no additional cost beyond existing Azure subscription
- `policyDefinitionGroups` data: Available via ARM API at no additional cost
- Compliance state queries: Included in Azure Resource Graph pricing (first 1M queries free/month)

### Implementation Costs (Development Time)
| Approach | Estimated Effort | Maintenance Burden |
|----------|-----------------|-------------------|
| Built-in Initiative Parsing | 2-3 days | Low (monitor Azure updates quarterly) |
| Static Control Registry | 5-8 days | Medium (update on framework revisions) |
| Full Custom Engine | 3-4 weeks | High (custom DSL, parser, UI) |

### Data Freshness Costs
- NIST CSF 2.0 next major revision: Unlikely before 2029-2030 (historical pattern)
- SOC 2 TSC next revision: 2025+ possible; AICPA revises approximately every 5-7 years
- Azure Policy initiative updates: Quarterly; monitor `Azure/azure-policy` GitHub releases

---

## 4. Stability Analysis

### Framework Stability
| Framework | Stability | Risk |
|-----------|-----------|------|
| SOC 2 TSC CC1-CC9 | ⭐⭐⭐⭐⭐ VERY STABLE | Control IDs unchanged since 2017; descriptions only refined |
| NIST CSF 2.0 | ⭐⭐⭐⭐⭐ STABLE | Just released Feb 2024; 5-7 year revision cycle |
| Azure Policy Group Names | ⭐⭐⭐⭐ STABLE | Breaking changes rare; Microsoft maintains backward compat |
| Azure Policy Definitions | ⭐⭐⭐ MODERATE | Individual policies added/deprecated; set definitions stable |

**Risk**: SOC 2 is an AICPA proprietary standard — Microsoft's mapping may lag AICPA revisions by 6-12 months. Always validate Azure's TSC mapping against AICPA's published criteria.

### Versioning Strategy
```python
# Track framework versions in your database
frameworks = [
    {"id": "SOC2", "version": "2017_rev2022", "azure_initiative": "SOC_2.json"},
    {"id": "NIST_CSF", "version": "2.0", "azure_initiative": "NIST_CSF_v2.0.json", 
     "azure_policy_set_id": "184a0e05-7b06-4a68-bbbe-13b8353bc613"}
]
```

---

## 5. Optimization Analysis

### Query Performance for Compliance-by-Control
Your current `PolicyState` model stores `policy_definition_group_names` as a CSV string in a single Text column. For control-based queries at scale:

**Current limitation**: 
```python
# This requires LIKE scan on text
policies = db.query(PolicyState).filter(
    PolicyState.policy_category.contains("CC6")
).all()
```

**Optimized approach** — separate control mapping table with proper indexing:
```sql
CREATE INDEX idx_policy_control_mapping ON policy_control_mappings (control_id);
CREATE INDEX idx_policy_control_mapping_policy ON policy_control_mappings (policy_definition_id);
```

**Caching strategy**: Compliance-by-control is cacheable for 15-60 minutes (same as existing `@cached("compliance_summary")` pattern).

---

## 6. Compatibility Analysis

### With Existing Codebase

| Existing Component | Compatibility with Framework Mapping | Notes |
|-------------------|-------------------------------------|-------|
| `PolicyState` model | ✅ HIGH — `policy_definition_group_names` already present | Parse this field to extract control IDs |
| `ComplianceService` | ✅ HIGH — add `get_compliance_by_control()` method | Extend existing pattern |
| `compliance.py` sync | ✅ HIGH — Azure API already returns group names | Populate mapping table at sync time |
| `custom_rule_service.py` | ✅ MEDIUM — extend to tag custom rules with control IDs | Optional enhancement |
| `/api/routes/compliance.py` | ✅ HIGH — add `/compliance/controls` endpoint | New route following existing pattern |
| Caching layer | ✅ HIGH — control compliance is cacheable | Add `@cached("compliance_by_control")` |

### With Azure Policy API
The Azure Policy Insights API returns `policyDefinitionGroupNames` as an array in each policy state. Your existing sync code already captures this:
```python
# In app/core/sync/compliance.py line ~100
if state.policy_definition_group_names:
    policy_category = ",".join(state.policy_definition_group_names)
```

⚠️ **Gap**: The sync code joins group names into `policy_category` as a single CSV string but doesn't normalize them into a structured mapping table. This is the key integration point.

---

## 7. Maintenance Analysis

### Long-Term Maintenance Strategy

**Low-maintenance path**: Use Azure's built-in initiative group names as the canonical control reference. When Azure updates their initiative (quarterly), your system automatically picks up new mappings via the next sync cycle.

**Medium-maintenance path**: Maintain a static control registry seeded from this research. Update when:
1. NIST releases CSF 3.0 (est. 2029+)
2. AICPA revises TSC (est. 2025-2027)
3. Azure adds new policy definitions to built-in initiatives

**Monitoring needed**:
```bash
# Monitor Azure policy releases
gh api repos/Azure/azure-policy/releases | jq '.[0:3]'

# Or watch the file directly
gh api repos/Azure/azure-policy/commits?path=built-in-policies/policySetDefinitions/Regulatory%20Compliance/SOC_2.json | jq '.[0]'
```

---

## 8. Framework Comparison Matrix

| Dimension | SOC 2 TSC | NIST CSF 2.0 |
|-----------|-----------|-------------|
| **Purpose** | Audit readiness, customer assurance | Risk management, security posture |
| **Audience** | SaaS/service org customers | Any organization |
| **Prescriptiveness** | Outcome-focused (WHAT) | More prescriptive (HOW + WHAT) |
| **Update Frequency** | ~5-7 years | ~5-7 years |
| **Azure Built-In** | ✅ SOC_2.json (mature) | ✅ NIST_CSF_v2.0.json v1.5.0 |
| **Cloud Focus** | Technology-agnostic, high-level | CSP-aware, operational |
| **Automatable Controls** | CC6-CC9, A1 (~50%) | PR, DE, partial RS/RC (~45%) |
| **Manual Controls** | CC1-CC5, P1-P8, C1 | GV, RS.MA, RS.AN |
| **Mapping Complexity** | Low (clear hierarchy) | Medium (subcategory notation) |
| **Customer Expectation** | Enterprise SaaS buyers | Government, regulated industries |
| **Sub-control granularity** | 9+4 categories, ~50 controls | 6 functions, 22 categories, ~100 subcategories |

---

## 9. Project-Specific Gap Analysis

Mapping existing `azure-governance-platform` capabilities to framework controls:

| Platform Capability | SOC 2 Controls Addressed | NIST CSF Controls Addressed |
|--------------------|--------------------------|------------------------------|
| Azure Policy sync | CC7.1, CC7.2 | DE.CM, DE.CM-09, ID.RA-01 |
| Secure Score tracking | CC7.1, CC6.1 | DE.CM, GV.SC-07 |
| MFA checks (preflight) | CC6.1, CC6.2 | PR.AA-01 |
| Identity/access monitoring | CC6.3, CC6.2 | PR.AA-01, PR.AA-05 |
| Budget/cost monitoring | (None direct) | (None direct) |
| Resource lifecycle tracking | CC8.1, A1.1 | PR.PS-02, ID.AM-01 |
| Audit log service | CC7.2, CC7.3 | DE.AE-03, DE.AE-06 |
| Compliance snapshot trends | CC4.1, CC4.2 | GV.OV |
| Access reviews | CC6.3 | PR.AA-05 |
| DMARC monitoring | CC6.6, CC7.2 | DE.CM-03 |
| Riverside requirements | CC3.x, CC9.2 | GV.SC-07, ID.RA |
| Notification/alerts | CC7.4, A1.1 | RS.CO-02, RS.CO-03 |

**Currently UNMAPPED by platform** (needs new features):
- CC8.1 (Change Management) — no CI/CD policy tracking
- A1.2, A1.3 (Backup compliance) — no backup status checks
- GV.OC-04 (Organizational context) — organizational governance metadata
- RC.RP-04 (Backup integrity verification) — no backup testing tracking
