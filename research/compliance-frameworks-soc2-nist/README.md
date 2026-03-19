# Compliance Frameworks Research: SOC 2 TSC & NIST CSF 2.0

**Research Agent**: web-puppy-d1a2ac  
**Date**: March 2026  
**Purpose**: Authoritative control reference for building regulatory framework mapping feature in Azure Governance Platform  
**Project Context**: FastAPI/Python platform with existing `ComplianceService`, `PolicyState` model, and Azure Policy sync pipeline

---

## Executive Summary

This research provides **production-ready control reference data** for two frameworks:

1. **SOC 2 Trust Services Criteria (AICPA 2017, revised 2022)** — 9 Common Criteria categories (CC1–CC9) + 4 additional criteria sets (A1, C1, PI1, P1–P8)
2. **NIST Cybersecurity Framework 2.0** (published February 26, 2024) — 6 functions (GV, ID, PR, DE, RS, RC) with ~100 total subcategories

**Key Finding**: Azure has a **native built-in policy initiative for BOTH frameworks** (`SOC_2.json` v1.0+, `NIST_CSF_v2.0.json` v1.5.0) confirmed live in the `Azure/azure-policy` GitHub repo as of March 2026. Your platform can leverage Azure's `policyDefinitionGroups` naming convention to map existing `PolicyState` records directly to compliance controls — no external API needed.

---

## Quick Reference: All Control IDs

### SOC 2 TSC — Common Criteria

| Category | Controls | Full Name |
|----------|----------|-----------|
| **CC1** | CC1.1–CC1.5 | Control Environment |
| **CC2** | CC2.1–CC2.3 | Communication and Information |
| **CC3** | CC3.1–CC3.4 | Risk Assessment |
| **CC4** | CC4.1–CC4.2 | Monitoring Activities |
| **CC5** | CC5.1–CC5.3 | Control Activities |
| **CC6** ⭐ | CC6.1–CC6.8 | Logical and Physical Access Controls |
| **CC7** ⭐ | CC7.1–CC7.5 | System Operations |
| **CC8** ⭐ | CC8.1 | Change Management |
| **CC9** | CC9.1–CC9.2 | Risk Mitigation |

### SOC 2 TSC — Additional Criteria

| Category | Controls | Applies When |
|----------|----------|--------------|
| **A1** ⭐ | A1.1–A1.3 | Availability trust service category selected |
| **C1** | C1.1–C1.2 | Confidentiality trust service category selected |
| **PI1** | PI1.1–PI1.5 | Processing Integrity trust service category selected |
| **P1–P8** | P1.1–P8.1 | Privacy trust service category selected |

### NIST CSF 2.0 — All Functions & Categories

| Function | Code | Categories |
|----------|------|-----------|
| **Govern** | GV | GV.OC, GV.RM, GV.RR, GV.PO, GV.OV, **GV.SC** |
| **Identify** | ID | **ID.AM**, **ID.RA**, ID.IM |
| **Protect** | PR | **PR.AA**, PR.AT, **PR.DS**, **PR.PS**, PR.IR |
| **Detect** | DE | **DE.CM**, **DE.AE** |
| **Respond** | RS | RS.MA, RS.AN, **RS.CO**, RS.MI |
| **Recover** | RC | **RC.RP**, RC.CO |

*(Bold = categories with Azure Policy built-in subcategory mappings)*

---

## CC6 — Logical and Physical Access Controls (8 Controls)

| ID | Short Description | Azure Relevance |
|----|-------------------|----------------|
| **CC6.1** | Logical access security software, infrastructure, architectures | MFA, Azure AD Conditional Access, Entra ID |
| **CC6.2** | Register/authorize new users before issuing credentials | User provisioning, Azure AD, identity lifecycle |
| **CC6.3** | Authorize/modify/remove access per documented rules | RBAC, access reviews, JIT access, PIM |
| **CC6.4** | Restrict physical access to facilities and assets | Data center physical security (Microsoft responsibility) |
| **CC6.5** | Discontinue protections only after data recovery capability diminished | Media disposal, decommissioning, Key Vault key destruction |
| **CC6.6** | Protect against threats from outside system boundaries | NSGs, Azure Firewall, WAF, DDoS Protection |
| **CC6.7** | Restrict/protect transmission and movement of information | TLS, private endpoints, encryption in transit, VPN |
| **CC6.8** | Prevent/detect unauthorized or malicious software | Defender for Cloud, antimalware, container security |

---

## CC7 — System Operations (5 Controls)

| ID | Short Description | Azure Relevance |
|----|-------------------|----------------|
| **CC7.1** | Detect config changes introducing vulnerabilities; monitor for new CVEs | Defender for Cloud, Secure Score, Azure Policy |
| **CC7.2** | Monitor for anomalies indicative of malicious acts | Log Analytics, Azure Monitor, Sentinel, SIEM |
| **CC7.3** | Evaluate events to determine if security incidents occurred | Incident triage, alert classification, SOC |
| **CC7.4** | Execute incident response program to understand/contain/remediate | IRP execution, playbooks, runbooks |
| **CC7.5** | Identify/develop/implement recovery activities from incidents | Post-incident recovery, PIR, system restoration |

---

## CC8 — Change Management (1 Control)

| ID | Short Description | Azure Relevance |
|----|-------------------|----------------|
| **CC8.1** | Authorize/design/develop/test/approve/implement changes | CI/CD pipelines, Azure DevOps, ARM/Bicep templates, change approval gates |

---

## A1 — Availability (3 Controls)

| ID | Short Description | Azure Relevance |
|----|-------------------|----------------|
| **A1.1** | Maintain/monitor/evaluate processing capacity | Azure Monitor, capacity alerts, auto-scaling, Quota monitoring |
| **A1.2** | Backup processes and recovery infrastructure to meet RTO/RPO | Azure Backup, Site Recovery, geo-redundant storage, BCDR |
| **A1.3** | Test recovery plan procedures | DR drills, backup restoration tests, runbook validation |

---

## NIST CSF 2.0 — Key Subcategories for Azure Cloud Governance

### PR.AA (Identity Management, Authentication, and Access Control)
| Subcategory | Description |
|-------------|-------------|
| **PR.AA-01** | Identities and credentials for authorized users, services, and hardware are managed by the organization |
| **PR.AA-05** | Access permissions, entitlements, and authorizations are defined in a policy, managed, enforced, and reviewed, incorporating least privilege and separation of duties |

### DE.CM (Continuous Monitoring)
| Subcategory | Description |
|-------------|-------------|
| **DE.CM-03** | Personnel activity and technology usage are monitored to find potentially adverse events |
| **DE.CM-09** | Computing hardware and software, runtime environments, and their data are monitored to find potentially adverse events |

### RS.CO (Response Communications)
| Subcategory | Description |
|-------------|-------------|
| **RS.CO-02** | Internal and external stakeholders are notified of incidents in a timely manner |
| **RS.CO-03** | Information is shared with designated internal and external stakeholders as established in the incident response plan |

### ID.AM (Asset Management)
| Subcategory | Description |
|-------------|-------------|
| **ID.AM-01** | Inventories of hardware managed by the organization are maintained |

---

## Key Technical Findings

### 1. Azure Group Name Convention (Critical for Implementation)
Azure Policy group names use the pattern: `{FRAMEWORK}_{CONTROL_ID}`:
- SOC 2: `SOC_2_CC6.1`, `SOC_2_CC7.2`, `SOC_2_A1.1`
- NIST CSF: `NIST_CSF_v2.0_PR.AA_01`, `NIST_CSF_v2.0_DE.CM_09`

Your `PolicyState.policy_definition_group_names` field already captures these strings from Azure's API.

### 2. N:M Mapping (Policies to Controls)
A single policy maps to multiple controls. Example:
- "MFA required for subscription owners" → CC6.1, CC6.3, PR.AA, PR.AA-01

### 3. Azure NIST CSF 2.0 Initiative Groups (Confirmed March 2026)
From `NIST_CSF_v2.0.json` v1.5.0:
```
GV.OC_04, GV.SC_07
ID.AM_01, ID.RA_01, ID.RA_07
PR.AA, PR.AA_01, PR.AA_05
PR.DS, PR.DS_01, PR.DS_02
PR.PS_02, PR.PS_04, PR.PS_05
DE.CM, DE.CM_03, DE.CM_09
DE.AE, DE.AE_03, DE.AE_06
RS.CO_02, RS.CO_03
RC.RP, RC.RP_04
```

### 4. Coverage Gaps to Address
Azure's built-in initiatives don't cover:
- RS.MA, RS.AN, RS.MI (respond categories) — these require manual or Sentinel-based mapping
- GV.RM, GV.RR, GV.PO, GV.OV — these are policy/process controls requiring manual evidence
- SOC 2 P1–P8 Privacy — requires supplemental data privacy controls
- CC1–CC5 (some) — organizational/governance controls not automatable via Azure Policy

---

## Directory Structure

```
research/compliance-frameworks-soc2-nist/
├── README.md                           ← This file (executive summary)
├── sources.md                          ← All sources with credibility assessments
├── analysis.md                         ← Multi-dimensional framework analysis
├── recommendations.md                  ← Project-specific implementation recommendations
└── raw-findings/
    ├── soc2-tsc-controls.md            ← Complete SOC 2 control reference (all CC1-CC9, A1, C1, PI1, P1-P8)
    ├── nist-csf-2-0-controls.md        ← Complete NIST CSF 2.0 reference (all 6 functions, ~100 subcategories)
    └── azure-policy-mapping-approaches.md ← Mapping patterns, SQL schema, KQL examples
```
