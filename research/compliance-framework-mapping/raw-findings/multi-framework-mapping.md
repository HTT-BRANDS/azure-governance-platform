# Multi-Framework Compliance Mapping — Industry Patterns

---

## The Core Problem

A single security finding (e.g., "S3 bucket has no server-side encryption") may be relevant to
multiple regulatory frameworks simultaneously:
- SOC 2 CC6.1 (Logical Access — data protection)
- NIST CSF 2.0 PR.DS-01 (Data at rest protected)
- NIST SP 800-53 SC-28 (Protection of Information at Rest)
- PCI DSS 3.2.1 Requirement 3.5
- CIS AWS 1.4 Benchmark 2.1.1

The question for architecture: **Where and how do you store these mappings?**

---

## Industry Pattern 1: Tag-Based (Control-Centric) — DOMINANT

Used by: AWS Security Hub, Prowler, Regula, Chef InSpec

### How It Works
1. Each security check/control is assigned an **array of compliance tags**
2. Tags reference specific framework control IDs
3. A single finding is generated once per check
4. Compliance reporting aggregates by tag group

### AWS Security Hub Implementation
```
Control: IAM.1 (Root account MFA enabled)
  → Standards tags: [FSBP, CIS 1.2.0, NIST 800-53 r5, PCI DSS]
  → RelatedRequirements: ["NIST.800-53.r5 IA-2", "PCI DSS v3.2.1 req 8.3.1"]
  → Consolidated Finding: 1 finding per control (not 4)
```

**AWS Official documentation**: "Individual controls can apply to more than one standard.
If you enable consolidated control findings, Security Hub generates a single finding for each
control, even if the control applies to more than one standard."

### Prowler Implementation
- Each framework has its own JSON file with `"Checks"` arrays
- The same check (`iam_root_mfa_enabled`) appears in:
  - `soc2_aws.json` → CC7.2 Checks
  - `nist_800_53_revision_5_aws.json` → IA-2 Checks
  - `cis_1.5_aws.json` → 1.5 Checks
- **Direction**: Framework → Controls → Checks (framework-files reference checks)

### Chef InSpec Implementation
```ruby
control 'aws-s3-encryption' do
  tag soc2:    ['CC6.1']
  tag nist:    ['SC-28', 'SC-8']
  tag pcidss:  ['3.5']
  tag severity: 'high'
  # ... test logic
end
```
**Direction**: Controls → Frameworks (controls have tag arrays)

---

## Industry Pattern 2: Category-Based (Standard-Centric)

Used by: Azure Regulatory Compliance, some GRC platforms

### How It Works
1. Each compliance standard is a separate "initiative" or "policy set"
2. Controls are organized per standard
3. A finding appears multiple times (once per relevant standard)
4. Reporting is organized by standard, not by control

### Azure Implementation
```
Standard: NIST SP 800-53 R5
  └── Control: SC-28 (Encryption at Rest)
       └── Assessment: "Storage account encryption enabled"
                → Status: PASS/FAIL

Standard: SOC 2
  └── Control: CC6.1 (Logical Access)
       └── Assessment: "Storage account encryption enabled"  ← Same check
                → Status: PASS/FAIL
```

**Azure Characteristic**: A finding can exist separately per standard — leads to duplicate
findings until "Purview integration" consolidates them.

---

## Comparison: Tag-Based vs Category-Based

| Aspect | Tag-Based (Control-Centric) | Category-Based (Standard-Centric) |
|--------|----------------------------|-----------------------------------|
| Data Model | Check → [Framework IDs] | Framework → [Controls] → [Checks] |
| Finding Duplicates | None (1 finding per check) | Yes (1 per framework per check) |
| New Framework Addition | Add new tag to existing control | Create new framework mapping set |
| Compliance Reporting | Aggregate by tag group | Dedicated per-standard view |
| Gap Analysis | Easy (which controls lack which tags?) | Harder (join across standard sets) |
| Example Tools | Prowler, Chef InSpec, Regula, AWS Security Hub | Azure MDC, OpenSCAP, GRC platforms |
| **Industry Trend** | ✅ Growing dominant | Legacy/enterprise |

---

## Recommended Data Model (Industry Standard)

Based on analysis of Prowler, AWS Security Hub, and Regula:

### Many-to-Many with Junction Table
```
Checks (or Controls)
  ├── check_id: "s3_bucket_encryption"
  ├── title: "S3 Bucket Server-Side Encryption Enabled"
  └── severity: "HIGH"

Frameworks
  ├── framework_id: "SOC2_2017"
  ├── name: "SOC 2 Trust Services Criteria"
  └── version: "2017_rev2022"

FrameworkControls
  ├── control_id: "CC6.1"
  ├── framework_id: "SOC2_2017"
  └── name: "Logical Access Security..."

CheckFrameworkMappings (Junction)
  ├── check_id: "s3_bucket_encryption"
  ├── framework_id: "SOC2_2017"
  └── control_id: "CC6.1"
```

### Alternative: Flat Tag Array (Simpler, Prowler-style)
```json
{
  "check_id": "s3_bucket_encryption",
  "compliance": {
    "SOC2_2017": ["CC6.1"],
    "NIST_CSF_2.0": ["PR.DS-01"],
    "NIST_800_53_r5": ["SC-28"],
    "PCI_DSS_3.2.1": ["3.5"]
  }
}
```

---

## Storage Format Decision: YAML vs Database vs Hardcoded

### Option A: Static YAML Files (Recommended for Framework Definitions)
```yaml
# frameworks/soc2_2017.yaml
framework:
  id: SOC2_2017
  name: "SOC 2 Trust Services Criteria"
  version: "2017 (Revised Points of Focus 2022)"
  published: "2023-09-30"
  source: "https://www.aicpa-cima.com/..."

controls:
  CC1.1:
    name: "COSO Principle 1 - Integrity and Ethical Values"
    section: "CC1.0 - Control Environment"
    required: true
  CC6.1:
    name: "Logical Access Security Software"
    section: "CC6.0 - Logical and Physical Access Controls"
    required: true
```

**Pros**: Human-readable, Git-auditable, no database dependency, easy to review
**Cons**: Requires file I/O on load, no relational queries

### Option B: Database Records (Recommended for Runtime Queries)
```sql
-- Framework definitions seeded from YAML
SELECT c.control_id, c.name, f.name as framework
FROM framework_controls c
JOIN frameworks f ON c.framework_id = f.id
JOIN check_mappings m ON c.control_id = m.control_id
WHERE m.check_id = 'iam_root_mfa_enabled'
```

**Pros**: Query flexibility, join with findings, compliance scores
**Cons**: Changes require migrations + deployment, harder audit trail

### Option C: Hardcoded in Application Code
```python
SOC2_MAPPINGS = {
    "iam_root_mfa_enabled": ["CC7.2", "CC6.1"],
    "s3_encryption": ["CC6.1", "CC6.7"],
}
```

**Pros**: Simple, no file or DB dependency
**Cons**: ❌ Not auditable, requires code deploy to update, mixes concerns,
         no version control of mappings separate from code

### Industry Consensus: YAML-seeded Database
- **Source of truth**: YAML files in `config/` or `data/` directory, version-controlled in Git
- **Runtime**: Seed into database on startup/migration for queryability
- **Audit trail**: YAML changes tracked in Git with PRs; DB seeds are deterministic
- **Example**: This project already uses `config/brands.yaml` as source of truth for
  brand definitions — same pattern applies to compliance framework definitions

---

## Framework Version Support: Do Organizations Maintain Multiple Versions?

### Yes — Demonstrated by Multiple Tools

**Prowler** (verified in research):
```
prowler/compliance/aws/
├── cis_1.4_aws.json      ← v1.4 still active
├── cis_1.5_aws.json      ← v1.5 current
├── nist_csf_1.1_aws.json ← old version still maintained
└── nist_800_53_revision_5_aws.json
```

**AWS Security Hub**: Maintains CIS v1.2.0 and CIS v1.4.0 simultaneously
**Azure MDC**: Supports multiple versions of PCI DSS, ISO 27001 simultaneously

### Why Multiple Versions Coexist
1. **Audit cycle overlap**: Organizations mid-audit can't change standards mid-year
2. **Customer requirements**: Different customers may require different versions
3. **Transition period**: New version adoption takes 12-24 months in enterprise
4. **Contractual obligations**: Some contracts specify a version year

### Industry Version Naming Convention
```
framework_id: "NIST_CSF_1.1"   # version in the ID
framework_id: "NIST_CSF_2.0"   # new version separate record
```
NOT:
```
framework_id: "NIST_CSF"        # ambiguous — which version?
framework_version: "2.0"        # version as separate field
```

**Best practice**: Embed version in framework_id for unambiguous reference in findings,
audit reports, and exports.
