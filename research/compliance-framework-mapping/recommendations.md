# ADR Recommendations — Compliance Framework Mapping

**For**: Architecture Decision Record — Regulatory Framework Mapping in Compliance SaaS

---

## Priority 1 (Critical — Must Have in ADR)

### R1: Use YAML as Source of Truth for Framework Definitions

**Recommendation**: Store all compliance framework control definitions as YAML files in a
`config/compliance/frameworks/` directory, committed to Git.

**Evidence**:
- Industry tools (Chef InSpec `inspec.yml`, Prowler compliance JSON, Checkov) all use
  text-based files as source of truth
- YAML is human-readable — auditors can review without tooling
- Git provides full audit history (who changed what mapping, when, why)
- PRs with mandatory review for compliance/* directory creates documented approval workflow

**ADR Decision**: Compliance framework definitions → YAML files in version control

**Example structure**:
```
config/compliance/
├── frameworks/
│   ├── soc2_2017.yaml
│   ├── nist_csf_2.0.yaml
│   ├── nist_csf_1.1.yaml       # Keep for backward compat
│   └── nist_800_53_r5.yaml
└── mappings/
    ├── aws_checks.yaml          # check → [framework_controls]
    └── azure_checks.yaml
```

---

### R2: Use Framework ID with Embedded Version (`SOC2_2017`, `NIST_CSF_2.0`)

**Recommendation**: Framework IDs must include version to prevent ambiguity in findings,
reports, and exports. Never use bare `NIST_CSF` without a version suffix.

**Evidence**:
- Prowler uses `nist_csf_1.1_aws.json` and `nist_800_53_revision_5_aws.json` (version in filename)
- AWS Security Hub stores standards as `standards/nist-800-53/v/5.0.0`
- When organizations transition frameworks, both versions coexist for 12-24 months
- Audit reports must specify which version of a standard was assessed

**ADR Decision**: Framework IDs = `{FRAMEWORK}_{VERSION}` as immutable identifiers

**Format**:
```yaml
framework_id: SOC2_2017         # Not "SOC2"
framework_id: NIST_CSF_2.0      # Not "NIST_CSF" or "CSF"
framework_id: NIST_CSF_1.1      # Old version retained separately
framework_id: NIST_800_53_R5    # Revision in ID
```

---

### R3: Use Tag-Based (Control-Centric) Multi-Framework Mapping

**Recommendation**: A security check should contain an array of compliance tags referencing
multiple framework controls. Do NOT create separate check records per framework.

**Evidence**:
- AWS Security Hub "consolidated control findings" eliminates duplicate findings per standard
- Prowler's architecture: each check appears in multiple framework JSON files by reference
- Chef InSpec: `tag soc2: ['CC6.1'], tag nist: ['SC-28']` on single control
- Azure MDC is the outlier (assessment-centric); leads to duplicate findings — not recommended

**ADR Decision**: Tag-based mapping — one finding per check, multiple framework tags

**Data model**:
```yaml
# In check definition
check_id: s3_encryption_at_rest
compliance_tags:
  SOC2_2017:       [CC6.1, CC6.7]
  NIST_CSF_2.0:    [PR.DS-01]
  NIST_800_53_R5:  [SC-28]
  PCI_DSS_4.0:     [3.5]
```

---

### R4: Seed Database from YAML at Deploy Time

**Recommendation**: YAML files are source of truth; database tables are the queryable
runtime representation. Seed DB from YAML during application migrations/startup.

**Evidence**:
- Framework data is read-heavy, write-rarely (updates ~1-2x/year per framework)
- Compliance score queries require DB JOINs across findings, controls, and frameworks
- File I/O on every compliance query is unacceptable for real-time dashboards
- This project already uses YAML config files (e.g., `config/brands.yaml` pattern)

**ADR Decision**: YAML seed → DB for runtime; never update DB directly (always via YAML PR)

**Migration strategy**:
```python
# Django management command example
class Command(BaseCommand):
    def handle(self, *args, **options):
        for yaml_file in Path('config/compliance/frameworks').glob('*.yaml'):
            data = yaml.safe_load(yaml_file.read_text())
            Framework.objects.update_or_create(
                framework_id=data['framework']['id'],
                defaults={...}
            )
```

---

## Priority 2 (Important — Strongly Recommended)

### R5: Support Multiple Framework Versions Simultaneously

**Recommendation**: Design the schema to hold multiple versions of the same framework
family. Never overwrite old versions.

**Evidence**:
- Prowler maintains `cis_1.4_aws.json` AND `cis_1.5_aws.json` simultaneously
- AWS Security Hub supports CIS v1.2.0 and v1.4.0 simultaneously
- Enterprise audit cycles: companies mid-SOC 2 audit cannot change standards mid-year
- NIST CSF 1.1 → 2.0: Both versions active simultaneously since Feb 2024

**Schema recommendation**:
```sql
-- Framework versions as separate records
INSERT INTO frameworks VALUES ('NIST_CSF_1.1', 'NIST CSF', '1.1', '2018-04-16', NULL, TRUE);
INSERT INTO frameworks VALUES ('NIST_CSF_2.0', 'NIST CSF', '2.0', '2024-02-26', NULL, TRUE);
-- deprecated_at NULL means still active
```

---

### R6: Include `deprecated_at` and `superseded_by` in Framework Schema

**Recommendation**: Framework records must have lifecycle fields to support transitions.

**Evidence**:
- SOC 2 example: "2017 TSC" is the current version — if AICPA releases 2025 TSC,
  you need to sunset 2017 without deleting it (findings reference it)
- NIST CSF 2.0 was published Feb 2024; CSF 1.1 has no official sunset date yet
- Audit evidence must reference the specific version used during the assessment period

**Schema**:
```yaml
framework:
  id: NIST_CSF_1.1
  name: "NIST Cybersecurity Framework"
  version: "1.1"
  published_at: "2018-04-16"
  deprecated_at: null          # null = still active
  superseded_by: NIST_CSF_2.0
  source_url: "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.04162018.pdf"
```

---

### R7: Include Mapping Rationale for Audit Defensibility

**Recommendation**: Each compliance tag mapping should have an optional `rationale`
field explaining WHY this check maps to that control. Critical for audit defense.

**Evidence**:
- AICPA auditors review the "points of focus" for each TSC control
- A SOC 2 auditor may challenge whether `s3_encryption_at_rest` satisfies CC6.1
- Having documented rationale in YAML → Git history creates defensible audit artifacts

**Example**:
```yaml
check_id: s3_encryption_at_rest
compliance_tags:
  SOC2_2017:
    CC6.1:
      rationale: |
        CC6.1 requires logical access security software including protection of
        information assets. S3 server-side encryption protects data at rest from
        unauthorized access, directly satisfying the 'encryption of information
        assets' point of focus.
    CC6.7:
      rationale: |
        CC6.7 covers transmission/storage of information. SSE-S3 ensures data
        stored in S3 is encrypted, satisfying storage protection requirements.
```

---

## Priority 3 (Nice to Have — Future Optimization)

### R8: Consider Separating Common Criteria from Additional Criteria in SOC 2

**Recommendation**: Design the schema to distinguish CC (always required) from
A/C/PI/P series (additional, scope-dependent) in SOC 2.

**Why**: Not all clients have Availability or Confidentiality in scope. The schema
should allow per-client framework scope configuration.

**Implementation**:
```yaml
controls:
  CC6.1:
    required: true          # Part of Security TSC — always required
    category: security
  A1.1:
    required: false         # Only if Availability TSC in scope
    category: availability
  C1.1:
    required: false         # Only if Confidentiality TSC in scope
    category: confidentiality
```

---

### R9: Add Machine-Readable Compliance Report Export

**Recommendation**: The YAML-seeded DB approach makes it straightforward to export
compliance findings in ASFF (AWS Security Finding Format) or STIX format for
interoperability with external GRC tools.

**Evidence**:
- AWS Security Hub uses ASFF as universal finding format
- Azure MDC supports continuous export to Event Hubs/Log Analytics
- Customers may need to import findings into Splunk, Vanta, Drata, or ServiceNow

---

## ADR Decision Summary Table

| Decision | Chosen Approach | Alternative Rejected | Reason |
|----------|----------------|---------------------|--------|
| Storage Format | YAML (source of truth) | Hardcoded code | Auditability, PR review |
| Runtime Storage | Database (seeded from YAML) | File I/O at runtime | Query performance |
| Mapping Pattern | Tag-based (check → [controls]) | Category-based (duplicate findings) | AWS Security Hub precedent |
| Framework IDs | Version-embedded (`SOC2_2017`) | Bare name (`SOC2`) | Audit report clarity |
| Version Strategy | Multi-version coexistence | Overwrite old versions | Audit cycle overlap |
| Format for export | JSON (from DB) | XML (XCCDF) | Ecosystem compatibility |

---

## SOC 2 2017 TSC Quick Reference (for ADR)

| Series | Count | Controls |
|--------|-------|---------|
| CC1.x — Control Environment | 5 | CC1.1–CC1.5 |
| CC2.x — Communication & Information | 3 | CC2.1–CC2.3 |
| CC3.x — Risk Assessment | 4 | CC3.1–CC3.4 |
| CC4.x — Monitoring Activities | 2 | CC4.1–CC4.2 |
| CC5.x — Control Activities | 3 | CC5.1–CC5.3 |
| CC6.x — Logical/Physical Access | 8 | CC6.1–CC6.8 |
| CC7.x — System Operations | 5 | CC7.1–CC7.5 |
| CC8.x — Change Management | 1 | CC8.1 |
| CC9.x — Risk Mitigation | 2 | CC9.1–CC9.2 |
| **Total CC** | **33** | |
| A1.x — Availability (optional) | 3 | A1.1–A1.3 |
| C1.x — Confidentiality (optional) | 2 | C1.1–C1.2 |
| PI1.x — Processing Integrity (optional) | 5 | PI1.1–PI1.5 |
| P1–P8 — Privacy (optional) | 8 | Various |

## NIST CSF 2.0 Quick Reference (for ADR)

| Function | ID | Categories | Subcategories |
|---------|----|-----------|---------------|
| Govern (NEW) | GV | 6 | 31 |
| Identify | ID | 3 | 21 |
| Protect | PR | 5 | 22 |
| Detect | DE | 2 | 11 |
| Respond | RS | 4 | 13 |
| Recover | RC | 2 | 8 |
| **Total** | | **22** | **106** |

**Published**: February 26, 2024 | **Preceding**: CSF 1.1 (2018, 5 functions, 108 subcategories)
