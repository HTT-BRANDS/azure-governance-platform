# Recommendations: Regulatory Framework Mapping Feature

**Agent**: web-puppy-d1a2ac | **Date**: March 2026  
**For**: Azure Governance Platform — regulatory framework mapping feature  
**Context**: Existing FastAPI/Python platform with `ComplianceService`, `PolicyState` model, Azure Policy sync

---

## Priority 1 — IMMEDIATE (Do This First)

### 1.1 Fix the Group Names Pipeline Gap

**The single most impactful change**: Your Azure Policy sync already retrieves `policyDefinitionGroupNames` from the API but stores them as a flattened CSV in `PolicyState.policy_category`. This loses the semantic structure needed for control mapping.

**Current code** (`app/core/sync/compliance.py` ~line 90):
```python
if state.policy_definition_group_names:
    policy_category = ",".join(state.policy_definition_group_names)
```

**Fix**: Store group names in a dedicated column and populate a control mapping table:

```python
# In app/models/compliance.py — add new column to PolicyState
class PolicyState(Base):
    # ... existing fields ...
    policy_group_names: Mapped[str | None] = Column(Text)  # JSON array of group names
    
# New junction model
class PolicyControlMapping(Base):
    __tablename__ = "policy_control_mappings"
    id: Mapped[int] = Column(Integer, primary_key=True)
    policy_definition_id: Mapped[str] = Column(String(500), index=True)
    framework: Mapped[str] = Column(String(20))       # "SOC2", "NIST_CSF_2"
    control_id: Mapped[str] = Column(String(50), index=True)  # "CC6.1", "PR.AA-01"
    tenant_id: Mapped[str] = Column(String(36))
```

**New Alembic migration needed**: `007_add_policy_control_mapping.py`

---

### 1.2 Seed the Control Registry

Create a Python module with the authoritative control data from this research:

```python
# app/data/compliance_controls.py

SOC2_CONTROLS = {
    "CC6": {
        "name": "Logical and Physical Access Controls",
        "controls": {
            "CC6.1": "Logical access security software, infrastructure, and architectures",
            "CC6.2": "Register and authorize new users before issuing credentials",
            "CC6.3": "Authorize/modify/remove access based on documented rules",
            "CC6.4": "Restrict physical access to authorized personnel",
            "CC6.5": "Discontinue protections only after data recovery capability diminished",
            "CC6.6": "Protect against threats from outside system boundaries",
            "CC6.7": "Restrict and protect transmission and movement of information",
            "CC6.8": "Prevent/detect unauthorized or malicious software",
        }
    },
    "CC7": {
        "name": "System Operations",
        "controls": {
            "CC7.1": "Detect config changes introducing vulnerabilities; monitor for CVEs",
            "CC7.2": "Monitor system components for anomalies indicative of malicious acts",
            "CC7.3": "Evaluate security events to determine if objectives are impacted",
            "CC7.4": "Execute incident response program to contain/remediate incidents",
            "CC7.5": "Identify and implement recovery activities from security incidents",
        }
    },
    "CC8": {
        "name": "Change Management",
        "controls": {
            "CC8.1": "Authorize/design/develop/test/approve/implement changes to infrastructure",
        }
    },
    "A1": {
        "name": "Availability",
        "controls": {
            "A1.1": "Maintain/monitor/evaluate processing capacity to manage demand",
            "A1.2": "Backup processes and recovery infrastructure to meet RTO/RPO",
            "A1.3": "Test recovery plan procedures supporting system recovery",
        }
    },
    # ... all CC1-CC9, C1, PI1, P1-P8 ...
}

NIST_CSF2_CONTROLS = {
    "PR.AA": {
        "name": "Identity Management, Authentication, and Access Control",
        "function": "PR",
        "subcategories": {
            "PR.AA-01": "Identities and credentials for authorized users, services, and hardware are managed",
            "PR.AA-05": "Access permissions incorporating least privilege and separation of duties are defined, managed, enforced, and reviewed",
        }
    },
    "DE.CM": {
        "name": "Continuous Monitoring",
        "function": "DE",
        "subcategories": {
            "DE.CM-03": "Personnel activity and technology usage are monitored for adverse events",
            "DE.CM-09": "Computing hardware, software, runtime environments, and data are monitored",
        }
    },
    # ... all categories and subcategories ...
}

# Azure group name → control ID mapping
AZURE_GROUP_TO_CONTROL = {
    # SOC 2
    "SOC_2_CC6.1": ("SOC2", "CC6.1"),
    "SOC_2_CC6.2": ("SOC2", "CC6.2"),
    "SOC_2_CC6.3": ("SOC2", "CC6.3"),
    "SOC_2_CC6.4": ("SOC2", "CC6.4"),
    "SOC_2_CC6.5": ("SOC2", "CC6.5"),
    "SOC_2_CC6.6": ("SOC2", "CC6.6"),
    "SOC_2_CC6.7": ("SOC2", "CC6.7"),
    "SOC_2_CC6.8": ("SOC2", "CC6.8"),
    "SOC_2_CC7.1": ("SOC2", "CC7.1"),
    "SOC_2_CC7.2": ("SOC2", "CC7.2"),
    "SOC_2_CC7.3": ("SOC2", "CC7.3"),
    "SOC_2_CC7.4": ("SOC2", "CC7.4"),
    "SOC_2_CC7.5": ("SOC2", "CC7.5"),
    "SOC_2_CC8.1": ("SOC2", "CC8.1"),
    "SOC_2_A1.1": ("SOC2", "A1.1"),
    "SOC_2_A1.2": ("SOC2", "A1.2"),
    "SOC_2_A1.3": ("SOC2", "A1.3"),
    # NIST CSF 2.0
    "NIST_CSF_v2.0_GV.OC_04": ("NIST_CSF_2", "GV.OC-04"),
    "NIST_CSF_v2.0_GV.SC_07": ("NIST_CSF_2", "GV.SC-07"),
    "NIST_CSF_v2.0_ID.AM_01": ("NIST_CSF_2", "ID.AM-01"),
    "NIST_CSF_v2.0_ID.RA_01": ("NIST_CSF_2", "ID.RA-01"),
    "NIST_CSF_v2.0_ID.RA_07": ("NIST_CSF_2", "ID.RA-07"),
    "NIST_CSF_v2.0_PR.AA": ("NIST_CSF_2", "PR.AA"),
    "NIST_CSF_v2.0_PR.AA_01": ("NIST_CSF_2", "PR.AA-01"),
    "NIST_CSF_v2.0_PR.AA_05": ("NIST_CSF_2", "PR.AA-05"),
    "NIST_CSF_v2.0_PR.DS": ("NIST_CSF_2", "PR.DS"),
    "NIST_CSF_v2.0_PR.DS_01": ("NIST_CSF_2", "PR.DS-01"),
    "NIST_CSF_v2.0_PR.DS_02": ("NIST_CSF_2", "PR.DS-02"),
    "NIST_CSF_v2.0_PR.PS_02": ("NIST_CSF_2", "PR.PS-02"),
    "NIST_CSF_v2.0_PR.PS_04": ("NIST_CSF_2", "PR.PS-04"),
    "NIST_CSF_v2.0_PR.PS_05": ("NIST_CSF_2", "PR.PS-05"),
    "NIST_CSF_v2.0_DE.CM": ("NIST_CSF_2", "DE.CM"),
    "NIST_CSF_v2.0_DE.CM_03": ("NIST_CSF_2", "DE.CM-03"),
    "NIST_CSF_v2.0_DE.CM_09": ("NIST_CSF_2", "DE.CM-09"),
    "NIST_CSF_v2.0_DE.AE": ("NIST_CSF_2", "DE.AE"),
    "NIST_CSF_v2.0_DE.AE_03": ("NIST_CSF_2", "DE.AE-03"),
    "NIST_CSF_v2.0_DE.AE_06": ("NIST_CSF_2", "DE.AE-06"),
    "NIST_CSF_v2.0_RS.CO_02": ("NIST_CSF_2", "RS.CO-02"),
    "NIST_CSF_v2.0_RS.CO_03": ("NIST_CSF_2", "RS.CO-03"),
    "NIST_CSF_v2.0_RC.RP": ("NIST_CSF_2", "RC.RP"),
    "NIST_CSF_v2.0_RC.RP_04": ("NIST_CSF_2", "RC.RP-04"),
}
```

---

## Priority 2 — SHORT-TERM (Sprint 1-2)

### 2.1 New API Endpoint: Compliance by Control

Add to `app/api/routes/compliance.py`:

```python
@router.get("/compliance/controls/{framework}")
async def get_compliance_by_control(
    framework: str,  # "SOC2" or "NIST_CSF_2"
    tenant_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Get compliance status grouped by control ID for a given framework."""
    service = ComplianceService(db)
    return await service.get_compliance_by_framework_control(framework, tenant_id)
```

### 2.2 Control Coverage Score Endpoint

```python
@router.get("/compliance/framework/{framework}/coverage")
async def get_framework_coverage(framework: str, tenant_id: str | None = None):
    """Returns % compliant per control category with control details."""
    # Returns:
    # {
    #   "framework": "SOC2",
    #   "overall_compliance": 87.3,
    #   "categories": [
    #     {
    #       "id": "CC6",
    #       "name": "Logical and Physical Access Controls",
    #       "compliance_percent": 92.1,
    #       "controls": [
    #         {"id": "CC6.1", "description": "...", "mapped_policies": 8, "compliant": 7}
    #       ]
    #     }
    #   ]
    # }
```

### 2.3 Alembic Migration

```python
# alembic/versions/008_add_compliance_framework_mapping.py

def upgrade():
    op.create_table(
        "compliance_frameworks",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version", sa.String(50)),
        sa.Column("azure_initiative_id", sa.String(200)),
        sa.Column("is_active", sa.Boolean, default=True),
    )
    
    op.create_table(
        "compliance_control_categories",
        sa.Column("id", sa.String(20), primary_key=True),   # "CC6", "PR.AA"
        sa.Column("framework_id", sa.String(50), sa.ForeignKey("compliance_frameworks.id")),
        sa.Column("name", sa.String(200)),
        sa.Column("description", sa.Text),
        sa.Column("sort_order", sa.Integer),
    )
    
    op.create_table(
        "compliance_controls",
        sa.Column("id", sa.String(50), primary_key=True),   # "CC6.1", "PR.AA-01"
        sa.Column("category_id", sa.String(20), sa.ForeignKey("compliance_control_categories.id")),
        sa.Column("azure_group_name", sa.String(200), index=True),
        sa.Column("description", sa.Text),
        sa.Column("cloud_relevance", sa.String(10)),
        sa.Column("automatable", sa.Boolean, default=True),
    )
    
    op.create_table(
        "policy_control_mappings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("policy_definition_id", sa.String(500), index=True),
        sa.Column("control_id", sa.String(50), sa.ForeignKey("compliance_controls.id"), index=True),
        sa.Column("tenant_id", sa.String(36), index=True),
        sa.UniqueConstraint("policy_definition_id", "control_id", "tenant_id"),
    )
```

---

## Priority 3 — MEDIUM-TERM (Sprint 3-4)

### 3.1 Manual Control Evidence Tracking

For controls NOT automatable via Azure Policy (CC1–CC5, GV.RM, GV.RR, GV.PO, P1–P8):

```python
class ControlEvidenceRecord(Base):
    __tablename__ = "control_evidence"
    
    id: Mapped[int] = Column(Integer, primary_key=True)
    control_id: Mapped[str] = Column(String(50))          # "CC1.1"
    tenant_id: Mapped[str] = Column(String(36))
    evidence_type: Mapped[str] = Column(String(50))       # "policy_doc", "attestation", "audit_report"
    evidence_url: Mapped[str | None] = Column(Text)
    status: Mapped[str] = Column(String(20))              # "compliant", "non_compliant", "not_applicable"
    reviewer: Mapped[str | None] = Column(String(200))
    review_date: Mapped[datetime | None] = Column(DateTime)
    next_review_date: Mapped[datetime | None] = Column(DateTime)
    notes: Mapped[str | None] = Column(Text)
```

### 3.2 Cross-Framework Mapping UI

Display a compliance heatmap showing:
- SOC 2 controls on Y axis
- NIST CSF 2.0 controls on X axis (mapped equivalents)
- Color intensity = compliance percentage
- Click through to specific Azure Policy violations

### 3.3 Compliance Report Generator

Extend `app/api/routes/exports.py` to generate:
- **SOC 2 Readiness Report** — pre-formatted for auditor review
- **NIST CSF 2.0 Profile** — current vs target profile comparison
- **Gap Analysis Report** — controls not covered by Azure built-in initiatives

---

## Priority 4 — LONG-TERM

### 4.1 Add NIST 800-53 R5 Framework
Azure has `NIST_SP_800-53_R5.json` (and `R5.1.1`) built-in — with much broader control coverage than CSF 2.0. Add as third framework option.

### 4.2 Framework Version Management
When AICPA or NIST releases updates:
```python
# Version tracking with migration support
def migrate_control_mapping(old_framework_id: str, new_framework_id: str, mapping_table: dict):
    """Migrate existing compliance data to new framework version."""
    pass
```

### 4.3 Azure policyMetadata API Integration
Fetch control ownership metadata directly:
```python
async def fetch_control_ownership(group_name: str) -> str:
    """Returns 'Customer', 'Microsoft', or 'Shared'."""
    url = f"https://management.azure.com/providers/Microsoft.PolicyInsights/policyMetadata/{group_name}"
    # Returns owner field from metadata
```

---

## Implementation Checklist

### Phase 1 (Immediate)
- [ ] Create Alembic migration `008_add_compliance_framework_mapping.py`
- [ ] Create `app/data/compliance_controls.py` with SOC2 + NIST CSF 2.0 static data
- [ ] Update compliance sync to populate `policy_control_mappings` table
- [ ] Add `azure_group_name` parsing to extract control IDs from group name strings

### Phase 2 (Sprint 1-2)
- [ ] Add `ComplianceControl` model and `PolicyControlMapping` model
- [ ] Add `get_compliance_by_framework_control()` to `ComplianceService`
- [ ] Add `/compliance/controls/{framework}` API endpoint
- [ ] Add `/compliance/framework/{framework}/coverage` API endpoint
- [ ] Add caching for new endpoints (`@cached("compliance_by_control")`)
- [ ] Write unit tests for control ID parsing logic

### Phase 3 (Sprint 3-4)
- [ ] Add `ControlEvidenceRecord` model for manual controls
- [ ] Add evidence management API routes
- [ ] Extend exports to generate SOC 2 readiness report
- [ ] Add NIST CSF 2.0 profile comparison view

---

## Critical Warnings

⚠️ **SOC 2 is NOT free to redistribute**: The full AICPA TSC document requires purchase/membership. Your application can reference control IDs and brief descriptions (fair use for technical implementation) but should NOT reproduce the full points of focus verbatim.

⚠️ **Microsoft's mappings ≠ AICPA certification**: Compliance with Azure's SOC 2 built-in policy initiative does NOT constitute SOC 2 certification. The built-in initiative covers a subset of controls; auditor judgment and manual evidence are still required.

⚠️ **CSF 2.0 subcategory notation**: NIST uses hyphen notation (`PR.AA-01`) but Azure uses underscore (`PR.AA_01`). Always normalize when comparing across systems.

⚠️ **Azure Policy group names are case-sensitive**: `SOC_2_CC6.1` ≠ `soc_2_cc6.1`. Your parsing code must handle exact case matching.

---

## Mapping Confidence Assessment

| Control Set | Confidence | Basis |
|------------|------------|-------|
| CC6.1–CC6.8 descriptions | ✅ HIGH | AICPA TSC authoritative text |
| CC7.1–CC7.5 descriptions | ✅ HIGH | AICPA TSC authoritative text |
| CC8.1 description | ✅ HIGH | AICPA TSC authoritative text |
| A1.1–A1.3 descriptions | ✅ HIGH | AICPA TSC authoritative text |
| Azure SOC 2 group names | ✅ HIGH | Confirmed from SOC_2.json source |
| NIST CSF 2.0 function/category names | ✅ HIGH | NIST CSWP 29 + CPRT |
| Azure NIST CSF 2.0 group names | ✅ HIGH | Confirmed from NIST_CSF_v2.0.json v1.5.0 |
| Cross-framework SOC2↔NIST mappings | ⚠️ MEDIUM | Based on NIST CPRT informative references; not official AICPA mapping |
| Manual control completeness (CC1-CC5) | ⚠️ MEDIUM | Descriptions from training data; verify against AICPA purchase |
