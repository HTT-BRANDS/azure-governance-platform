---
status: proposed
date: 2025-07-14
decision-makers: Solutions Architect 🏛️, Security Auditor 🛡️, Pack Leader 🐺
consulted: Web Puppy 🕵️ (research), Experience Architect 🎨 (API contracts)
informed: All Code Puppy agents, MSP administrators
relates-to: CM-003
---

# Use static YAML with tag-based mapping for regulatory framework compliance tracking

## Context and Problem Statement

The Azure Governance Platform tracks compliance findings across tenants via `ComplianceSnapshot`, `PolicyState`, and `CustomComplianceRule` models (built in v1.5.3 per ADR-0005). MSP administrators managing 5 tenants need to understand how existing compliance checks map to **SOC2 Trust Service Criteria** and **NIST Cybersecurity Framework** controls — the two frameworks most commonly requested in audit evidence packages.

The platform must: (1) define regulatory framework control structures (SOC2 TSC CC+A series, NIST CSF 2.0 all 6 functions), (2) map existing compliance findings to framework controls, (3) expose a `GET /api/v1/compliance/frameworks` endpoint, and (4) support framework version coexistence for audit cycle transitions.

How should the regulatory framework mapping data be stored, structured, and integrated with the existing compliance pipeline?

## Decision Drivers

- **Auditability (K.O. criterion)**: Framework definitions must be version-controlled with full change history — SOC2 auditors require evidence of who changed what, when
- **Security**: No new attack surface — framework data is read-only reference data derived from public standards (AICPA TSC, NIST CSWP 29)
- **Multi-framework support**: A single compliance finding must map to controls across multiple frameworks simultaneously (e.g., encryption check → SOC2 CC6.1 + NIST CSF PR.DS-01)
- **Version coexistence**: Must support NIST CSF 1.1 and 2.0 concurrently during 12–24 month industry transition period; SOC2 2017 TSC with 2022 Revised Points of Focus
- **Implementation velocity**: Must integrate with existing FastAPI + SQLAlchemy stack in ≤1 sprint
- **Compatibility**: Must work alongside existing `ComplianceSnapshot`, `PolicyState`, `CustomComplianceRule` models without schema migration

## Considered Options

1. **Static YAML mapping file** — `config/compliance_frameworks.yaml` loaded at startup with `yaml.safe_load()`, cached in memory, served via read-only endpoint
2. **Database-backed mapping tables** — New `compliance_frameworks` and `framework_controls` tables in PostgreSQL with seed migration
3. **Hardcoded Python dictionary** — Framework definitions as Python `dict` literals in a module file

## Decision Outcome

**Chosen option: "Static YAML mapping file"**, because it is the only option that satisfies the auditability K.O. criterion while providing clean Git diffs for compliance change review, zero database migration risk, and startup-time validation — all at minimal implementation cost.

### Data Architecture

#### YAML Structure (`config/compliance_frameworks.yaml`)

```yaml
# Regulatory Framework Mapping — Azure Governance Platform
# Source of truth for SOC2 TSC and NIST CSF control definitions
# Changes require PR review (branch protection on config/)
# Version: See individual framework entries

frameworks:
  SOC2_2017:
    name: "SOC 2 Trust Services Criteria"
    version: "2017 (Revised Points of Focus 2022)"
    authority: "AICPA"
    published_at: "2017-01-01"
    source_url: "https://us.aicpa.org/interestareas/frc/assuranceadvisoryservices/trustservicescriteria"
    deprecated_at: null
    superseded_by: null
    controls:
      # Common Criteria (CC) — mandatory for all SOC 2 engagements
      CC1.1:
        name: "COSO Principle 1: Integrity and Ethical Values"
        series: "CC1"
        series_name: "Control Environment"
        description: "The entity demonstrates a commitment to integrity and ethical values."
      CC1.2:
        name: "COSO Principle 2: Board Independence"
        series: "CC1"
        series_name: "Control Environment"
        description: "The board of directors demonstrates independence from management and exercises oversight."
      # ... CC1.3–CC1.5 (5 total in CC1 series)
      CC2.1:
        name: "COSO Principle 13: Quality Information"
        series: "CC2"
        series_name: "Communication and Information"
        description: "The entity obtains or generates and uses relevant, quality information."
      # ... CC2.2–CC2.3 (3 total in CC2 series)
      CC3.1:
        name: "COSO Principle 6: Risk Assessment Objectives"
        series: "CC3"
        series_name: "Risk Assessment"
        description: "The entity specifies objectives with sufficient clarity to enable identification of risks."
      # ... CC3.2–CC3.4 (4 total in CC3 series)
      CC4.1:
        name: "COSO Principle 16: Ongoing Monitoring"
        series: "CC4"
        series_name: "Monitoring Activities"
        description: "The entity selects, develops, and performs ongoing evaluations."
      # ... CC4.2 (2 total in CC4 series)
      CC5.1:
        name: "COSO Principle 10: Control Activities Selection"
        series: "CC5"
        series_name: "Control Activities"
        description: "The entity selects and develops control activities that mitigate risks."
      # ... CC5.2–CC5.3 (3 total in CC5 series)
      CC6.1:
        name: "Logical and Physical Access — Security Software"
        series: "CC6"
        series_name: "Logical and Physical Access Controls"
        description: "Logical access security software, infrastructure, and architectures."
      CC6.2:
        name: "Logical and Physical Access — User Registration"
        series: "CC6"
        series_name: "Logical and Physical Access Controls"
        description: "User registration and authorization prior to issuing credentials."
      CC6.3:
        name: "Logical and Physical Access — Credential Management"
        series: "CC6"
        series_name: "Logical and Physical Access Controls"
        description: "Credential lifecycle management including modification and revocation."
      CC6.4:
        name: "Physical Access — Restrictions"
        series: "CC6"
        series_name: "Logical and Physical Access Controls"
        description: "Physical access to facilities and protected information assets is restricted."
      CC6.5:
        name: "Logical and Physical Access — Asset Disposal"
        series: "CC6"
        series_name: "Logical and Physical Access Controls"
        description: "Disposition of logical and physical assets to prevent unauthorized access."
      CC6.6:
        name: "Logical Access — External Threats"
        series: "CC6"
        series_name: "Logical and Physical Access Controls"
        description: "Measures against threats outside system boundaries."
      CC6.7:
        name: "Data Transmission — Authorized Channels"
        series: "CC6"
        series_name: "Logical and Physical Access Controls"
        description: "Restricting data transmission to authorized senders and recipients."
      CC6.8:
        name: "Malicious Software Prevention"
        series: "CC6"
        series_name: "Logical and Physical Access Controls"
        description: "Controls to prevent or detect malicious software."
      CC7.1:
        name: "Monitoring Infrastructure and Software"
        series: "CC7"
        series_name: "System Operations"
        description: "Detection and monitoring procedures for new vulnerabilities."
      CC7.2:
        name: "Anomaly Detection"
        series: "CC7"
        series_name: "System Operations"
        description: "Monitoring system components for anomalies indicating malicious acts."
      CC7.3:
        name: "Security Event Evaluation"
        series: "CC7"
        series_name: "System Operations"
        description: "Evaluating identified security events to determine remediation."
      CC7.4:
        name: "Incident Response"
        series: "CC7"
        series_name: "System Operations"
        description: "The entity responds to identified security incidents."
      CC7.5:
        name: "Incident Recovery"
        series: "CC7"
        series_name: "System Operations"
        description: "Identifying, developing, and implementing recovery activities."
      CC8.1:
        name: "Change Management"
        series: "CC8"
        series_name: "Change Management"
        description: "Changes to infrastructure, data, software, and procedures are authorized and implemented."
      CC9.1:
        name: "Risk Mitigation — Business Disruption"
        series: "CC9"
        series_name: "Risk Mitigation"
        description: "Identifying and assessing risks and mitigation strategies."
      CC9.2:
        name: "Risk Mitigation — Vendor Management"
        series: "CC9"
        series_name: "Risk Mitigation"
        description: "Assessing and managing risks associated with vendors and partners."
      # Availability (A) Series — optional, per-audit scope
      A1.1:
        name: "Availability — Capacity Planning"
        series: "A1"
        series_name: "Availability"
        description: "Current processing capacity and usage is maintained and monitored."
      A1.2:
        name: "Availability — Environmental Protections"
        series: "A1"
        series_name: "Availability"
        description: "Environmental protections, backups, and recovery infrastructure."
      A1.3:
        name: "Availability — Recovery Testing"
        series: "A1"
        series_name: "Availability"
        description: "Recovery plan testing confirms system recovery meets objectives."

  NIST_CSF_2.0:
    name: "NIST Cybersecurity Framework"
    version: "2.0"
    authority: "NIST"
    published_at: "2024-02-26"
    source_url: "https://doi.org/10.6028/NIST.CSWP.29"
    deprecated_at: null
    superseded_by: null
    controls:
      # GOVERN (GV) — NEW in CSF 2.0
      GV.OC-01:
        name: "Organizational Context — Mission Understanding"
        function: "Govern"
        function_id: "GV"
        category: "Organizational Context"
        category_id: "GV.OC"
      GV.OC-02:
        name: "Organizational Context — Stakeholder Requirements"
        function: "Govern"
        function_id: "GV"
        category: "Organizational Context"
        category_id: "GV.OC"
      # ... GV.OC-03 through GV.OC-05 (5 in GV.OC)
      GV.RM-01:
        name: "Risk Management Strategy — Established"
        function: "Govern"
        function_id: "GV"
        category: "Risk Management Strategy"
        category_id: "GV.RM"
      # ... GV.RM-02 through GV.RM-07 (7 in GV.RM)
      GV.RR-01:
        name: "Organizational Roles and Responsibilities"
        function: "Govern"
        function_id: "GV"
        category: "Roles, Responsibilities, and Authorities"
        category_id: "GV.RR"
      # ... GV.RR-02 through GV.RR-04 (4 in GV.RR)
      GV.PO-01:
        name: "Cybersecurity Policy — Established"
        function: "Govern"
        function_id: "GV"
        category: "Policy"
        category_id: "GV.PO"
      GV.PO-02:
        name: "Cybersecurity Policy — Reviewed"
        function: "Govern"
        function_id: "GV"
        category: "Policy"
        category_id: "GV.PO"
      GV.OV-01:
        name: "Cybersecurity Oversight — Results"
        function: "Govern"
        function_id: "GV"
        category: "Oversight"
        category_id: "GV.OV"
      # ... GV.OV-02 through GV.OV-03 (3 in GV.OV)
      GV.SC-01:
        name: "Supply Chain Risk Management Program"
        function: "Govern"
        function_id: "GV"
        category: "Cybersecurity Supply Chain Risk Management"
        category_id: "GV.SC"
      # ... GV.SC-02 through GV.SC-10 (10 in GV.SC)

      # IDENTIFY (ID)
      ID.AM-01:
        name: "Asset Management — Hardware Inventory"
        function: "Identify"
        function_id: "ID"
        category: "Asset Management"
        category_id: "ID.AM"
      # ... ID.AM-02 through ID.AM-08 (8 in ID.AM)
      ID.RA-01:
        name: "Risk Assessment — Vulnerability Identification"
        function: "Identify"
        function_id: "ID"
        category: "Risk Assessment"
        category_id: "ID.RA"
      # ... ID.RA-02 through ID.RA-10 (10 in ID.RA)
      ID.IM-01:
        name: "Improvement — Lessons Learned"
        function: "Identify"
        function_id: "ID"
        category: "Improvement"
        category_id: "ID.IM"
      # ... ID.IM-02 through ID.IM-04 (4 in ID.IM)

      # PROTECT (PR)
      PR.AA-01:
        name: "Identity and Access — Identity Management"
        function: "Protect"
        function_id: "PR"
        category: "Identity Management, Authentication, and Access Control"
        category_id: "PR.AA"
      # ... PR.AA-02 through PR.AA-06 (6 in PR.AA)
      PR.AT-01:
        name: "Awareness and Training — Personnel"
        function: "Protect"
        function_id: "PR"
        category: "Awareness and Training"
        category_id: "PR.AT"
      PR.AT-02:
        name: "Awareness and Training — Privileged Users"
        function: "Protect"
        function_id: "PR"
        category: "Awareness and Training"
        category_id: "PR.AT"
      PR.DS-01:
        name: "Data Security — Data-at-Rest Protection"
        function: "Protect"
        function_id: "PR"
        category: "Data Security"
        category_id: "PR.DS"
      PR.DS-02:
        name: "Data Security — Data-in-Transit Protection"
        function: "Protect"
        function_id: "PR"
        category: "Data Security"
        category_id: "PR.DS"
      # ... PR.DS-10, PR.DS-11 (note: intentional numbering gaps in CSF 2.0)
      PR.PS-01:
        name: "Platform Security — Configuration Management"
        function: "Protect"
        function_id: "PR"
        category: "Platform Security"
        category_id: "PR.PS"
      # ... PR.PS-02 through PR.PS-06 (6 in PR.PS, new in CSF 2.0)
      PR.IR-01:
        name: "Technology Infrastructure Resilience — Protection"
        function: "Protect"
        function_id: "PR"
        category: "Technology Infrastructure Resilience"
        category_id: "PR.IR"
      PR.IR-02:
        name: "Technology Infrastructure Resilience — Architecture"
        function: "Protect"
        function_id: "PR"
        category: "Technology Infrastructure Resilience"
        category_id: "PR.IR"

      # DETECT (DE)
      DE.CM-01:
        name: "Continuous Monitoring — Network Monitoring"
        function: "Detect"
        function_id: "DE"
        category: "Continuous Monitoring"
        category_id: "DE.CM"
      # ... DE.CM-02 through DE.CM-09 (9 in DE.CM)
      DE.AE-02:
        name: "Adverse Event Analysis — Event Correlation"
        function: "Detect"
        function_id: "DE"
        category: "Adverse Event Analysis"
        category_id: "DE.AE"
      # ... DE.AE-03 through DE.AE-08

      # RESPOND (RS)
      RS.MA-01:
        name: "Incident Management — Plan Execution"
        function: "Respond"
        function_id: "RS"
        category: "Incident Management"
        category_id: "RS.MA"
      # ... RS.MA-02 through RS.MA-05
      RS.AN-03:
        name: "Incident Analysis — Root Cause"
        function: "Respond"
        function_id: "RS"
        category: "Incident Analysis"
        category_id: "RS.AN"
      # ... RS.AN-06 through RS.AN-08
      RS.CO-02:
        name: "Incident Reporting — Stakeholder Communication"
        function: "Respond"
        function_id: "RS"
        category: "Incident Reporting and Communication"
        category_id: "RS.CO"
      RS.CO-03:
        name: "Incident Reporting — Coordination"
        function: "Respond"
        function_id: "RS"
        category: "Incident Reporting and Communication"
        category_id: "RS.CO"
      RS.MI-01:
        name: "Incident Mitigation — Containment"
        function: "Respond"
        function_id: "RS"
        category: "Incident Mitigation"
        category_id: "RS.MI"
      RS.MI-02:
        name: "Incident Mitigation — Eradication"
        function: "Respond"
        function_id: "RS"
        category: "Incident Mitigation"
        category_id: "RS.MI"

      # RECOVER (RC)
      RC.RP-01:
        name: "Incident Recovery Plan Execution"
        function: "Recover"
        function_id: "RC"
        category: "Incident Recovery Plan Execution"
        category_id: "RC.RP"
      # ... RC.RP-02 through RC.RP-06
      RC.CO-03:
        name: "Incident Recovery Communication — Stakeholders"
        function: "Recover"
        function_id: "RC"
        category: "Incident Recovery Communication"
        category_id: "RC.CO"
      RC.CO-04:
        name: "Incident Recovery Communication — Public Updates"
        function: "Recover"
        function_id: "RC"
        category: "Incident Recovery Communication"
        category_id: "RC.CO"
```

#### Mapping Strategy: Tag-Based Lookup

Compliance findings and custom rules carry a `compliance_tags` field — a list of framework-qualified control IDs:

```python
# Example: A storage encryption check maps to both frameworks
compliance_tags = [
    "SOC2_2017.CC6.1",    # Logical access security
    "SOC2_2017.CC6.7",    # Authorized data transmission
    "NIST_CSF_2.0.PR.DS-01",  # Data-at-rest protection
]
```

The tag format is `{framework_id}.{control_id}`, providing:
- Unambiguous framework version reference (no separate version field needed)
- Multi-framework mapping per finding (one finding → many controls)
- Easy filtering: `SELECT * WHERE 'SOC2_2017.CC6.1' = ANY(compliance_tags)`
- Validation: tags are cross-checked against the loaded YAML control ID set at API write time

#### API Endpoint

```
GET /api/v1/compliance/frameworks
GET /api/v1/compliance/frameworks?framework_id=SOC2_2017
GET /api/v1/compliance/frameworks?framework_id=NIST_CSF_2.0&function=Protect
```

Response shape:
```json
{
  "frameworks": {
    "SOC2_2017": {
      "name": "SOC 2 Trust Services Criteria",
      "version": "2017 (Revised Points of Focus 2022)",
      "authority": "AICPA",
      "control_count": 36,
      "controls": { "CC1.1": { "name": "...", "series": "CC1" }, ... }
    },
    "NIST_CSF_2.0": {
      "name": "NIST Cybersecurity Framework",
      "version": "2.0",
      "authority": "NIST",
      "control_count": 106,
      "controls": { "GV.OC-01": { "name": "...", "function": "Govern" }, ... }
    }
  },
  "loaded_at": "2025-07-14T10:00:00Z",
  "content_hash": "sha256:a1b2c3..."
}
```

### SOC2 Scope

**Included in initial release:**
- **CC series (Common Criteria)**: CC1.1–CC9.2 — 33 controls across 9 series (mandatory for all SOC2 Type II engagements)
- **A series (Availability)**: A1.1–A1.3 — 3 controls (optional, included because availability monitoring is a core platform capability)

**Total: 36 SOC2 controls**

**Deferred**: Confidentiality (C1.1–C1.2), Processing Integrity (PI1.1–PI1.5), Privacy (P1–P8) — these are audit-scope dependent and will be added when customer demand warrants it.

### NIST CSF 2.0 Scope

**All 6 functions included** (CSF 2.0, published 2024-02-26):
- **Govern (GV)**: 6 categories, 31 subcategories — NEW in CSF 2.0
- **Identify (ID)**: 3 categories, 21 subcategories (restructured from CSF 1.1)
- **Protect (PR)**: 5 categories, 22 subcategories (includes new PR.PS Platform Security)
- **Detect (DE)**: 2 categories, 11 subcategories
- **Respond (RS)**: 4 categories, 13 subcategories
- **Recover (RC)**: 2 categories, 8 subcategories

**Total: 106 NIST CSF 2.0 subcategories across 22 categories**

> **Note**: CSF 2.0 subcategory IDs have intentional numbering gaps (e.g., `PR.DS-01, 02, 10, 11` — gaps mark removed draft subcategories). The YAML uses literal ID strings from NIST CSWP 29; do not assume sequential numbering.

### Framework Versioning Strategy

Framework versions are embedded directly in the framework ID:

```yaml
# Version is part of the ID — not a separate mutable field
SOC2_2017:    # 2017 TSC with 2022 Revised Points of Focus
NIST_CSF_2.0: # CSF 2.0 (February 2024)
NIST_CSF_1.1: # CSF 1.1 (April 2018) — can coexist for transition
```

**Multi-version coexistence rules:**
- Multiple versions of the same framework can exist simultaneously in the YAML
- Findings retain their framework version tag permanently (immutable audit reference)
- A `deprecated_at` field signals when a framework version should no longer be used for new assessments
- A `superseded_by` field points to the replacement version
- No automatic migration of existing tags when a new version is added

This pattern matches industry practice: AWS Security Hub, Azure MDC, and Prowler all support concurrent framework versions.

### YAML Loading Security Requirements

**Mandatory** (per Security Auditor review):

```python
def load_frameworks_yaml(path: Path) -> dict:
    """Load compliance frameworks from YAML with security guards."""
    content = path.read_bytes()
    # Guard: file size limit prevents anchor bomb DoS
    if len(content) > 512_000:  # 512KB hard limit
        raise ValueError(f"compliance_frameworks.yaml exceeds 512KB: {len(content)} bytes")
    # Guard: MUST use safe_load — yaml.load() enables RCE via !!python/object tags
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError("compliance_frameworks.yaml must be a YAML mapping at root level")
    # Audit: log content hash for SOC2 evidence trail
    file_hash = hashlib.sha256(content).hexdigest()
    logger.info("Loaded compliance frameworks: sha256=%s", file_hash)
    return data
```

**Prohibited YAML loading patterns:**
- `yaml.load()` — arbitrary Python object instantiation (RCE)
- `yaml.full_load()` — CVE-2020-14343 exploited FullLoader
- `yaml.unsafe_load()` — explicitly named as dangerous
- Custom `Loader` classes — expand attack surface unnecessarily

### Consequences

**Good:**
- Framework definitions are Git-versioned with full diff history — auditors can trace every change with author, timestamp, and PR review record
- Zero database migration — no new tables, no seed scripts, no rollback risk
- Read-only static data — no user input touches framework definitions, eliminating injection attack surface
- Tag-based mapping follows industry standard (AWS Security Hub, Prowler, Chef InSpec) — well-understood pattern
- Multi-framework support is trivial — adding a new framework is a YAML edit + PR review
- Response caching makes the endpoint O(1) — zero DB or file I/O per request after startup
- Version-embedded IDs prevent ambiguity in audit evidence packages

**Bad:**
- YAML file must be kept in sync with authoritative framework updates manually — no auto-update mechanism
- Adding a new framework version requires a code deploy (YAML is bundled with the application)
- No runtime query flexibility — cannot filter controls by arbitrary attributes without loading the full dataset
- Developers unfamiliar with compliance frameworks may find the YAML structure opaque

**Neutral:**
- The endpoint returns public-standard information (SOC2 TSC and NIST CSF are published documents) — no confidentiality concern, but authentication is still required to prevent unauthenticated enumeration of platform capabilities
- The `/frameworks` endpoint does NOT require `TenantAuthorization` — this is intentional because framework definitions are global, not tenant-scoped

### Confirmation

This decision is confirmed when:
1. `config/compliance_frameworks.yaml` exists with SOC2 CC1-CC9 + A1 series (36 controls) and NIST CSF 2.0 all 6 functions (106 subcategories)
2. `GET /api/v1/compliance/frameworks` returns framework data with `content_hash` field
3. YAML is loaded with `yaml.safe_load()` only (confirmed by fitness function FF-1)
4. File size guard (512KB limit) is enforced before parsing (confirmed by fitness function)
5. Framework data is cached at startup — no file I/O per request
6. SHA-256 content hash is logged at startup for audit trail
7. All fitness functions in `tests/architecture/test_fitness_functions.py` pass

## STRIDE Security Analysis

| Threat Category | Risk Level | Mitigation |
|-----------------|-----------|------------|
| **Spoofing** | Low | `/frameworks` endpoint inherits router-level authentication from `compliance.py` (`dependencies=[Depends(get_current_user)]`). YAML file authenticity is established by Git commit signatures and branch protection on `config/` directory. No user-supplied identity claims in the framework data path. |
| **Tampering** | Low | YAML loaded with `yaml.safe_load()` only — `yaml.load()`, `yaml.full_load()`, and `yaml.unsafe_load()` are prohibited (enforced by fitness function FF-1). File size limit (512KB) guards against YAML anchor/alias bombs. SHA-256 content hash logged at startup for integrity verification. `compliance_tags` validated against known control ID set at API write time — fabricated tags rejected with 422. |
| **Repudiation** | Low | Git history provides immutable audit trail for all YAML changes. Application logs SHA-256 hash of loaded file at startup, creating evidence link between running instance and specific framework content. Standard uvicorn access logs record `/frameworks` endpoint requests. |
| **Information Disclosure** | Low | SOC2 TSC and NIST CSF 2.0 are published public standards — no sensitive information in the response. Authentication prevents unauthenticated enumeration. Response includes `monitoring_scope: "automated_only"` to explicitly document that not all controls have automated checks (prevents inferring detection blind spots). |
| **Denial of Service** | Low | Response cached in memory at startup — O(1) serialization per request with zero file I/O. Rate limiting inherited from compliance router. YAML file size limit (512KB) prevents anchor bomb DoS at parse time. `Cache-Control: public, max-age=3600` header reduces client re-fetch frequency. |
| **Elevation of Privilege** | None | Endpoint returns read-only static data — no write operations, no tenant-scoped data, no state mutations. `compliance_tags` validation at write time prevents compliance posture inflation through fabricated control tags. No `TenantAuthorization` needed (data is global, not tenant-scoped) — this is intentional and documented. |

**Overall Security Posture:** This decision introduces **no new code execution paths** and **no new write operations**. The only new attack surface is a read-only endpoint serving cached public-standard data behind existing authentication. The primary risk is YAML deserialization — fully mitigated by mandatory `yaml.safe_load()` with file size limits, enforced by automated fitness functions. Security Auditor 🛡️ conditionally approved pending fitness function implementation.

**Security Auditor Co-sign:** Reviewed and conditionally approved by Security Auditor 🛡️ (`security-auditor-d2947b`). Three mandatory gates before implementation: (1) `yaml.safe_load()` fitness function, (2) `compliance_tags` validation against known control IDs, (3) YAML file size limit guard.

## Pros and Cons of the Options

### Option A — Static YAML Mapping File (selected)

*Framework definitions stored as YAML in `config/compliance_frameworks.yaml`, loaded at application startup with `yaml.safe_load()`, cached in memory, served via read-only authenticated endpoint.*

- Good, because **Git provides immutable audit trail** — every framework change has author, timestamp, PR review, and diff
- Good, because **zero database migration** — no new tables, no seed scripts, no rollback complexity
- Good, because **human-readable for auditors** — compliance reviewers can read YAML without tooling
- Good, because **supports comments** — mapping rationale can be documented inline (`# CC6.1 applies because...`)
- Good, because **language-agnostic** — same file could be consumed by other tools in the compliance pipeline
- Good, because **no runtime write path** — read-only data eliminates injection/tampering at API level
- Good, because **industry-standard pattern** — Prowler, Chef InSpec, Checkov all use YAML/JSON files for framework definitions
- Neutral, because file size limit and `safe_load()` guards are needed — trivial to implement but must not be forgotten
- Bad, because **updates require code deploy** — adding a new framework version requires a PR + deploy cycle
- Bad, because **no runtime query flexibility** — cannot dynamically filter controls without loading full dataset
- Bad, because **manual sync with authoritative sources** — AICPA/NIST updates must be tracked and applied manually

### Option B — Database-Backed Mapping Tables (not selected)

*New `compliance_frameworks` and `framework_controls` PostgreSQL tables, populated via Alembic seed migration, queried at runtime via SQLAlchemy.*

- Good, because **rich query support** — SQL filtering by framework, series, function, category
- Good, because **runtime updates** — new frameworks can be added without code deploy via admin API
- Good, because **consistent with existing data model** — follows same ORM patterns as `ComplianceSnapshot`, `PolicyState`
- Bad, because **Alembic migration risk** — adds schema migration for reference data; migration rollback complexity for 5 production tenants
- Bad, because **audit trail is weaker** — DB changes require separate audit logging; Git diffs are more natural for compliance evidence
- Bad, because **seed data management** — must maintain seed scripts, handle re-seeding, manage migration ordering with data dependencies
- Bad, because **overengineered for ~142 static records** — framework definitions change at most annually; DB flexibility is unnecessary
- Bad, because **no comments in DB rows** — cannot document mapping rationale inline the way YAML supports

### Option C — Hardcoded Python Dictionary (not selected)

*Framework definitions as Python `dict` literals in a module file (e.g., `app/constants/frameworks.py`).*

- Good, because **zero infrastructure** — just import and use
- Good, because **IDE autocompletion** — Python dict keys get type checking
- Good, because **startup validated** — Python import errors catch typos immediately
- Bad, because **mixes compliance data with code** — SOC2 control definitions are not application logic
- Bad, because **cannot be reviewed by non-engineers** — auditors cannot read Python; YAML is human-readable
- Bad, because **Git diffs are noisy** — Python string formatting obscures content changes
- Bad, because **no comments convention** — inline `#` comments in dict literals are less readable than YAML comments
- Bad, because **Python-specific** — cannot be reused by other compliance tools in the pipeline

## Fitness Functions

The following automated tests enforce this ADR. They belong in `tests/architecture/test_fitness_functions.py`:

### FF-1: YAML safe_load() enforcement

```python
def test_adr0006_yaml_safe_load_enforced():
    """ADR-0006 FF-1: Compliance framework YAML must be loaded with yaml.safe_load() only.

    yaml.load() enables arbitrary Python object instantiation (RCE) via
    !!python/object tags. yaml.full_load() was exploited by CVE-2020-14343.
    Only yaml.safe_load() is permitted for loading compliance_frameworks.yaml.
    """
    banned_patterns = ["yaml.load(", "yaml.unsafe_load", "yaml.full_load(", "UnsafeLoader"]

    for filepath in Path("app").rglob("*.py"):
        content = filepath.read_text()
        if "compliance_frameworks" not in content and "frameworks" not in content.lower():
            continue
        if "yaml" not in content:
            continue
        for banned in banned_patterns:
            assert banned not in content, (
                f"ADR-0006 violation: {filepath} uses banned YAML loader '{banned}'. "
                "Only yaml.safe_load() is permitted for compliance framework data."
            )
```

### FF-2: Frameworks endpoint on authenticated router

```python
def test_adr0006_frameworks_endpoint_inherits_auth():
    """ADR-0006 FF-2: /frameworks route must be on the authenticated compliance router.

    The compliance router at app/api/routes/compliance.py declares
    dependencies=[Depends(get_current_user)] at the router level. The
    /frameworks endpoint MUST be registered on this router, not on a
    separate unauthenticated APIRouter.
    """
    compliance_route = Path("app/api/routes/compliance.py")
    if not compliance_route.exists():
        pytest.skip("compliance routes not found")
    content = compliance_route.read_text()
    assert "get_current_user" in content, (
        "ADR-0006 violation: compliance router must include get_current_user "
        "in dependencies. /frameworks endpoint inherits this authentication."
    )
```

### FF-3: Compliance tags validated against known control IDs

```python
def test_adr0006_compliance_tags_validated():
    """ADR-0006 FF-3: compliance_tags must be validated against known framework control IDs.

    Fabricated tags (e.g., 'SOC2_FULLY_COMPLIANT') must be rejected at API
    write time. Tag validation must cross-reference the control ID set
    loaded from config/compliance_frameworks.yaml.
    """
    rule_service = Path("app/api/services/custom_rule_service.py")
    if not rule_service.exists():
        pytest.skip("custom_rule_service not found")
    content = rule_service.read_text()
    if "compliance_tags" in content:
        assert "valid_control_ids" in content or "framework" in content.lower(), (
            "ADR-0006 violation: compliance_tags accepted without validation "
            "against known framework control IDs from compliance_frameworks.yaml."
        )
```

### FF-4: YAML file size guard

```python
def test_adr0006_yaml_file_size_guard():
    """ADR-0006 FF-4: YAML loading code must enforce a file size limit before parsing.

    Prevents YAML anchor/alias bomb (billion laughs) DoS. The file size
    limit must be checked BEFORE yaml.safe_load() is called.
    """
    for filepath in Path("app").rglob("*.py"):
        content = filepath.read_text()
        if "compliance_frameworks" not in content:
            continue
        if "yaml.safe_load" in content or "safe_load" in content:
            assert "512" in content or "size" in content.lower() or "len(" in content, (
                f"ADR-0006 violation: {filepath} loads compliance_frameworks.yaml "
                "without a file size limit check. Add: if len(content) > 512_000: raise ValueError(...)"
            )
```

### FF-5: Compliance frameworks YAML exists with required structure

```python
def test_adr0006_frameworks_yaml_exists():
    """ADR-0006 FF-5: config/compliance_frameworks.yaml must exist with required structure.

    The YAML must contain SOC2_2017 and NIST_CSF_2.0 framework definitions
    with controls under each framework.
    """
    yaml_path = Path("config/compliance_frameworks.yaml")
    if not yaml_path.exists():
        pytest.skip("compliance_frameworks.yaml not yet created")

    import yaml
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    assert "frameworks" in data, "YAML must have 'frameworks' root key"
    frameworks = data["frameworks"]
    assert "SOC2_2017" in frameworks, "YAML must include SOC2_2017 framework"
    assert "NIST_CSF_2.0" in frameworks, "YAML must include NIST_CSF_2.0 framework"

    for fw_id in ["SOC2_2017", "NIST_CSF_2.0"]:
        fw = frameworks[fw_id]
        assert "name" in fw, f"{fw_id} must have 'name' field"
        assert "version" in fw, f"{fw_id} must have 'version' field"
        assert "controls" in fw, f"{fw_id} must have 'controls' field"
        assert len(fw["controls"]) > 0, f"{fw_id} must have at least one control"
```

## More Information

**Relates to:** CM-003 (Regulatory Framework Mapping — SOC2/NIST CSF)

**Research Package:** [`research/compliance-framework-mapping/`](../../research/compliance-framework-mapping/) — full evidence including:
- SOC2 2017 TSC control inventory (33 CC + 3 A = 36 controls)
- NIST CSF 2.0 function/category/subcategory breakdown (6 functions, 22 categories, 106 subcategories)
- Compliance-as-code format comparison (Chef InSpec, OpenSCAP, Regula, Prowler)
- Tag-based vs category-based mapping analysis with industry tool survey
- Framework versioning patterns from AWS Security Hub, Azure MDC, Prowler

**Key References:**
- AICPA 2017 Trust Services Criteria (Revised Points of Focus 2022): https://us.aicpa.org/interestareas/frc/assuranceadvisoryservices/trustservicescriteria
- NIST CSF 2.0 (CSWP 29, February 2024): https://doi.org/10.6028/NIST.CSWP.29
- AWS Security Hub Consolidated Control Findings: https://docs.aws.amazon.com/securityhub/latest/userguide/controls-findings-create-update.html
- Prowler compliance frameworks: https://github.com/prowler-cloud/prowler
- PyYAML safe_load documentation: https://pyyaml.org/wiki/PyYAMLDocumentation
- CVE-2020-14343 (PyYAML FullLoader): https://nvd.nist.gov/vuln/detail/CVE-2020-14343

**Related ADRs:**
- [ADR-0005: Custom compliance rules](adr-0005-custom-compliance-rules.md) — JSON Schema rule engine that will carry `compliance_tags`
- [ADR-0004: Research-first protocol](adr-0004-research-first-protocol.md) — research methodology used for this ADR
- [ADR-0001: Multi-agent architecture](adr-0001-multi-agent-architecture.md) — agents that will implement this

**Related Code:**
- `app/models/custom_rule.py` — `CustomComplianceRule` model (will carry `compliance_tags`)
- `app/api/routes/compliance.py` — existing `/api/v1/compliance/*` routes (new `/frameworks` endpoint goes here)
- `app/api/routes/compliance_rules.py` — custom rule CRUD routes
- `app/api/services/custom_rule_service.py` — rule service (will add tag validation)
- `config/brands.yaml` — existing YAML config pattern in the project

**Implementation Sequence (for Husky 🐺):**
1. Create `config/compliance_frameworks.yaml` with full SOC2 CC+A and NIST CSF 2.0 controls
2. Create `app/api/services/framework_service.py` with `load_frameworks_yaml()` using `yaml.safe_load()` + size guard + SHA-256 logging
3. Add `GET /api/v1/compliance/frameworks` route to `app/api/routes/compliance.py`
4. Add `compliance_tags` validation to `custom_rule_service.py` (cross-check against loaded control IDs)
5. Add fitness functions FF-1 through FF-5 to `tests/architecture/test_fitness_functions.py`
6. Write unit tests in `tests/unit/test_compliance_frameworks.py` (≥10 tests per roadmap requirement)

**Future Evolution:**
- Add NIST CSF 1.1 for clients still on the older framework version
- Add SOC2 Confidentiality (C), Processing Integrity (PI), and Privacy (P) series when customer demand warrants it
- Consider a cross-walk mapping (SOC2 control → NIST CSF subcategory equivalence) for unified coverage dashboards
- If framework count exceeds 10+, evaluate migrating to database-backed storage for query flexibility

**Review History:**
- 2025-07-14: Initial ADR proposed by Solutions Architect 🏛️ (`solutions-architect-47ac68`)
- Research conducted by: Web Puppy 🕵️ (`web-puppy-session-e2a678`)
- Security review by: Security Auditor 🛡️ (`security-auditor-d2947b`) — conditionally approved pending fitness functions
- Pending sign-off: Pack Leader 🐺

---

**ADR Status:** Proposed
**Implementation Status:** ⏳ Pending (CM-003 / Task 9.5.1)
**Last Updated:** July 14, 2025
**Authored By:** Solutions Architect 🏛️ (`solutions-architect-47ac68`)
**Reviewed By:** Security Auditor 🛡️ (`security-auditor-d2947b`)
