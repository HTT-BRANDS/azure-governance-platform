# Azure Policy → SOC2/NIST Mapping: Approaches & Best Practices

**Sources**:  
- Azure/azure-policy GitHub repository (authoritative, March 2026)
- Microsoft Learn: Azure Policy Regulatory Compliance docs
- NIST CPRT Informative References tool
- Azure Policy built-in initiative JSONs: SOC_2.json, NIST_CSF_v2.0.json

---

## How Azure Policy Implements Regulatory Mapping

### 1. Built-In Initiative Architecture

Azure Policy regulatory compliance works via **Policy Set Definitions** (initiatives):

```json
{
  "policyDefinitionGroups": [
    {
      "name": "SOC_2_CC6.1",
      "additionalMetadataId": "/providers/Microsoft.PolicyInsights/policyMetadata/SOC_2_CC6.1"
    }
  ],
  "policyDefinitions": [
    {
      "policyDefinitionReferenceId": "...",
      "policyDefinitionId": "/providers/Microsoft.Authorization/policyDefinitions/...",
      "groupNames": ["SOC_2_CC6.1", "SOC_2_CC6.6"]
    }
  ]
}
```

**Key insight**: A single Azure policy (e.g., "MFA should be enabled for accounts with owner permissions") can map to **multiple** controls across **multiple frameworks** simultaneously. This is the N:M mapping pattern.

---

## 2. The Three-Layer Mapping Model

```
Azure Policy Definition         Control Framework Category       Control ID(s)
─────────────────────────      ─────────────────────────       ─────────────
"MFA required for owners"  →   SOC 2 CC6.1                     CC6.1
                           →   SOC 2 CC6.3                     CC6.3
                           →   NIST CSF v2.0 PR.AA              PR.AA-01
                           →   NIST CSF v2.0 PR.AA_01           PR.AA-01
                           →   NIST 800-53 R5 IA-2              IA-2
```

**Layer 1** — Azure Policy Definition (the actual technical check, e.g., Audit/Deny effect)  
**Layer 2** — Policy Group Name (the framework control ID, e.g., `SOC_2_CC6.1`)  
**Layer 3** — Framework Category (the human-readable control name)

---

## 3. Standard Mapping Table Formats

### Format A: Policy → Controls (used in Azure Compliance Portal)
| Azure Policy Name | Policy ID | SOC 2 Control(s) | NIST CSF Control(s) |
|-------------------|-----------|-----------------|---------------------|
| MFA for subscription owners | ... | CC6.1, CC6.3 | PR.AA, PR.AA-01 |
| Storage public access disabled | ... | CC6.6, CC6.7 | PR.AA-05, PR.DS-01 |

### Format B: Control → Policies (used in audit reports)
| Control ID | Control Name | Mapped Azure Policies | Pass Rate |
|------------|-------------|----------------------|-----------|
| CC6.1 | Logical access security | 12 policies | 87% |
| CC7.1 | Detection and monitoring | 8 policies | 92% |
| PR.AA-01 | Identities/credentials managed | 5 policies | 95% |

### Format C: Cross-Framework (used for dual compliance)
| Azure Policy | SOC 2 | NIST CSF 2.0 | NIST 800-53 R5 | ISO 27001 |
|-------------|-------|-------------|----------------|-----------|
| MFA for admins | CC6.1 | PR.AA-01 | IA-2 | A.9.4.2 |
| Encryption at rest | CC6.1, C1.1 | PR.DS-01 | SC-28 | A.10.1 |

---

## 4. Key Azure-Native Mapping Mechanisms

### A. policyMetadata API
Microsoft maintains metadata for each control group at:
```
GET /providers/Microsoft.PolicyInsights/policyMetadata/{metadataName}
```
Example: `/providers/Microsoft.PolicyInsights/policyMetadata/NIST_CSF_v2.0_PR.AA_01`

This returns:
- Control ID
- Control title
- Control description
- Framework reference URL
- Owner (Customer vs Microsoft vs Shared)

### B. Compliance State API
```
POST /subscriptions/{subscriptionId}/providers/Microsoft.PolicyInsights/policyStates/latest/queryResults
```

With filter: `policyDefinitionGroupNames/any(g: g eq 'SOC_2_CC6.1')`

This lets you query ALL resources' compliance state **grouped by control**.

### C. policyDefinitionGroups in Assessments
Azure Security Center (Defender for Cloud) exposes compliance against built-in initiatives:
- Regulatory compliance dashboard shows % compliant per control
- Export via: Continuous export → Log Analytics → KQL queries

---

## 5. Best Practice: The Group-Name Convention

Azure Policy group names follow this convention:
```
{FRAMEWORK}_{VERSION}_{CONTROL_ID}
```

Examples:
- `SOC_2_CC6.1` — SOC 2 control CC6.1
- `NIST_CSF_v2.0_PR.AA_01` — NIST CSF 2.0 PR.AA-01
- `NIST_SP_800-53_R5_IA-2` — NIST 800-53 Rev 5 IA-2
- `PCI_DSS_v4.0.1_7.2` — PCI DSS v4.0.1 requirement 7.2

**For your application**: Store these group name strings as foreign keys in your database to enable cross-framework queries.

---

## 6. Microsoft's Shared Responsibility Model in Mappings

For cloud services, controls fall into three ownership categories:

| Ownership | Meaning | Example |
|-----------|---------|---------|
| **Microsoft** | Microsoft is responsible; customer inherits compliance | Physical data center security (CC6.4) |
| **Customer** | Customer must implement | MFA configuration (CC6.1) |
| **Shared** | Both Microsoft and customer have responsibilities | Encryption key management (CC6.1, CC6.7) |

**Azure Policy built-in initiatives primarily cover Customer and Shared controls.**

The policyMetadata `owner` field indicates: `"Microsoft"`, `"Customer"`, or `"Shared"`.

---

## 7. Control Coverage Analysis: What Azure Built-In Covers

### SOC 2 Coverage by Category
| TSC Category | Total Controls | Azure Built-In Maps | Coverage |
|-------------|---------------|--------------------:|---------|
| CC1 (Control Environment) | 5 | ~3 | 60% |
| CC2 (Communication) | 3 | ~2 | 67% |
| CC3 (Risk Assessment) | 4 | ~2 | 50% |
| CC4 (Monitoring) | 2 | ~2 | 100% |
| CC5 (Control Activities) | 3 | ~2 | 67% |
| **CC6 (Logical/Physical Access)** | **8** | **8** | **100%** |
| **CC7 (System Operations)** | **5** | **5** | **100%** |
| **CC8 (Change Management)** | **1** | **1** | **100%** |
| CC9 (Risk Mitigation) | 2 | ~1 | 50% |
| A1 (Availability) | 3 | 3 | 100% |
| C1 (Confidentiality) | 2 | ~1 | 50% |

### NIST CSF 2.0 Coverage by Category
| Function | Categories | Azure Built-In Subcategories | Notes |
|----------|-----------|------------------------------|-------|
| GV (Govern) | 6 | 2 (GV.OC-04, GV.SC-07) | Limited — governance is policy/process heavy |
| ID (Identify) | 3 | 3 (AM-01, RA-01, RA-07) | Core asset/risk mgmt covered |
| **PR (Protect)** | **5** | **8 subcategories** | **Best coverage** |
| **DE (Detect)** | **2** | **6 subcategories** | **Strong monitoring coverage** |
| RS (Respond) | 4 | 2 (CO-02, CO-03) | Communication only; MA/AN/MI gaps |
| RC (Recover) | 2 | 2 (RP, RP-04) | Backup integrity covered |

---

## 8. Recommended Mapping Implementation Patterns

### Pattern 1: Database Schema Approach
```sql
-- Framework Registry
CREATE TABLE compliance_frameworks (
    id VARCHAR(50) PRIMARY KEY,  -- 'SOC2_2017', 'NIST_CSF_2_0'
    name VARCHAR(200),
    version VARCHAR(50),
    published_date DATE,
    azure_initiative_id VARCHAR(200)  -- Policy Set Definition ID
);

-- Control Categories  
CREATE TABLE compliance_categories (
    id VARCHAR(100) PRIMARY KEY,  -- 'CC6', 'PR.AA'
    framework_id VARCHAR(50) REFERENCES compliance_frameworks(id),
    name VARCHAR(200),           -- 'Logical and Physical Access Controls'
    description TEXT
);

-- Individual Controls
CREATE TABLE compliance_controls (
    id VARCHAR(100) PRIMARY KEY,  -- 'CC6.1', 'PR.AA-01'
    category_id VARCHAR(100) REFERENCES compliance_categories(id),
    azure_group_name VARCHAR(200), -- 'SOC_2_CC6.1', 'NIST_CSF_v2.0_PR.AA_01'
    description TEXT,
    cloud_relevance VARCHAR(20)   -- 'HIGH', 'MEDIUM', 'LOW'
);

-- Policy-to-Control Mapping
CREATE TABLE policy_control_mappings (
    policy_definition_id VARCHAR(200),
    control_id VARCHAR(100) REFERENCES compliance_controls(id),
    ownership VARCHAR(20),  -- 'Customer', 'Microsoft', 'Shared'
    PRIMARY KEY (policy_definition_id, control_id)
);
```

### Pattern 2: Use Azure policyMetadata API to Auto-Populate
```python
import requests

# Enumerate all policy metadata for a framework
url = "https://management.azure.com/providers/Microsoft.PolicyInsights/policyMetadata"
params = {
    "api-version": "2019-10-01",
    "$filter": "properties/policyDefinitionGroupName startswith 'NIST_CSF_v2.0'"
}
```

### Pattern 3: Compliance Roll-Up via KQL
```kql
// Roll up compliance by SOC 2 control
PolicyStates
| where TimeGenerated > ago(24h)
| where PolicySetDefinitionName contains "SOC"
| summarize 
    Compliant = countif(ComplianceState == "Compliant"),
    NonCompliant = countif(ComplianceState == "NonCompliant"),
    Total = count()
  by PolicyDefinitionGroupNames, PolicyDefinitionName
| extend ComplianceRate = todouble(Compliant) / todouble(Total) * 100
| order by PolicyDefinitionGroupNames asc
```

---

## 9. Cross-Framework Equivalence Table (SOC2 ↔ NIST CSF 2.0)

Key mappings for Azure governance platform:

| SOC 2 TSC | NIST CSF 2.0 | Topic |
|-----------|-------------|-------|
| CC6.1 | PR.AA, PR.AA-01 | Logical access / identity & credentials |
| CC6.2 | PR.AA-01 | User registration / identity management |
| CC6.3 | PR.AA-01, PR.AA-05 | Access authorization / least privilege |
| CC6.6 | PR.AA-05, PR.IR-01 | External threats / network protection |
| CC6.7 | PR.DS-01, PR.DS-02 | Data in transit & at rest |
| CC6.8 | DE.CM-09, PR.PS-05 | Malware prevention / unauthorized software |
| CC7.1 | DE.CM-09, ID.RA-01 | Vulnerability detection |
| CC7.2 | DE.CM, DE.AE | System monitoring / anomaly detection |
| CC7.3, CC7.4 | RS.MA, RS.AN | Incident classification & response |
| CC7.5 | RC.RP | Incident recovery |
| CC8.1 | ID.RA-07, PR.PS-02 | Change management |
| CC9.1 | RC.RP, ID.RA | Risk mitigation / recovery planning |
| CC9.2 | GV.SC-07 | Vendor/supply chain risk |
| A1.1 | PR.IR-04 | Capacity management |
| A1.2 | RC.RP, RC.RP-04 | Backup and recovery |
| A1.3 | RC.RP-05 | Recovery testing |
| C1.1 | PR.DS-01, ID.AM-07 | Confidential data inventory |
| C1.2 | PR.DS-01 | Data disposal |

---

## 10. NIST CSF 2.0 Informative References to NIST 800-53 R5

For teams needing to bridge CSF 2.0 to 800-53 R5 (which has more Azure built-in coverage):

| CSF 2.0 | NIST 800-53 R5 |
|---------|---------------|
| PR.AA-01 | IA-2, IA-4, IA-5 |
| PR.AA-05 | AC-2, AC-3, AC-6 |
| PR.DS-01 | SC-28 |
| PR.DS-02 | SC-8 |
| DE.CM | AU-6, SI-4 |
| DE.CM-09 | SI-3, SI-4 |
| RS.CO-02 | IR-6 |
| RC.RP-04 | CP-9, CP-10 |

*(Source: NIST CPRT Informative References tool, csrc.nist.gov)*
