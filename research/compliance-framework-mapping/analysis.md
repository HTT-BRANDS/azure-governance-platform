# Multi-Dimensional Analysis — Compliance Framework Mapping

---

## Security Analysis

### Risk: Hardcoded Compliance Mappings
**Threat**: If mappings are embedded in code, a compromised developer with code access
can silently alter which findings map to which controls — and the change goes undetected
without explicit code review.

**Mitigation**: Store mappings in YAML files under Git with:
- Mandatory PR review policy for `compliance/` directory
- CODEOWNERS file requiring compliance team sign-off
- Audit log of all changes (Git history)

### Risk: Stale Framework Versions
**Threat**: SOC 2 and NIST update their frameworks. If the platform only supports
hardcoded versions, findings may map to deprecated controls, causing audit failures.

**Mitigation**: Version-aware framework IDs (`SOC2_2017`, `NIST_CSF_2.0`) with
explicit sunset/transition dates in framework metadata.

### Risk: Many-to-Many Mapping Drift
**Threat**: A security check maps to CC6.1 but an auditor's template expects CC6.7.
Incorrect mappings create false compliance attestations.

**Mitigation**: Source framework files from authoritative sources (AICPA, NIST) and
validate mappings against official control guidance. Add "rationale" field to mappings.

---

## Cost Analysis

### Static YAML Files
- **Storage cost**: Near zero (text files)
- **Infrastructure cost**: None (no separate service)
- **Maintenance cost**: Low (framework updates ~1-2x/year)
- **Migration cost**: None

### Database Records
- **Storage cost**: Negligible (thousands of rows at most)
- **Infrastructure cost**: Zero marginal (reuses existing DB)
- **Maintenance cost**: Medium (schema migrations on framework updates)
- **Migration cost**: Low if designed well (version field in schema)

### Third-Party GRC Platform (e.g., Vanta, Drata)
- **License cost**: $10k–$100k+/year depending on scale
- **Infrastructure cost**: Included
- **Maintenance cost**: Low (vendor-managed)
- **Lock-in cost**: High (proprietary APIs, data export limitations)

**Recommendation**: Start with YAML + database seed. Avoid third-party GRC lock-in
for core framework data; use for workflow/evidence management only.

---

## Implementation Complexity Analysis

### Option A: Static YAML (Simplest)
- **Effort**: Low — 1-3 days to define schema, populate 2-3 frameworks
- **Dependencies**: PyYAML or similar; zero new infrastructure
- **Learning curve**: None (YAML is universally understood)
- **Risk**: Medium — no query optimization; fine at small scale (<10 frameworks, <500 checks)

### Option B: Database-Seeded from YAML (Recommended)
- **Effort**: Medium — 3-7 days for schema design, seed scripts, seed data
- **Dependencies**: Existing ORM (Django/SQLAlchemy/Prisma); existing DB
- **Learning curve**: Low (standard ORM patterns)
- **Risk**: Low — established pattern, supports rich queries for compliance dashboards

### Option C: Prowler-style Multi-JSON
- **Effort**: Medium — same as YAML but JSON files per framework
- **Dependencies**: None new
- **Risk**: Low for tools; Medium for SaaS (file management gets complex >10 frameworks)

### Option D: OPA/Rego Policy Engine
- **Effort**: High — 2-4 weeks; requires OPA expertise
- **Dependencies**: OPA server or library (new infrastructure)
- **Learning curve**: High (Rego is a specialized language)
- **Risk**: High for small teams; appropriate for enterprise-scale compliance engines

---

## Stability Analysis

### Framework Stability

| Framework | Update Frequency | Current Version | Last Major Change |
|-----------|-----------------|-----------------|-------------------|
| SOC 2 TSC | Low (~5 years) | 2017 (rev. 2022) | 2022 (Points of Focus update) |
| NIST CSF | Low (~5-8 years) | 2.0 (Feb 2024) | 2024 (major restructure) |
| NIST 800-53 | Low (~4 years) | Rev 5 (2020) | 2020 |
| CIS Benchmarks | High (annually) | Varies by service | 2024-2025 |
| PCI DSS | Medium (~3 years) | v4.0 (Mar 2022) | 2022 |

**Implication**: SOC 2 and NIST CSF are very stable — design the schema to handle
annual CIS Benchmark updates as the stress test.

### Tool Stability
- **Prowler**: Active development, 13.4k stars — high stability signal
- **Chef InSpec**: Progress Chef maintains; mature, stable (v7.0)
- **AWS Security Hub**: AWS-managed — extremely stable but opaque
- **Azure MDC**: Microsoft-managed — stable but changes with Azure policy engine

---

## Optimization Analysis

### Performance Considerations for Compliance SaaS

**Read Pattern**: For each security finding, look up which frameworks/controls it maps to.
This is a hot path (called for every finding on every scan).

**Caching Strategy**:
```
1. Load framework YAML files at application startup → cache in memory
2. OR seed into DB on deploy → query at runtime (slower but fresher)
3. Best: both — YAML as source of truth, DB as query layer, memory cache for hot paths
```

**Query Optimization**:
```sql
-- Index on check_id for fast mapping lookup
CREATE INDEX idx_check_mappings_check_id ON check_framework_mappings(check_id);

-- Composite index for framework-specific queries
CREATE INDEX idx_check_mappings_framework ON check_framework_mappings(framework_id, control_id);
```

**Scale Estimate** (for sizing):
- SOC 2: 33 CC controls + 3 A controls = 36 controls
- NIST CSF 2.0: 106 subcategories
- NIST 800-53: ~1,000 controls (with enhancements)
- CIS per service: ~50-200 controls
- **Total across 10 frameworks**: ~2,000-5,000 records — trivially small for any DB

---

## Compatibility Analysis

### With Existing Tech Stack
*Note: Run `list_files` on project root to get actual stack; this is framework-neutral.*

| Technology | Compatibility with YAML Approach |
|-----------|----------------------------------|
| Django (Python) | ✅ Native YAML support via PyYAML; management commands for seeding |
| FastAPI (Python) | ✅ Same as Django |
| Node.js/TypeScript | ✅ js-yaml, native JSON |
| Ruby on Rails | ✅ Native YAML (Rails config uses YAML by default) |
| PostgreSQL | ✅ JSONB column for flexible storage; or relational tables |
| SQLite | ✅ JSON support in modern SQLite |

### With Audit/Compliance Tooling
- **Vanta/Drata**: Import CSV/JSON mappings; YAML + conversion script works
- **Tugboat Logic**: Custom evidence upload; YAML-sourced exports work
- **ServiceNow GRC**: XML/JSON import; convert from YAML
- **OpenSCAP**: XCCDF — separate conversion step needed if targeting SCAP

---

## Maintenance Analysis

### Framework Update Workflow

When NIST releases CSF 3.0 (hypothetical):
1. Create `config/frameworks/nist_csf_3.0.yaml` — new file, doesn't touch 2.0
2. Create DB migration to add new framework records
3. Map existing checks to new control IDs via PR (reviewed, audited)
4. Retain `nist_csf_2.0.yaml` for backwards compatibility
5. Add `deprecated_at` field to 2.0 framework record when appropriate
6. Update compliance reports to show which version was used

**Estimated maintenance effort per framework update**: 1-3 days (mostly mapping review)

### Deprecation Policy Recommendation
```yaml
framework:
  id: NIST_CSF_1.1
  name: "NIST Cybersecurity Framework"
  version: "1.1"
  published: "2018-04-16"
  deprecated_at: "2025-12-31"    # sunset date
  superseded_by: NIST_CSF_2.0
  active: false
```

---

## Summary Matrix

| Criterion | Static YAML | DB-Seeded YAML | Hardcoded Code | OPA/Rego |
|-----------|------------|----------------|----------------|----------|
| Security (audit trail) | ✅ Git | ✅ Git + DB | ❌ Code review only | ✅ Git |
| Cost | ✅ Zero | ✅ Minimal | ✅ Zero | ⚠️ OPA infra |
| Complexity | ✅ Low | ✅ Medium | ✅ Low | ❌ High |
| Stability | ✅ High | ✅ High | ⚠️ Fragile | ✅ High |
| Performance | ⚠️ File I/O | ✅ DB queries | ✅ In-memory | ✅ OPA cache |
| Compatibility | ✅ Universal | ✅ Universal | ⚠️ Tied to language | ⚠️ Rego-specific |
| Maintenance | ✅ Easy | ✅ Easy | ❌ Code deploy | ⚠️ Rego expertise |
| **VERDICT** | ✅ Good for MVP | ✅ **Recommended** | ❌ Anti-pattern | ⚠️ Scale only |
