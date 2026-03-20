# NIST Cybersecurity Framework (CSF) 2.0 — Raw Findings

**Source**: NIST.gov (official) + csf.tools (verbatim republication of NIST document)
**Primary Source**: https://www.nist.gov/cyberframework
**Document URL**: https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf
**Publication Date**: February 26, 2024
**CSF 1.1 Archive**: Still available at https://www.nist.gov/cyberframework (CSF 1.1 Archive section)
**Two-Year Anniversary**: February 24, 2026

---

## CSF 2.0 Functions — Complete Listing (All 6)

| # | Function ID | Function Name | Categories | Subcategories | New in 2.0? |
|---|------------|---------------|------------ |---------------|-------------|
| 1 | **GV** | Govern | 6 | 31 | ✅ NEW (replaces ID.GV, ID.BE from 1.1) |
| 2 | **ID** | Identify | 3 | 21 | Restructured |
| 3 | **PR** | Protect | 5 | 22 | Restructured |
| 4 | **DE** | Detect | 2 | 11 | Restructured |
| 5 | **RS** | Respond | 4 | 13 | Restructured |
| 6 | **RC** | Recover | 2 | 8 | Restructured |
| | **TOTAL** | | **22 categories** | **106 subcategories** | |

---

## GV: GOVERN — 6 Categories, 31 Subcategories

> *"The organization's cybersecurity risk management strategy, expectations, and policy are
> established, communicated, and monitored."*
> GOVERN is at the **center** of the CSF wheel — it informs all other functions.

| Category ID | Category Name | Subcategories |
|-------------|--------------|---------------|
| GV.OC | Organizational Context | 5 (GV.OC-01 to GV.OC-05) |
| GV.RM | Risk Management Strategy | 7 (GV.RM-01 to GV.RM-07) |
| GV.RR | Roles, Responsibilities, And Authorities | 4 (GV.RR-01 to GV.RR-04) |
| GV.PO | Policy | 2 (GV.PO-01, GV.PO-02) |
| GV.OV | Oversight | 3 (GV.OV-01 to GV.OV-03) |
| GV.SC | Cybersecurity Supply Chain Risk Management | 10 (GV.SC-01 to GV.SC-10) |
| **GV Total** | | **31** |

**GV.SC subcategory highlights (all 10 verified):**
- GV.SC-01 to GV.SC-10 covering: C-SCRM strategy, supplier roles, integration with ERM,
  supplier criticality, contractual requirements, due diligence, risk monitoring,
  incident planning, lifecycle management, post-relationship provisions.

---

## ID: IDENTIFY — 3 Categories, 21 Subcategories

> *"The organization's current cybersecurity risks are understood."*

| Category ID | Category Name | Subcategories |
|-------------|--------------|---------------|
| ID.AM | Asset Management | 7 (ID.AM-01–05, 07, 08)* |
| ID.RA | Risk Assessment | 10 (ID.RA-01 to ID.RA-10) |
| ID.IM | Improvement | 4 (ID.IM-01 to ID.IM-04) |
| **ID Total** | | **21** |

*Note: ID.AM-06 was removed between draft and final CSF 2.0 — numbering gap is intentional.
ID.IM is a new category in 2.0 (incorporates former DE.DP from 1.1).

---

## PR: PROTECT — 5 Categories, 22 Subcategories

> *"Safeguards to manage the organization's cybersecurity risks are used."*

| Category ID | Category Name | Subcategories |
|-------------|--------------|---------------|
| PR.AA | Identity Management, Authentication, And Access Control | 6 (PR.AA-01 to PR.AA-06) |
| PR.AT | Awareness And Training | 2 (PR.AT-01, PR.AT-02) |
| PR.DS | Data Security | 4 (PR.DS-01, 02, 10, 11)* |
| PR.PS | Platform Security | 6 (PR.PS-01 to PR.PS-06) |
| PR.IR | Technology Infrastructure Resilience | 4 (PR.IR-01 to PR.IR-04) |
| **PR Total** | | **22** |

*Note: PR.DS-01, 02, 10, 11 — large numbering gap indicates removed subcategories from draft.
PR.AA replaced PR.AC from CSF 1.1.
PR.PS is entirely new in 2.0 (Platform Security).
PR.IR is entirely new in 2.0 (Technology Infrastructure Resilience).

---

## DE: DETECT — 2 Categories, 11 Subcategories

> *"Possible cybersecurity attacks and compromises are found and analyzed."*

| Category ID | Category Name | Subcategories |
|-------------|--------------|---------------|
| DE.CM | Continuous Monitoring | 5 (DE.CM-01, 02, 03, 06, 09)* |
| DE.AE | Adverse Event Analysis | 6 (DE.AE-02, 03, 04, 06, 07, 08)* |
| **DE Total** | | **11** |

*Note: Gaps in numbering (DE.CM-04, 05, 07, 08 and DE.AE-01, 05 removed) reflect consolidation
from 1.1 which had 3 DETECT categories (DE.AE, DE.CM, DE.DP).

---

## RS: RESPOND — 4 Categories, 13 Subcategories

> *"Actions regarding a detected cybersecurity incident are taken."*

| Category ID | Category Name | Subcategories |
|-------------|--------------|---------------|
| RS.MA | Incident Management | 5 (RS.MA-01 to RS.MA-05) |
| RS.AN | Incident Analysis | 4 (RS.AN-03, 06, 07, 08)* |
| RS.CO | Incident Response Reporting And Communication | 2 (RS.CO-02, 03)* |
| RS.MI | Incident Mitigation | 2 (RS.MI-01, RS.MI-02) |
| **RS Total** | | **13** |

*Note: RS.MA is new in CSF 2.0 (replaces RS.RP from 1.1). Numbering gaps reflect consolidation.

---

## RC: RECOVER — 2 Categories, 8 Subcategories

> *"Assets and operations affected by a cybersecurity incident are restored."*

| Category ID | Category Name | Subcategories |
|-------------|--------------|---------------|
| RC.RP | Incident Recovery Plan Execution | 6 (RC.RP-01 to RC.RP-06) |
| RC.CO | Incident Recovery Communication | 2 (RC.CO-03, RC.CO-04)* |
| **RC Total** | | **8** |

*Note: RC.CO-01 and RC.CO-02 removed; remaining subcategories renumbered from 1.1.

---

## CSF 1.1 vs CSF 2.0 — Key Changes

### Structural Changes

| Dimension | CSF 1.1 (2018) | CSF 2.0 (Feb 26, 2024) |
|-----------|----------------|------------------------|
| Functions | 5 (ID, PR, DE, RS, RC) | **6** (+ GV: Govern) |
| Categories | 23 | 22 |
| Subcategories | 108 | 106 |
| Supply Chain | ID.SC (5 subcategories) | GV.SC (10 subcategories) — expanded |

### Functional Changes

**New in 2.0:**
1. **GV: GOVERN** — Brand new function, consolidates:
   - ID.GV: Governance (from Identify in 1.1)
   - ID.BE: Business Environment (from Identify in 1.1)
   - Adds new: GV.OC, GV.RM, GV.RR, GV.PO, GV.OV, GV.SC

2. **GV.SC: Cybersecurity Supply Chain Risk Management** — dramatically expanded from ID.SC (5
   subcategories in 1.1) to GV.SC (10 subcategories in 2.0)

3. **ID.IM: Improvement** — new category (incorporates continuous improvement from across functions)

4. **PR.PS: Platform Security** — new (covers hardware, firmware, OS, application security)

5. **PR.IR: Technology Infrastructure Resilience** — new (covers network security, resilience)

**Renamed/Restructured:**
- PR.AC → PR.AA (Identity Management, Authentication, and Access Control)
- DE.AE → DE.AE (kept same ID, renamed to Adverse Event Analysis)
- RS.RP → RS.MA (Incident Management — new name, expanded)

**Removed (absorbed into other categories):**
- ID.GV → GV (whole function)
- ID.BE → GV.OC
- DE.DP (Detection Processes) → absorbed into ID.IM and DE.AE

### CSF 1.1 Detect Categories (for comparison)
CSF 1.1 had 3 DETECT categories: DE.AE, DE.CM, DE.DP (Detection Processes)
CSF 2.0 consolidated to 2 DETECT categories: DE.CM, DE.AE

### Format Changes
- Implementation Examples now online (not in document)
- Community Profiles introduced
- Informative References now online-only (updated more frequently)
- Quick Start Guides added for specific use cases
- GOVERN depicted at center of the CSF "wheel" diagram

---

## Framework Versioning Approach (NIST)

- CSF 1.1 is archived but still accessible at nist.gov
- CSF 2.0 was released February 26, 2024
- NIST provides a Quick Start Guide for transitioning from 1.1 → 2.0
- Both versions maintained simultaneously during transition
- The NIST CSF website provides "CSF 1.1 Archive" section
- As of Feb 2026: csf.tools shows both v1.1 and v2.0 reference pages active
- No sunset date published for CSF 1.1 support
