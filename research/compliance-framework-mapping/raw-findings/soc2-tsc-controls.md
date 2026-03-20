# SOC 2 Trust Services Criteria (TSC) — Raw Findings

**Source**: AICPA official page + Prowler soc2_aws.json (cross-referenced)
**Primary Source URL**: https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022
**Published**: September 30, 2023 (554.3 KB PDF)
**Version**: 2017 Trust Services Criteria (With Revised Points of Focus — 2022)

---

## Framework Versioning Note

The "2017" in SOC 2 is the framework version year (not publication year). AICPA updated the
**Points of Focus** in 2022 but kept the 2017 TSC structure. The full document was re-published
September 30, 2023. There is **no separate "2023 TSC"** — the current authoritative edition is
**"2017 TSC (With Revised Points of Focus – 2022)"**.

---

## Common Criteria (CC) Series

The CC series is mandatory for all SOC 2 engagements (Security Trust Service Category).

| Control ID | Name / Topic | Section |
|-----------|-------------|---------|
| **CC1.x — Control Environment** (5 controls) | | |
| CC1.1 | COSO Principle 1: Demonstrates Commitment to Integrity and Ethical Values | CC1.0 |
| CC1.2 | COSO Principle 2: Board Independence and Oversight of Internal Controls | CC1.0 |
| CC1.3 | COSO Principle 3: Organizational Structure, Reporting Lines, and Authorities | CC1.0 |
| CC1.4 | COSO Principle 4: Commitment to Competence | CC1.0 |
| CC1.5 | COSO Principle 5: Enforcement of Accountability | CC1.0 |
| **CC2.x — Communication and Information** (3 controls) | | |
| CC2.1 | COSO Principle 13: Obtains/Uses Relevant Quality Information | CC2.0 |
| CC2.2 | COSO Principle 14: Communicates Internally | CC2.0 |
| CC2.3 | COSO Principle 15: Communicates Externally | CC2.0 |
| **CC3.x — Risk Assessment** (4 controls) | | |
| CC3.1 | COSO Principle 6: Specifies Suitable Objectives | CC3.0 |
| CC3.2 | COSO Principle 7: Identifies and Analyzes Risk | CC3.0 |
| CC3.3 | COSO Principle 8: Assesses Fraud Risk | CC3.0 |
| CC3.4 | COSO Principle 9: Identifies and Analyzes Significant Change | CC3.0 |
| **CC4.x — Monitoring Activities** (2 controls) | | |
| CC4.1 | COSO Principle 16: Conducts Ongoing and/or Separate Evaluations | CC4.0 |
| CC4.2 | COSO Principle 17: Evaluates and Communicates Deficiencies | CC4.0 |
| **CC5.x — Control Activities** (3 controls) | | |
| CC5.1 | COSO Principle 10: Selects and Develops Control Activities | CC5.0 |
| CC5.2 | COSO Principle 11: General Controls Over Technology | CC5.0 |
| CC5.3 | COSO Principle 12: Deploys Controls Through Policies and Procedures | CC5.0 |
| **CC6.x — Logical and Physical Access Controls** (8 controls) | | |
| CC6.1 | Logical Access Security Software, Infrastructure, and Architectures | CC6.0 |
| CC6.2 | System Credentials and Access for New Users | CC6.0 |
| CC6.3 | Role-Based Access — Least Privilege, Segregation of Duties | CC6.0 |
| CC6.4 | Physical Access Restrictions | CC6.0 |
| CC6.5 | Logical and Physical Access Credential Removal on Termination | CC6.0 |
| CC6.6 | Logical Access Security Against External Threats | CC6.0 |
| CC6.7 | Transmission, Movement, and Removal of Information | CC6.0 |
| CC6.8 | Prevention/Detection of Unauthorized or Malicious Software | CC6.0 |
| **CC7.x — System Operations** (5 controls) | | |
| CC7.1 | Detection and Monitoring Procedures for Vulnerabilities | CC7.0 |
| CC7.2 | Monitoring for Anomalies Indicative of Malicious Acts | CC7.0 |
| CC7.3 | Evaluation of Security Events | CC7.0 |
| CC7.4 | Response to Security Incidents | CC7.0 |
| CC7.5 | Identification and Recovery from Security Incidents | CC7.0 |
| **CC8.x — Change Management** (1 control) | | |
| CC8.1 | Authorizes, Designs, Tests, and Approves Changes | CC8.0 |
| **CC9.x — Risk Mitigation** (2 controls) | | |
| CC9.1 | Risk Mitigation Activities | CC9.0 |
| CC9.2 | Business Partners and Vendors Risk Assessment | CC9.0 |

### CC Control Count Summary
| Series | Section Name | Count |
|--------|-------------|-------|
| CC1.x | Control Environment | 5 |
| CC2.x | Communication and Information | 3 |
| CC3.x | Risk Assessment | 4 |
| CC4.x | Monitoring Activities | 2 |
| CC5.x | Control Activities | 3 |
| CC6.x | Logical and Physical Access Controls | 8 |
| CC7.x | System Operations | 5 |
| CC8.x | Change Management | 1 |
| CC9.x | Risk Mitigation | 2 |
| **TOTAL** | | **33** |

---

## Availability (A) Series

Additional criteria for the Availability Trust Service Category. Organizations include these
only when scoped for the Availability TSC.

| Control ID | Name / Topic | Section |
|-----------|-------------|---------|
| A1.1 | Capacity Management — Current and Planned Capacity | A1.0 |
| A1.2 | Environmental Protections, Backups, and Recovery Infrastructure | A1.0 |
| A1.3 | Recovery Plan Testing | A1.0 |

**A Series Count: 3 controls**

---

## Other Optional Series (not in scope for basic Security-only audit)

| Series | Section | Count |
|--------|---------|-------|
| Confidentiality (C) | C1.x | 2 controls (C1.1, C1.2) |
| Processing Integrity (PI) | PI1.x | 5 controls (PI1.1–PI1.5) |
| Privacy (P) | P1.x–P8.x | 8 controls |

---

## Prowler JSON Format for SOC 2 Controls (Verified Structure)

```json
{
  "Framework": "SOC2",
  "Name": "System and Organization Controls 2 (SOC2)",
  "Version": "",
  "Provider": "AWS",
  "Requirements": [
    {
      "Id": "cc_6_1",
      "Name": "CC6.1 The entity implements logical access security...",
      "Description": "...",
      "Attributes": [
        {
          "ItemId": "cc_6_1",
          "Section": "CC6.0 - Logical and Physical Access",
          "Service": "s3",
          "Type": "automated"
        }
      ],
      "Checks": ["s3_bucket_public_access"]
    }
  ]
}
```

**Key observation**: Prowler's SOC 2 JSON uses snake_case IDs (`cc_6_1` not `CC6.1`),
and the Availability section uses `cc_a_1_1` (maps to A1.2 in the AICPA document).
**Version field is empty string** — no version tracking in the file itself.

---

## Controls Covered in Prowler's soc2_aws.json (Automatable Subset)

The following CC controls appear in Prowler's file (not exhaustive — covers automatable checks only):
- CC1.3, CC2.1, CC3.1, CC3.2, CC3.3, CC3.4, CC4.2
- CC5.2, CC6.1, CC6.2, CC6.3, CC6.6, CC6.7, CC6.8
- CC7.1, CC7.2, CC7.3, CC7.4, CC7.5, CC8.1
- A1.2 (labeled as `cc_a_1_1`), C1.1, C1.2
- PI1.2, PI1.3, PI1.4, PI1.5

**Controls NOT in Prowler** (manual/non-automatable):
CC1.1, CC1.2, CC1.4, CC1.5, CC2.2, CC2.3, CC4.1, CC5.1, CC5.3, CC6.4, CC6.5, CC9.1, CC9.2,
A1.1, A1.3
