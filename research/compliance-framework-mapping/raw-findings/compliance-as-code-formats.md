# Compliance-as-Code Tool Formats — Raw Findings

---

## Chef InSpec (Progress Chef)

**Source**: https://docs.chef.io/inspec/7.0/profiles/
**Current Version**: InSpec 7.0 (also 6.8, 5.24, 5.23 available)
**License**: Apache 2.0 (open source core)

### Profile Structure
```
profile/
├── README.md
├── controls/
│   ├── example.rb          ← Controls in Ruby DSL
│   └── control_etc.rb
├── libraries/
│   └── extension.rb
├── files/
│   └── extras.conf
└── inspec.yml              ← Profile metadata (YAML)
```

### inspec.yml (Profile Metadata — YAML Format)
```yaml
name: my-soc2-profile
title: SOC 2 Compliance Profile
maintainer: Security Team
copyright: ACME Corp
copyright_email: security@example.com
license: Apache-2.0
summary: SOC 2 Trust Services Criteria compliance checks
version: 1.0.0
supports:
  - platform: aws
inspec_version: '>= 4.0'
depends:
  - name: aws-compliance
    supermarket: compliance/aws-cis-level2
```

### Control File (Ruby DSL — .rb)
```ruby
control 'soc2-cc6.1' do
  impact 1.0
  title 'CC6.1 - Logical Access Security'
  desc 'The entity implements logical access security software...'
  tag soc2: ['CC6.1']
  tag nist: ['AC-2', 'AC-3', 'IA-2']
  tag severity: 'critical'

  describe aws_iam_users do
    its('entries') { should_not be_empty }
  end
end
```

### Key Observations
- **Framework mapping**: Tags in Ruby DSL (not YAML) — `tag soc2: ['CC6.1']`
- **Multi-framework**: Single control can have tags for SOC2, NIST, PCI-DSS simultaneously
- **Version control**: YAML + Ruby files are Git-friendly
- **Profile versioning**: Semantic versioning in `inspec.yml`
- **Supermarket**: Public profile registry (like npm for compliance)

---

## OpenSCAP

**Standard**: SCAP (Security Content Automation Protocol) — NIST standard
**Format**: XCCDF (Extensible Configuration Checklist Description Format) in **XML**
**Also uses**: OVAL (Open Vulnerability and Assessment Language) in XML

### XCCDF Example
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Benchmark xmlns="http://checklists.nist.gov/xccdf/1.2"
           id="RHEL-9-soc2-benchmark"
           style="SCAP_1.3">
  <status date="2024-01-01">draft</status>
  <title>SOC 2 Compliance Benchmark for RHEL 9</title>
  <version>1.0</version>

  <Profile id="soc2-cc6">
    <title>CC6 - Logical and Physical Access Controls</title>
    <select idref="rule-cc6.1-encryption" selected="true"/>
  </Profile>

  <Rule id="rule-cc6.1-encryption" severity="high">
    <title>CC6.1 - Encrypt Data at Rest</title>
    <description>Ensure filesystem encryption is enabled</description>
    <ident system="https://aicpa.org/tsc">CC6.1</ident>
    <check system="http://oval.mitre.org/XMLSchema/oval-definitions-5">
      <check-content-ref href="oval.xml" name="oval:cc6_encryption:def:1"/>
    </check>
  </Rule>
</Benchmark>
```

### Key Observations
- **Format**: XML — verbose, machine-readable, not human-friendly for editing
- **Auditability**: XML diffs are hard to read; poor for code review
- **Standard**: NIST-official SCAP standard; used in FISMA compliance
- **Tooling**: SCAP Workbench, OpenSCAP scanner (oscap CLI)
- **Version control**: XML works in Git but diffs are verbose
- **Use case**: OS-level compliance (RHEL, Ubuntu); not cloud-native

---

## Regula (Fugue/Lacework)

**Source**: https://regula.dev (open source, by Fugue/Lacework)
**Format**: Open Policy Agent (OPA) Rego language + JSON metadata
**License**: Apache 2.0

### Rego Policy Example
```rego
package rules.soc2_cc6_1_s3_encryption

import future.keywords.contains
import future.keywords.if
import future.keywords.in

__rego__metadoc__ := {
  "id": "FG_R00100",
  "title": "S3 bucket server-side encryption enabled",
  "description": "S3 bucket should have server-side encryption enabled (CC6.1)",
  "custom": {
    "controls": {
      "SOC2": ["CC6.1"],
      "NIST_800_53": ["SC-28"],
      "CIS_AWS_1_4": ["2.1.1"]
    },
    "severity": "High"
  }
}

deny[info] {
  bucket := input.resources[_]
  bucket.resource_type == "aws_s3_bucket"
  not bucket.config.server_side_encryption_configuration[_]
  info := {
    "message": sprintf("S3 bucket '%v' has no server-side encryption", [bucket.id])
  }
}
```

### Key Observations
- **Format**: Rego (OPA) language + embedded JSON metadata
- **Multi-framework mapping**: `"controls"` object maps single rule to multiple frameworks
- **Machine-readable**: JSON metadata within Rego is queryable
- **Auditability**: Good — Rego is text-based, Git-diffs cleanly
- **Version control**: Rego files are Git-friendly
- **Cloud native**: Designed for IaC (Terraform, CloudFormation, Kubernetes)

---

## Prowler

**Source**: https://github.com/prowler-cloud/prowler
**Stars**: 13.4k | **Forks**: 2.1k (as of research date)
**Format**: JSON files per framework per cloud provider

### Directory Structure
```
prowler/compliance/
├── aws/
│   ├── soc2_aws.json
│   ├── nist_csf_1.1_aws.json
│   ├── cis_1.4_aws.json
│   ├── cis_1.5_aws.json           ← Multiple versions simultaneously!
│   ├── nist_800_53_revision_5_aws.json
│   └── pci_3.2.1_aws.json
├── azure/
│   ├── soc2_azure.json
│   └── ...
└── gcp/
    └── ...
```

### JSON Compliance Format
```json
{
  "Framework": "SOC2",
  "Name": "System and Organization Controls 2 (SOC2)",
  "Version": "",
  "Provider": "AWS",
  "Description": "...",
  "Requirements": [
    {
      "Id": "cc_6_1",
      "Name": "CC6.1 The entity implements logical access security...",
      "Description": "Full description from AICPA TSC...",
      "Attributes": [
        {
          "ItemId": "cc_6_1",
          "Section": "CC6.0 - Logical and Physical Access",
          "Service": "s3",
          "Type": "automated"
        }
      ],
      "Checks": [
        "s3_bucket_public_access"
      ]
    }
  ]
}
```

### Key Observations
- **Format**: JSON per framework per cloud provider
- **Multi-version**: Multiple CIS versions coexist (`cis_1.4_aws.json`, `cis_1.5_aws.json`)
- **Version field**: Empty string in SOC2 file — no version tracking embedded
- **Control ID format**: Snake_case (`cc_6_1` not `CC6.1`)
- **One-to-many**: One control → many checks (checks array)
- **Many-to-many**: One check can appear in multiple framework JSON files
- **Auditability**: JSON diffs cleanly in Git; human-readable
- **Platforms**: 14 providers (aws, azure, gcp, kubernetes, m365, etc.)
- **Active**: Latest commit March 18, 2026

---

## AWS Security Hub (Tier 1 Cloud Tool)

**Source**: https://docs.aws.amazon.com/securityhub/latest/userguide/
**Format**: ASFF (Amazon Security Finding Format) — JSON schema

### Supported Standards (as of research date)
1. AWS Foundational Security Best Practices (FSBP)
2. AWS Resource Tagging
3. CIS AWS Foundations Benchmark
4. NIST SP 800-53 Revision 5
5. NIST SP 800-171 Revision 2
6. PCI DSS
7. Service-Managed Standard: AWS Control Tower

### Multi-Framework Control Mapping Approach
- **Control-centric**: Controls exist independently of standards
- **Consolidated Control Findings**: One finding per control, even across multiple standards
- **Standard = tag**: Standards are metadata labels applied to controls
- Official AWS quote: *"Individual controls can apply to more than one standard"*
- If consolidated findings OFF: separate finding per enabled standard per control
- If consolidated findings ON: single finding per control regardless of standard count

### ASFF Compliance Field
```json
{
  "Compliance": {
    "Status": "PASSED",
    "RelatedRequirements": [
      "NIST.800-53.r5 AC-2",
      "NIST.800-53.r5 AC-3",
      "PCI DSS v3.2.1 requirement 7.1"
    ],
    "SecurityControlId": "IAM.1",
    "AssociatedStandards": [
      {"StandardsId": "standards/aws-foundational-security-best-practices/v/1.0.0"},
      {"StandardsId": "standards/nist-800-53/v/5.0.0"}
    ]
  }
}
```

---

## Azure Regulatory Compliance (Defender for Cloud)

**Source**: https://learn.microsoft.com/en-us/azure/defender-for-cloud/regulatory-compliance-dashboard
**Last Updated**: July 15, 2025
**Format**: Azure Policy definitions (JSON) + compliance standard schemas

### Key Approach
- **Assessment-centric**: Each control has automated + manual assessments
- **Multi-cloud**: Supports Azure, AWS, GCP in same dashboard
- **Default standard**: MCSB (Microsoft Cloud Security Benchmark)
- **Purview integration**: Compliance data flows to Microsoft Purview Compliance Manager
- Continuous export to Event Hubs or Log Analytics
- Report generation: PDF, CSV, Azure certification reports

### Supported Standard Types
- Industry: PCI DSS, SOC, ISO
- Government: NIST, FedRAMP, HIPAA
- Regional: GDPR, UK Cyber Essentials
- Cloud-specific: CIS Azure, Azure Security Benchmark

---

## Format Comparison Table

| Tool | Primary Format | Secondary | Multi-Framework | Auditability | Version Control |
|------|---------------|-----------|-----------------|--------------|-----------------|
| Chef InSpec | YAML + Ruby DSL | — | Tags in Ruby | ✅ Good | ✅ Git-native |
| OpenSCAP | XML (XCCDF) | XML (OVAL) | XCCDF profiles | ⚠️ Poor (verbose XML) | ⚠️ Verbose diffs |
| Regula | Rego (OPA) | JSON embedded | Control metadata | ✅ Good | ✅ Git-native |
| Prowler | JSON | — | Multiple JSON files | ✅ Good | ✅ Clean diffs |
| AWS Security Hub | ASFF (JSON) | — | Tags/Standards array | ✅ API | ❌ Managed service |
| Azure MDC | JSON policies | — | Policy initiative | ✅ ARM/Bicep | ✅ IaC-managed |

---

## Industry Consensus on Best Format for Compliance Mapping Data

### For Static Compliance Definitions (Control Metadata)
**Winner: YAML** — Most compliance-as-code frameworks (Terraform compliance, Checkov, kics)
use YAML for control definitions because:
1. Human-readable — auditors can review without tooling
2. Git-diff friendly — changes are clearly visible in PRs
3. Comments supported — can explain mapping rationale
4. Industry standard for "source of truth" config files
5. Easily validated with JSON Schema (YAML is a superset of JSON)

### For Machine-Readable Compliance Data (API responses, exports)
**Winner: JSON** — APIs, databases, and automation tools use JSON:
1. Universal language for APIs
2. Strict schema validation
3. No comment ambiguity
4. Native to most databases (PostgreSQL JSONB, SQLite JSON)

### For Audit Trail
**Winner: Both in Git** — The format matters less than version control:
1. Every change tracked with author, timestamp, commit message
2. PR review creates documented approval workflow
3. Tag-based releases for version milestones
4. Diff visibility for compliance deltas between versions

### What NOT to do
- **Hardcoded in application code**: No — creates coupling, requires code deploy to update mappings
- **Only in database with no backup to files**: No — loses auditability of changes
- **Only in a managed service config**: No — vendor lock-in, no portable audit trail
