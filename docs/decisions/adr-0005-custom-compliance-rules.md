---
status: proposed
date: 2026-03-19
decision-makers: Solutions Architect 🏛️, Security Auditor 🛡️, Pack Leader 🐺
consulted: Web Puppy 🕵️ (research), Experience Architect 🎨 (API contracts)
informed: All Code Puppy agents, MSP administrators
relates-to: CM-002
---

# Use JSON Schema rule definitions for custom compliance rule engine

## Context and Problem Statement

The Azure Governance Platform currently evaluates compliance by syncing Azure Policy state into `ComplianceSnapshot` and `PolicyState` models, and tracks Riverside-specific compliance via `RiversideCompliance` and `RiversideMFA` models. MSP administrators managing 5 tenants want to define **custom compliance rules beyond what Azure Policy provides** — for example, enforcing organisation-specific naming conventions, minimum MFA coverage thresholds, compliance score floors, approved resource SKUs, and required tag sets.

These custom rules must be:
- Defined by tenant administrators (untrusted input in a multi-tenant context)
- Evaluated against resource properties, compliance scores, and MFA coverage data
- Integrated into the existing sync pipeline and exposed via the compliance API
- Secure against injection, sandbox escape, and cross-tenant data leakage

How should the custom compliance rule definition and evaluation system be designed?

## Decision Drivers

- **Security (K.O. criterion)**: Rules authored by tenant admins in a multi-tenant SaaS platform must not create injection vectors — a single compromised rule must not affect other tenants or the host process
- **Expressiveness**: Must cover three rule categories: `resource_property` checks, `compliance_score` thresholds, and `mfa_coverage` requirements
- **Auditability**: Rule definitions must be stored, versioned, and auditable with full change history
- **Implementation velocity**: Must integrate with existing FastAPI + SQLAlchemy stack in 1–2 sprints
- **Compatibility**: Must work alongside existing `ComplianceSnapshot`, `PolicyState`, `RiversideCompliance`, and `RiversideMFA` models without disruption
- **Tenant isolation**: Rules scoped per tenant; no cross-tenant rule visibility or evaluation side effects

## Considered Options

1. **JSON Schema rule definitions stored in DB** — declarative JSON describing what resource/compliance properties must match, evaluated via the `jsonschema` library (no code execution)
2. **Python expression evaluator** (`simpleeval` / `ast.literal_eval`) — tenant-authored Python expressions evaluated at runtime for richer conditions
3. **Azure Policy definition language clone** — full reimplementation of Azure Policy's condition language with 11 effects, 20+ operators, resource alias system

## Decision Outcome

**Chosen option: "JSON Schema rule definitions stored in DB"**, because it is the only option that satisfies the security K.O. criterion while meeting expressiveness requirements for the three target rule categories, at low implementation cost within the existing stack.

Option 2 is **eliminated** due to CVE-2026-32640 (CVSS 8.7/10 HIGH) — a live sandbox escape vulnerability in `simpleeval` that enables remote code execution through object attribute chain traversal. In a multi-tenant compliance platform holding Azure credentials and Key Vault references, this is an existential risk.

Option 3 is **deferred** — full reimplementation of Azure Policy's definition language is estimated at 6–18 months and creates a competing system to the native Azure Policy state already synced by this platform.

### Rule Categories and Schema Design

Custom rules are organized into three categories, each with a defined evaluation context:

#### Category 1: `resource_property`

Evaluates Azure resource properties synced from the Resource model.

```json
{
  "rule_name": "storage-https-only",
  "category": "resource_property",
  "resource_type": "Microsoft.Storage/storageAccounts",
  "severity": "High",
  "effect": "audit",
  "schema": {
    "type": "object",
    "properties": {
      "supportsHttpsTrafficOnly": { "const": true }
    },
    "required": ["supportsHttpsTrafficOnly"]
  }
}
```

#### Category 2: `compliance_score`

Evaluates against `ComplianceSnapshot` or `RiversideCompliance` data.

```json
{
  "rule_name": "minimum-compliance-score",
  "category": "compliance_score",
  "severity": "High",
  "effect": "audit",
  "schema": {
    "type": "object",
    "properties": {
      "overall_compliance_percent": { "type": "number", "minimum": 80 },
      "non_compliant_resources": { "type": "integer", "maximum": 10 }
    },
    "required": ["overall_compliance_percent"]
  }
}
```

#### Category 3: `mfa_coverage`

Evaluates against `RiversideMFA` data.

```json
{
  "rule_name": "admin-mfa-required",
  "category": "mfa_coverage",
  "severity": "Critical",
  "effect": "audit",
  "schema": {
    "type": "object",
    "properties": {
      "admin_mfa_percentage": { "type": "number", "minimum": 100 },
      "mfa_coverage_percentage": { "type": "number", "minimum": 90 }
    },
    "required": ["admin_mfa_percentage", "mfa_coverage_percentage"]
  }
}
```

### Database Model

```python
class CustomComplianceRule(Base):
    """Custom compliance rule definitions using JSON Schema."""
    __tablename__ = "custom_compliance_rules"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    rule_name: Mapped[str] = Column(String(255), nullable=False)
    rule_description: Mapped[str | None] = Column(Text)
    category: Mapped[str] = Column(
        String(50), nullable=False
    )  # resource_property | compliance_score | mfa_coverage
    resource_type: Mapped[str | None] = Column(String(255))  # For resource_property rules
    severity: Mapped[str] = Column(String(20), nullable=False, default="Medium")
    effect: Mapped[str] = Column(String(20), nullable=False, default="audit")
    schema: Mapped[dict] = Column(JSONB, nullable=False)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_by: Mapped[str] = Column(String(255), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### Integration Points

**API Endpoints** (under `/api/v1/compliance/rules`):

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/compliance/rules` | List rules for tenant (filtered by `tenant_id` via authz) |
| `POST` | `/api/v1/compliance/rules` | Create rule (validates schema, enforces security limits) |
| `GET` | `/api/v1/compliance/rules/{id}` | Get rule details |
| `PUT` | `/api/v1/compliance/rules/{id}` | Update rule (re-validates schema) |
| `DELETE` | `/api/v1/compliance/rules/{id}` | Soft-delete rule |
| `POST` | `/api/v1/compliance/rules/{id}/evaluate` | Dry-run evaluation against current data |

**Sync Pipeline Integration**: Rules are evaluated during each compliance sync cycle. The `ComplianceService` is extended with a `evaluate_custom_rules(tenant_id)` method that:

1. Loads all active rules for the tenant
2. Determines the evaluation context per rule category:
   - `resource_property` → resource properties from latest sync
   - `compliance_score` → latest `ComplianceSnapshot` data
   - `mfa_coverage` → latest `RiversideMFA` data
3. Validates context data against each rule's JSON Schema
4. Stores violations as `CustomRuleViolation` records
5. Violations surface in the existing compliance summary and non-compliant policies views

### Security Guards

The `JsonSchemaRuleEngine` enforces these security constraints:

1. **No remote `$ref` resolution** — prevents SSRF via schema loading
2. **Schema size limit: 64KB** — prevents memory exhaustion
3. **Regex pattern length limit: 500 chars** — prevents ReDoS
4. **Schema nesting depth limit: 10 levels** — prevents deep recursion
5. **Validator caching per rule_id** — prevents recompilation DoS
6. **Format checking disabled** — removes attack surface from format validators
7. **Input sanitization** — rule names/descriptions sanitized for XSS prevention

### Consequences

**Good:**
- No code execution path in the rule evaluation pipeline — eliminates entire class of injection vulnerabilities
- Rule definitions are pure JSON data — storable in PostgreSQL JSONB, renderable in UI, version-trackable
- `jsonschema` library is mature (MIT license, zero known CVEs, Python 3.10–3.14 support)
- Covers all three required rule categories (`resource_property`, `compliance_score`, `mfa_coverage`)
- Natural integration with existing compliance models via tenant_id FK
- 1–2 sprint implementation timeline
- Multi-tenant isolation is trivially enforced via `tenant_id` foreign key and existing `TenantAuthorization` middleware

**Bad:**
- Cannot express cross-property comparisons (e.g., `fieldA >= fieldB`)
- Cannot express date arithmetic (e.g., `expiryDate > now() + 30d`)
- No built-in effect system — audit/deny semantics must be wrapped externally
- ~20% of conceivable governance rules may require a future upgrade to OPA/Rego

**Neutral:**
- JSON Schema is well-known but some administrators may prefer a simpler DSL for common rules — mitigated by providing rule templates and a UI builder

### Confirmation

This decision is confirmed when:
1. `custom_compliance_rules` table exists with `tenant_id`, `category`, `schema` (JSONB) columns
2. `JsonSchemaRuleEngine.evaluate()` passes all unit tests including tenant isolation tests
3. Security review confirms no code execution path in the validation pipeline
4. Remote `$ref` resolution is disabled (confirmed by fitness function)
5. Schema size and pattern length limits enforced (confirmed by fitness function)
6. Rules are evaluated during sync runs and results visible via `/api/v1/compliance/rules`

## STRIDE Security Analysis

| Threat Category | Risk Level | Mitigation |
|-----------------|-----------|------------|
| **Spoofing** | Low | Rules stored with `tenant_id` FK; RBAC limits rule creation to MSP administrators; Azure AD authentication required on all `/api/v1/compliance/rules` endpoints via existing `get_current_user` dependency |
| **Tampering** | Low | DB integrity constraints on `custom_compliance_rules` table; JSON Schema validated on write via `Draft202012Validator.check_schema()`; all mutations logged to `audit_log` table with `created_by` field |
| **Repudiation** | Low | All rule CRUD operations logged to `audit_log` with user ID, timestamp, and action; evaluation results timestamped with `evaluated_at`; `updated_at` column tracks modifications |
| **Information Disclosure** | Low | Tenant isolation enforced at DB level via `tenant_id` FK and existing `TenantAuthorization` middleware (same pattern as `ComplianceService`); no cross-tenant rule visibility in any query |
| **Denial of Service** | Medium | Schema size limit (64KB), regex pattern length limit (500 chars), validator caching prevents recompilation, rate limiting on evaluation endpoint; max schema nesting depth (10 levels) prevents deep recursion |
| **Elevation of Privilege** | **None** | **JSON Schema evaluation has no code execution model.** The `jsonschema` library processes schemas as pure data — there is no interpreter, sandbox, or execution environment to escape. This is the fundamental security advantage over Option 2. |

**Overall Security Posture**: This decision introduces **no new code execution attack surfaces**. The only new attack vectors are standard data-handling concerns (DoS via large schemas, ReDoS via regex patterns) which are mitigated by explicit size and length limits. Compared to Option 2, which carries CVE-2026-32640 (CVSS 8.7, RCE via sandbox escape), this approach reduces the rule engine's security risk from **Critical** to **Low**.

**Key CVE Evidence (Option 2 elimination)**:
- `CVE-2026-32640` / `GHSA-44vg-5wv2-h2hg`: simpleeval sandbox escape, CVSS v4 8.7/10, AV:Network/AC:Low/PR:None/UI:None, CWE-94 Code Injection — affects all versions < 1.0.5
- Recurring pattern: simpleeval GitHub issues #81 (2023), #154 (2024), #166 (2025), #171 (2026)
- `ast.literal_eval`: Python 3.14.3 docs explicitly state *"calling it on untrusted data is thus not recommended"*; confirmed DoS via memory/C-stack exhaustion

## Pros and Cons of the Options

### Option A — JSON Schema Rule Definitions (selected)

*Declarative JSON Schema stored as JSONB in PostgreSQL, evaluated via `jsonschema` library with security guards.*

- Good, because **no code execution** — zero injection attack surface by design
- Good, because **DB-native** — JSONB storage in existing PostgreSQL, versionable, auditable
- Good, because **covers all three rule categories** — `resource_property`, `compliance_score`, `mfa_coverage`
- Good, because **low implementation cost** — 1–2 sprints within existing FastAPI/SQLAlchemy stack
- Good, because **multi-tenant safe by design** — `tenant_id` FK, no shared evaluation state
- Good, because **JSON Schema is a stable, widely-understood standard** (Draft 2020-12)
- Good, because **`iter_errors()` returns all violations** — not just the first match
- Neutral, because security guards are needed — must disable remote `$ref`, enforce size/pattern limits
- Bad, because **cannot express cross-property comparisons** (e.g., `retentionDays >= backupFrequencyDays`)
- Bad, because **no date arithmetic** — cannot express time-relative rules
- Bad, because **~20% expressiveness gap** — future upgrade to OPA/Rego may be needed

### Option B — Python Expression Evaluator (eliminated)

*Tenant-authored Python expressions evaluated by `simpleeval` or `ast.literal_eval` at compliance check time.*

- Good, because high expressiveness — arbitrary expressions cover all rule scenarios
- Bad, because **CVE-2026-32640 (CVSS 8.7 HIGH)** — active sandbox escape enabling RCE via attribute chain traversal to `os`/`sys`. Network-exploitable, zero-auth, zero-interaction.
- Bad, because **ast.literal_eval is too limited** — cannot evaluate comparison operators; Python docs say unsafe on untrusted input
- Bad, because **recurring security pattern** — 4 sandbox escape issues in 4 consecutive years
- Bad, because **compliance SaaS context amplifies risk** — platform holds Azure credentials and Key Vault references; sandbox escape = full compromise

**This option is eliminated by the security K.O. criterion.**

### Option C — Azure Policy Definition Language Clone (deferred)

*Full reimplementation of Azure Policy's condition language: 11 effects, 20+ operators, resource alias system, parameter interpolation.*

- Good, because 100% Azure Policy compatibility
- Good, because familiar to Azure administrators
- Good, because declarative (no code execution if implemented correctly)
- Bad, because **6–18 month engineering effort** for production-quality implementation
- Bad, because **11 complex effects** with distinct pre-conditions and evaluation semantics
- Bad, because **100+ resource aliases** require a maintained registry
- Bad, because **competes with native Azure Policy** — this platform already syncs Azure Policy state
- Bad, because **ongoing maintenance burden** — must track Azure Policy language changes

**This option is deferred. If full Azure Policy compatibility becomes required, OPA/Rego is a better foundation than building from scratch.**

## Fitness Functions

The following automated tests enforce this ADR. They are located in `tests/architecture/test_fitness_functions.py`:

### FF-1: No code execution in compliance rule evaluation

```python
def test_no_code_execution_in_rule_engine():
    """ADR-0005 FF-1: Custom compliance rules must not execute code.

    Verify that the rule engine module does not import any code execution
    libraries (eval, exec, subprocess, simpleeval, ast.literal_eval for
    untrusted input).
    """
    rule_engine_files = list(Path("app").rglob("*rule*engine*.py"))
    rule_service_files = list(Path("app").rglob("*compliance*rule*.py"))
    all_files = rule_engine_files + rule_service_files

    banned_imports = {"simpleeval", "subprocess", "os.system", "exec", "eval"}
    banned_calls = {"eval(", "exec(", "compile(", "ast.literal_eval("}

    for filepath in all_files:
        content = filepath.read_text()
        for banned in banned_imports:
            assert banned not in content, (
                f"ADR-0005 violation: {filepath} imports banned module '{banned}'. "
                f"Custom compliance rules must use JSON Schema only (no code execution)."
            )
        for banned_call in banned_calls:
            assert banned_call not in content, (
                f"ADR-0005 violation: {filepath} calls '{banned_call}'. "
                f"Custom compliance rules must use JSON Schema only (no code execution)."
            )
```

### FF-2: Custom rules require tenant isolation

```python
def test_custom_rules_require_tenant_id():
    """ADR-0005 FF-2: Custom compliance rule model must enforce tenant isolation.

    The CustomComplianceRule model must have a tenant_id FK column to ensure
    multi-tenant isolation.
    """
    model_file = Path("app/models/compliance.py")
    if not model_file.exists():
        pytest.skip("compliance model not yet created")

    content = model_file.read_text()
    if "CustomComplianceRule" in content:
        assert "tenant_id" in content, (
            "ADR-0005 violation: CustomComplianceRule model must have tenant_id column "
            "for multi-tenant isolation."
        )
        assert "ForeignKey" in content and "tenants.id" in content, (
            "ADR-0005 violation: tenant_id must be a ForeignKey to tenants.id."
        )
```

### FF-3: No remote $ref in schema validation

```python
def test_no_remote_ref_in_rule_schemas():
    """ADR-0005 FF-3: Rule engine must block remote $ref URLs (SSRF prevention).

    Any file implementing rule schema validation must contain logic to
    reject remote $ref references (http://, https://).
    """
    rule_files = list(Path("app").rglob("*rule*engine*.py"))
    if not rule_files:
        pytest.skip("rule engine not yet implemented")

    for filepath in rule_files:
        content = filepath.read_text()
        assert "http://" in content or "$ref" in content, (
            f"ADR-0005 violation: {filepath} must check for and reject remote $ref URLs "
            f"to prevent SSRF attacks."
        )
```

### FF-4: Compliance rules API requires authentication

```python
def test_compliance_rules_api_requires_auth():
    """ADR-0005 FF-4: /api/v1/compliance/rules endpoints must require authentication.

    The rules router must include get_current_user dependency at router level
    or on every route.
    """
    rules_route = Path("app/api/routes/compliance.py")
    if not rules_route.exists():
        pytest.skip("compliance routes not found")

    content = rules_route.read_text()
    if "/rules" in content or "custom_rule" in content:
        assert "get_current_user" in content, (
            "ADR-0005 violation: Compliance rules endpoints must require authentication "
            "via Depends(get_current_user)."
        )
```

## More Information

**Relates to:** CM-002 (Custom Compliance Rule Engine)

**Research Package:** [`research/compliance-rule-engine-adr/`](../../research/compliance-rule-engine-adr/) — full evidence including:
- CVE-2026-32640 details and CVSS metrics
- JSON Schema performance benchmarks (5,000 validations/sec)
- Azure Policy definition structure analysis (11 effects, 20+ operators)
- OPA/Rego evaluation as future extension path
- Source credibility assessments and bibliography

**Key References:**
- CVE-2026-32640: https://nvd.nist.gov/vuln/detail/CVE-2026-32640
- GHSA-44vg-5wv2-h2hg: https://github.com/advisories/GHSA-44vg-5wv2-h2hg
- Python `ast.literal_eval` docs: https://docs.python.org/3/library/ast.html#ast.literal_eval
- Azure Policy definition structure: https://learn.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure-basics
- jsonschema library: https://python-jsonschema.readthedocs.io/en/stable/
- OPA Policy Language: https://www.openpolicyagent.org/docs/policy-language

**Related ADRs:**
- [ADR-0001: Multi-agent architecture](adr-0001-multi-agent-architecture.md) — agents that will implement this
- [ADR-0004: Research-first protocol](adr-0004-research-first-protocol.md) — research methodology used

**Related Code:**
- `app/models/compliance.py` — existing `ComplianceSnapshot`, `PolicyState` models
- `app/api/services/compliance_service.py` — existing compliance evaluation service
- `app/api/services/riverside_compliance.py` — MFA gap analysis functions
- `app/api/routes/compliance.py` — existing `/api/v1/compliance/*` routes

**Future Evolution:**
- If >20% of rule requests require expressions not possible in JSON Schema (cross-property, date arithmetic), evaluate OPA/Rego as a complementary engine
- Consider `cel-python` (Common Expression Language) as an intermediate option for mathematical comparisons without injection risk

**Review History:**
- 2026-03-19: Initial ADR proposed by Solutions Architect 🏛️ (`solutions-architect-1d4b5d`)
- Research conducted by: Web Puppy 🕵️
- Pending review: Security Auditor 🛡️ (STRIDE co-sign), Pack Leader 🐺 (sign-off)

---

**ADR Status:** Proposed
**Implementation Status:** ⏳ Pending (CM-002)
**Last Updated:** March 19, 2026
**Maintained By:** Solutions Architect 🏛️
