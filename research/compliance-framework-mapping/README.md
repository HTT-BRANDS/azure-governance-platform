# Compliance Framework Mapping Research
## Executive Summary — ADR Reference

**Researcher**: web-puppy-c8ef40
**Research Date**: June 2025
**Purpose**: Architecture Decision Record — Regulatory Framework Mapping in Compliance SaaS
**Primary Sources**: AICPA (SOC 2), NIST (CSF), Prowler OSS, Chef InSpec, AWS/Azure vendor docs

---

## 🎯 Bottom Line Up Front (for ADR)

| Question | Answer |
|----------|--------|
| How many SOC 2 CC controls? | **33** (CC1.1–CC9.2 across 9 series) |
| How many SOC 2 A controls? | **3** (A1.1–A1.3) |
| SOC 2 current version year? | **2017** (Revised Points of Focus 2022; re-published Sep 30, 2023) |
| How many NIST CSF 2.0 functions? | **6** (added GOVERN in 2.0; was 5 in 1.1) |
| NIST CSF 2.0 total subcategories? | **106** across 22 categories |
| Best format for compliance data? | **YAML (source of truth) + DB (runtime)** |
| Tag-based vs category-based? | **Tag-based is dominant industry standard** |
| Multiple framework versions? | **Yes — coexistence is normal** (Prowler, AWS Security Hub all do it) |

---

## 1. SOC 2 Trust Services Criteria (TSC) — 2017 Version

### Current Version
- **Official name**: "2017 Trust Services Criteria (With Revised Points of Focus – 2022)"
- **Published**: September 30, 2023 (AICPA PDF, 554.3 KB)
- **Source**: https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022
- **Note**: The "2017" refers to the criteria version year, not publication year. There is **no separate "2023 TSC"** — the 2022 Revised Points of Focus update is part of the 2017 TSC document.

### Common Criteria (CC) Series — 33 Controls Total

| Series | Section Name | Controls | IDs |
|--------|-------------|---------|-----|
| CC1.x | Control Environment | 5 | CC1.1–CC1.5 |
| CC2.x | Communication and Information | 3 | CC2.1–CC2.3 |
| CC3.x | Risk Assessment | 4 | CC3.1–CC3.4 |
| CC4.x | Monitoring Activities | 2 | CC4.1–CC4.2 |
| CC5.x | Control Activities | 3 | CC5.1–CC5.3 |
| CC6.x | **Logical and Physical Access Controls** | **8** | CC6.1–CC6.8 |
| CC7.x | System Operations | 5 | CC7.1–CC7.5 |
| CC8.x | Change Management | 1 | CC8.1 |
| CC9.x | Risk Mitigation | 2 | CC9.1–CC9.2 |
| **TOTAL** | | **33** | |

### Availability (A) Series — 3 Controls

| ID | Description |
|----|-------------|
| A1.1 | Capacity planning and monitoring |
| A1.2 | Environmental protections, backups, recovery infrastructure |
| A1.3 | Recovery plan testing |

### Other Optional Series (for expanded TSC scope)
- **Confidentiality**: C1.1, C1.2 (2 controls)
- **Processing Integrity**: PI1.1–PI1.5 (5 controls)
- **Privacy**: P1.x–P8.x (8+ controls)

> 📌 **ADR Note**: CC series is mandatory for any SOC 2 (Security category). A/C/PI/P
> series are optional additional categories — design schema to support per-client scope.

---

## 2. NIST Cybersecurity Framework 2.0

### Key Facts
- **Published**: February 26, 2024 (NIST CSWP 29)
- **Previous version**: CSF 1.1 (April 16, 2018)
- **Download**: https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf

### 6 Functions (vs 5 in CSF 1.1)

| # | ID | Function | Categories | Subcategories | New in 2.0? |
|---|----|----------|-----------|---------------|-------------|
| 1 | **GV** | **Govern** | 6 | **31** | ✅ **NEW** |
| 2 | ID | Identify | 3 | 21 | Restructured |
| 3 | PR | Protect | 5 | 22 | Restructured |
| 4 | DE | Detect | 2 | 11 | Restructured |
| 5 | RS | Respond | 4 | 13 | Restructured |
| 6 | RC | Recover | 2 | 8 | Restructured |
| | **Total** | | **22** | **106** | |

### GV (Govern) Categories — NEW in 2.0
`GV.OC` (Org Context, 5 subcats) | `GV.RM` (Risk Mgmt, 7) | `GV.RR` (Roles, 4) |
`GV.PO` (Policy, 2) | `GV.OV` (Oversight, 3) | `GV.SC` (Supply Chain, 10)

### Key Changes from CSF 1.1 → 2.0

| Dimension | CSF 1.1 | CSF 2.0 |
|-----------|---------|---------|
| Functions | 5 | **6 (+GV)** |
| Categories | 23 | 22 |
| Subcategories | 108 | **106** |
| Supply chain controls | 5 (ID.SC) | **10 (GV.SC)** — doubled |
| Governance | Mixed into ID.GV, ID.BE | **Dedicated GV function** |
| Platform security | Scattered | **PR.PS** (new category) |
| Tech infrastructure resilience | Scattered | **PR.IR** (new category) |
| Improvement | DE.DP | **ID.IM** (moved to Identify) |

> 📌 **ADR Note**: If storing CSF subcategory IDs, be aware that CSF 2.0 has **numbering
> gaps** (e.g., PR.DS-01, 02, 10, 11 — gaps indicate removed subcategories between draft
> and final). Do not assume sequential numbering.

---

## 3. Compliance-as-Code Format Best Practices

### What Industry Tools Use

| Tool | Primary Format | Multi-Framework Pattern |
|------|---------------|------------------------|
| **Chef InSpec** | YAML (metadata) + Ruby DSL (controls) | Tags: `tag soc2: ['CC6.1']` |
| **OpenSCAP** | XML (XCCDF + OVAL) | Profile elements per standard |
| **Regula (OPA)** | Rego language + JSON metadata | `"controls": {"SOC2": ["CC6.1"]}` |
| **Prowler** | JSON (one file per framework) | Checks array per control |
| **AWS Security Hub** | ASFF (JSON) | `RelatedRequirements[]` array |
| **Azure MDC** | JSON (Policy definitions) | Initiative = standard |

### Industry Consensus: YAML-Seeded Database

```
[YAML files in Git]  →  [DB Migration/Seed]  →  [Application queries DB]
  (source of truth)       (deploy-time)           (runtime)
      ↓
  [Git audit trail]
  [PR review process]
  [Change history]
```

**Why YAML as source of truth**:
1. ✅ Human-readable (auditors can review without tooling)
2. ✅ Git-diff friendly (changes visible in PRs)
3. ✅ Supports comments (document mapping rationale)
4. ✅ No database dependency for the definitions themselves
5. ✅ Universal (language-agnostic, works with any tech stack)

**Why NOT hardcoded in application code**:
- ❌ Requires code deploy to update a mapping
- ❌ Mixes compliance data with business logic
- ❌ Cannot easily be reviewed by non-engineers (auditors)
- ❌ No separate version history for compliance data vs application code

---

## 4. Tag-Based vs Category-Based Multi-Framework Mapping

### Tag-Based (Control-Centric) — DOMINANT PATTERN

One security check → array of compliance tags for multiple frameworks.

```yaml
check_id: s3_bucket_encryption
compliance_tags:
  SOC2_2017:      [CC6.1, CC6.7]
  NIST_CSF_2.0:   [PR.DS-01]
  NIST_800_53_R5: [SC-28]
  PCI_DSS_4.0:    [3.5]
```

**Used by**: Prowler, Chef InSpec, Regula, AWS Security Hub (Consolidated Findings)

**Advantages**:
- One finding per check (no duplicates)
- Adding a new framework = add tag to existing checks
- Easy gap analysis ("which checks don't cover GV.SC-05?")
- Maps to AWS Security Hub's "consolidated control findings" architecture

### Category-Based (Standard-Centric) — LEGACY / ENTERPRISE

Each standard has its own set of controls; same check appears multiple times.

**Used by**: Azure MDC (historically), OpenSCAP profiles, some GRC platforms

**Disadvantages**:
- Duplicate findings (same issue, N findings for N standards)
- Adding a new framework = audit and re-map all controls
- Harder to see cross-framework coverage gaps

> 📌 **ADR Decision**: Use tag-based mapping. It is the architecture used by AWS Security Hub,
> Prowler (13k stars), Chef InSpec, and Regula. The pattern scales to any number of frameworks
> without creating duplicate findings.

---

## 5. Framework Versioning

### Do Organizations Support Multiple Versions Simultaneously?

**Yes — universally.** Evidence:
- **Prowler**: `cis_1.4_aws.json` AND `cis_1.5_aws.json` both active simultaneously
- **AWS Security Hub**: CIS v1.2.0 and CIS v1.4.0 both supported
- **Azure MDC**: Multiple PCI DSS, ISO 27001 versions active simultaneously

### Why Multi-Version is Required

1. **Audit cycles**: Organizations mid-SOC 2 audit cannot change framework version mid-year
2. **Customer requirements**: Different customers contractually specify different versions
3. **Transition periods**: Enterprise framework adoption takes 12-24 months
4. **Historical findings**: Old findings must reference the version in use at that time

### Version Naming Convention (Industry Standard)

```
✅ NIST_CSF_1.1     # version embedded in ID
✅ NIST_CSF_2.0     # separate record for new version
✅ SOC2_2017        # year in ID
✅ NIST_800_53_R5   # revision in ID

❌ NIST_CSF         # ambiguous — which version?
❌ SOC2             # ambiguous — 2017? 2022 revision?
```

### Framework Lifecycle Schema

```yaml
framework:
  id: NIST_CSF_1.1
  name: "NIST Cybersecurity Framework"
  version: "1.1"
  published_at: "2018-04-16"
  deprecated_at: null          # null = still active
  superseded_by: "NIST_CSF_2.0"
  source_url: "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.04162018.pdf"
```

---

## Research File Index

| File | Contents |
|------|---------|
| `README.md` | ← You are here — executive summary |
| `sources.md` | All sources with credibility tiers and validation |
| `analysis.md` | Security, cost, complexity, stability, maintenance analysis |
| `recommendations.md` | 9 prioritized ADR recommendations with rationale |
| `raw-findings/soc2-tsc-controls.md` | Complete SOC 2 CC and A control list |
| `raw-findings/nist-csf-2-0.md` | NIST CSF 2.0 complete function/category/subcategory breakdown |
| `raw-findings/compliance-as-code-formats.md` | InSpec, OpenSCAP, Regula, Prowler, AWS, Azure formats |
| `raw-findings/multi-framework-mapping.md` | Tag-based vs category-based pattern analysis |

---

## Source Authority Summary

| Source | Authority | Tier | Used For |
|--------|-----------|------|---------|
| AICPA (aicpa-cima.com) | Standards body | 1 | SOC 2 TSC official |
| NIST (nist.gov/nvlpubs) | Federal agency | 1 | CSF 2.0 official |
| csf.tools | Reference republication | 2 | CSF verification, 1.1 vs 2.0 |
| Prowler (GitHub) | OSS tool, 13.4k stars | 2 | Compliance-as-code pattern |
| Chef InSpec Docs | Vendor official | 2 | InSpec YAML+Ruby pattern |
| Microsoft Learn | Vendor official | 2 | Azure multi-framework approach |
| AWS Docs (inferred) | Vendor official | 2 | AWS Security Hub ASFF pattern |
