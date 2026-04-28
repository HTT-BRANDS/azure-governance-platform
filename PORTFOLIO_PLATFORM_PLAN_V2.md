# HTT Portfolio Platform — Strategic Plan V2

**Authors:** Richard (code-puppy-ab8d6a) — synthesized from cross-repo audit and adversarial review
**Audience:** Tyler Granlund, then planning-agent for execution decomposition
**Date:** 2026-04-28
**Status:** DRAFT V2 — supersedes V1, incorporates redteam findings, ready for planning-agent

**Predecessor documents (preserved as historical record):**
- [`CONTROL_TOWER_MASTERMIND_PLAN_2026.md`](./CONTROL_TOWER_MASTERMIND_PLAN_2026.md) — V1 draft
- [`CONTROL_TOWER_MASTERMIND_PLAN_2026_REDTEAM.md`](./CONTROL_TOWER_MASTERMIND_PLAN_2026_REDTEAM.md) — adversarial review by epistemic-architect

> **Working-title-neutral filename**: V1 used "Control Tower" as both
> framing and identity. V2 separates the *concept* (a portfolio platform)
> from the *name* (TBD per the naming exercise in §11). Filename will be
> renamed when the naming decision lands in Phase 3 prep.

---

## What changed from V1

| Item | V1 stance | V2 stance |
|---|---|---|
| Brand name | "Control Tower" (final) | TBD — 5 candidates evaluated, decision deferred to Phase 3 prep |
| Riverside framing | "Riverside compliance theater" | "HTT-built platform for HTT use; Riverside is one consumer of evidence" |
| Phase 1 / Phase 2 ordering | File splits → DDD extraction (sequential) | Hybrid: domain boundaries on paper → splits along those lines → relocation |
| Phase 0.5 | Not present | New: continuity / bus-factor / runbook track |
| Cost ceiling | "<$100/mo" hard cap | Phased: $53 → $80 → $150 → $300–400/mo per phase |
| CIEM (B2B governance) | Build from scratch | Decision D8 added: build vs Microsoft Entra Permissions Management vs hybrid |
| WIGGUM_ROADMAP relationship | Not addressed | Decision D9 added: supplement vs replace vs coexist |
| AI layer (`/ask` only) | V1 had only read | V2 adds `/act` agentic-ops with guardrails |
| DPIA / data classification | Absent | Per-domain `DATA_CLASSIFICATION.md` artifact required |
| SBOM / SLSA on platform itself | Implicit (already done in `7mk8`) | Explicit acknowledgment + extension |
| Success metrics | Vague ("Tyler walks in and wins") | Quantitative per-phase targets (TTBO, MTTD, $-saved-attributed) |
| Bridge sunset criteria | Absent | Each Phase 4 bridge has written kill-condition |
| Phase 4 bridges | One serial phase | 5 parallel tracks with explicit `httbi-before-DART` ordering |
| Ownership framing | "Tyler walks in and wins" | "HTT Brands has built X; Tyler is lead engineer" |

---

## 1. The Problem We're Solving

HTT Brands operates a multi-brand portfolio (HTT, BCC, FN, TLL, DCE) with
five separate engineering surfaces — Azure governance, AWS BI for salon
ops, Azure SQL data layer, M365 hub-and-spoke template, and a predecessor
governance platform. Each surface solves a real problem; together they
form an unintentional platform-of-platforms with no shared brand, no
shared ergonomics, and no executive-visible value story.

Riverside (HTT's PE owner) currently receives quarterly portfolio
read-outs assembled manually from each surface. The opportunity is to
build a single internal platform where:

- **Cost** across Azure direct, AWS, M365/Pax8, and SaaS subscriptions is
  reconciled and attributable to brand/RG/resource/tag.
- **Identity** across five Entra tenants is observable as a graph, with
  cross-tenant grants tracked, time-bounded, and auditable.
- **Compliance** is continuous (policy-as-code + automated evidence),
  not point-in-time slide decks.
- **Resources** are inventoried and right-sized portfolio-wide.
- **BI** from each brand's data products (DART, `httbi`) is reachable
  through a single read-only query layer for cross-brand analysis.
- **Lifecycle** for new brand acquisitions is a parameterized playbook,
  not a 90-day engineering project.

This is an internal platform. HTT Brands owns it. Tyler is the lead
engineer. Riverside is one of many consumers (the others being HTT IT,
brand operators, MSP partners, and acquired-brand onboarding teams).

---

## 2. The Five-Repo Audit (V2: ownership-clarified)

| Repo | Cloud | Purpose | Ownership | Relationship to V2 plan |
|---|---|---|---|---|
| `azure-governance-platform` | Azure | Multi-tenant cost/identity/compliance hub | HTT Brands | Becomes the unified platform host |
| `control-tower` (predecessor) | Azure | 44 collectors, persona dashboards | HTT Brands | Archive; cherry-pick IP forward |
| `DART` | AWS | Salon ops BI for contractors | HTT Brands | Federate via bi_bridge; remains independent product |
| `bi-migration-agent` | Azure | SQL VM → Azure SQL migration | HTT Brands | Sunset on completion; produces `httbi` data product |
| `DeltaSetup` | M365 | Hub-and-spoke SharePoint template | HTT Brands | Becomes parameterized lifecycle playbook |

**Ownership note:** All five repos are HTT Brands assets. This plan
proposes engineering work *inside* HTT-owned repositories using
HTT-owned infrastructure. The platform's IP, brand, and operational
artifacts are HTT property. Tyler's role is lead engineer; the platform
is HTT's.

---

## 3. Mission / Vision / Values (V2: neutral framing)

### Mission
Make operational truth, cost truth, identity truth, and compliance truth
visible and queryable across HTT Brands' multi-brand portfolio in a
single internal platform.

### Vision (3-year)
HTT Brands operates a unified internal platform that turns brand
acquisition into a configuration step, makes portfolio cost attribution
microscope-and-telescope queryable, and produces continuous compliance
evidence rather than point-in-time read-outs.

### Values
1. **Receipts.** Every claim is queryable; every dashboard cites its
   source.
2. **Microscope and telescope on one screen.** Resource-tag-level
   granularity, portfolio-level rollup, simultaneously.
3. **Hub-and-spoke is the answer to "what about brand N+1."** Adding a
   brand is configuration, not engineering.
4. **Cost-conscious at every layer.** Phased ceiling stated up-front
   (§6); scope contracts when the ceiling is threatened.
5. **Boring tech for reliability, sharp tech for value.** FastAPI +
   Azure SQL on the reliability path; AI-native query, agentic ops,
   anomaly detection on the value path.
6. **Open by default within the portfolio.** Brand operators can read
   each other's non-sensitive metrics; cross-pollination is a feature.

---

## 4. The Architecture (V2: domains + interfaces, unchanged from V1)

Six bounded contexts, one external-interface adapter layer, one HTTP
boundary. This survived the redteam because it was correct.

```
         ┌───────────────────────────────────┐
         │          PLATFORM HUB             │
         │   (FastAPI + HTMX, App Service)   │
         └──────────────┬────────────────────┘
                        │
      ┌─────────┬───────┼────────┬─────────┬──────────┐
      ▼         ▼       ▼        ▼         ▼          ▼
   ┌─────┐ ┌────────┐ ┌────────┐ ┌──────┐ ┌──────┐ ┌──────────┐
   │Cost │ │Identity│ │Compli- │ │Resou-│ │ BI   │ │Lifecycle │
   │     │ │        │ │ ance   │ │ rces │ │Bridge│ │ Playbook │
   └──┬──┘ └───┬────┘ └───┬────┘ └──┬───┘ └──┬───┘ └────┬─────┘
      │        │          │          │        │          │
      └────────┴──────────┴──────────┴────────┴──────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       INTERFACES (adapters)        SHARED CORE
       Azure / AWS / Pax8 /         Auth / Cache / Config /
       Snowflake / M365             Telemetry / Audit
```

### Sequencing within domains (V2 hybrid approach)

Per redteam S1: domain boundary identification on paper happens first
(Phase 1, ~1 week), THEN file-size refactors happen along those lines
(Phase 1.5), THEN full DDD relocation (Phase 2). This avoids
double-touching every refactor.

---

## 5. The Phase Plan (V2: revised sequencing)

### Phase -1 — Ownership & Framing Alignment (concurrent with Phase 0)
- Confirm with HTT leadership that platform IP framing in this plan
  matches HTT's expectations (one paragraph: "HTT Brands has built X,
  Tyler is lead engineer, all artifacts HTT-owned").
- Update top-of-doc framing in all five repos' READMEs to reflect this
  framing.
- No legal pause is requested; the plan operates within standard
  work-for-hire scope. This phase is alignment, not gating.

### Phase 0 — Hygiene & Honesty (Week 1) ✅ DONE 2026-04-28
- Repair `.venv/` so tests run locally.
- Delete dead `origin/staging` branch.
- Honesty pass on `INFRASTRUCTURE_END_TO_END.md`.
- Pointer-to-truth banners on `CHANGELOG.md` and `WIGGUM_ROADMAP.md`.
- Update `mvxt` bd issue with staging-green evidence.
- **TYLER:** Dispatch production deploy off `main`.
- Investigate and clean up stale `control-tower-{4hn,rh1,tei,zp6}/`
  agent worktrees in predecessor repo (Feb 20–24 stale state).

### Phase 0.5 — Continuity & Bus-Factor (Week 1, parallel) ← NEW IN V2
- `RUNBOOK.md` for "Tyler is unavailable for 2+ weeks" scenarios.
- `SECRETS_OF_RECORD.md` enumerating where every credential lives and
  who else has read access.
- `AGENT_ONBOARDING.md` for a different human picking up the platform.
- DR-runbook seed: stated RTO/RPO for the platform's own data store
  (currently undefined; needs at minimum a backup-restore-test cadence).

### Phase 1 — Domain Boundary Definition (Week 2) ← NEW SHAPE IN V2
**Paper exercise. No code moves.**
- For each of the six target domains (cost, identity, compliance,
  resources, lifecycle, bi_bridge), produce:
  - `domains/<x>/README.md` — purpose, entities, invariants
  - `domains/<x>/DATA_CLASSIFICATION.md` — PII scope, retention,
    breach-notification scope (NEW: required per redteam item #1)
  - List of current code locations (file paths, line ranges) that
    belong to this domain
  - Inbound and outbound interface contracts
- Validate via dependency graph: domains do not import from each other
  laterally; all cross-domain calls go through interfaces.

### Phase 1.5 — File-Size Refactor Along Domain Lines (Weeks 2–3)
The 10 oversized files (>900 LOC) get split, but each split respects the
domain boundary documented in Phase 1. Tests gate each split; no mixed-
purpose commits.

Files in scope (unchanged from V1):
- `app/main.py` (1050 LOC) → ~150 LOC wiring + extracted middleware/routers
- `app/core/cache.py` (1181 LOC) → cache/{inmemory,redis,decorator,tenant_names}.py
- `app/preflight/admin_risk_checks.py` (921 LOC) → Strategy pattern
- `app/services/riverside_sync.py` (1075 LOC) → per-table modules
- `app/services/backfill_service.py` (999 LOC) → engine + handlers
- `app/api/routes/auth.py` (940 LOC) → routes + service split
- `app/core/config.py` (986 LOC) → config + keyvault
- `app/core/riverside_scheduler.py` (1110 LOC) → per-check submodules
- `app/api/services/budget_service.py` (1026 LOC) → CRUD/sync/alerting
- `app/services/lighthouse_client.py` (901 LOC) → request/response layers

### Phase 2 — DDD Relocation (Weeks 4–5)
Now that file boundaries respect domain boundaries, relocate
domain-specific code from `app/api/services/`, `app/services/`, and
`app/core/sync/` into `app/domains/<x>/`. Each move is mechanical
(import-path-preserving), with tests green before and after.

Add `app/interfaces/{azure,aws,pax8,snowflake,m365}/` adapter layer; all
external SDK calls funnel through these.

### Phase 3 — Naming & Rebrand Decision (Week 6) ← MOVED LATER IN V2
- Resolve the naming question (D-Name; see §11 for 5 candidates).
- Repo rename based on D-Name decision.
- Archive predecessor `control-tower` repo with forwarding README.
- Migrate predecessor IP we want forward (44 collectors triage,
  ResilientAzureClient pattern).
- Production hostname migration with 301 redirect (90-day window) AND
  documented rollback condition (if confusion >X helpdesk tickets/week,
  roll back hostname).
- Doc rewrite leads with new platform framing.

### Phase 4 — Cross-Repo Bridges (Weeks 7–14, 5 parallel tracks)
Each bridge is independent. **Per redteam S5: do `httbi` BEFORE `DART`.**
Each bridge has a written sunset criterion.

#### 4a. `cost :: Pax8` (recommended first — pure read-only, no auth complexity)
- Pull Pax8 invoices, normalize against Azure Cost Mgmt direct billing.
- Single ledger view in Cost domain.
- **Sunset criterion:** if Pax8 API stability is >5% monthly broken-call
  rate, replace with weekly CSV export ingestion.

#### 4b. `bi_bridge :: httbi` (do BEFORE DART per S5)
- Power BI XMLA federated query for Lash Lounge franchisee data.
- Same tenant family, same identity, validates federated-query pattern.
- **Sunset criterion:** if XMLA query latency exceeds 5s p95, replace
  with materialized view refresh on Azure SQL.

#### 4c. `bi_bridge :: DART` (after httbi proven)
- Athena query proxy through platform with Cognito-token-exchange-to-Entra.
- **Sunset criterion:** if Athena scan cost exceeds $50/mo or query
  latency exceeds 10s p95, replace with cached/batch-ETL'd subset in
  Azure SQL.

#### 4d. `lifecycle :: DCE template` (parameterized via Configuration-as-Code)
- DeltaSetup PowerShell becomes a brand-config YAML reconciled by a
  controller. Audit log derives from git history (per redteam item #8).
- **Sunset criterion:** if a brand acquisition takes >5 days end-to-end,
  re-evaluate whether the playbook fundamentally needs human steps.

#### 4e. `identity :: B2B governance UI`
- See D8 (CIEM build vs buy). If buy: integrate Microsoft Entra
  Permissions Management views into the platform UI. If build: minimal
  viable graph view + expiry-tracking + deprovisioning workflow.
- **Sunset criterion:** if Entra Permissions Management ships
  HTT-portfolio-equivalent functionality natively, retire custom
  domain.

### Phase 5 — AI-Native Layer (Weeks 15–18) ← MAY SLIP per redteam S3
- `/ask` endpoint: RAG over platform's own data (cost facts, identity
  graph, compliance state, audit log). Azure OpenAI + indexed views.
- `/act` endpoint (NEW IN V2): agentic-ops with guardrails. Examples:
  "auto-open bd issue when cost anomaly detected," "auto-deprovision
  expired B2B grant after Tyler approval." Read-write actions require
  explicit allowlist + dry-run + audit log.
- Anomaly detection: cross-domain signals (e.g., DCE bookings drop while
  ad spend holds flat).

### Phase 6 — Evidence Bundle Capability (Weeks 19–22) ← REFRAMED IN V2
**V1 framing (sanitized):** "Riverside read-out becomes a 30-minute demo
with receipts" → **V2 framing:** Build a per-quarter evidence-bundle
generator that produces:
- Portfolio-level cost dashboard with drill-down to resource-level
  attribution.
- Compliance evidence bundle (PDF + machine-readable JSON) suitable for
  any external read-out.
- "Days-to-onboard" metric for each acquired brand, baselined against
  the DCE template.
- Cost optimization receipts ledger: every saving, attributed, dated,
  sourced.

This is a generic capability. It serves Riverside, future PE diligence,
acquired-brand onboarding, internal exec read-outs, and audit
preparation equally.

---

## 6. Realistic Phased Cost Ceilings (V2: corrected per redteam)

| Phase | Target ceiling | Drivers |
|---|---|---|
| Today (Phase 0 done) | $53/mo | App Service B1 + Azure SQL Basic + Storage LRS + KV + App Insights |
| End of Phase 2 | $80/mo | Same + slight increase for log retention if Application Insights sampling tightens |
| End of Phase 4 | $150/mo | Adds Pax8 ingestion ($0; API), httbi XMLA queries ($0; existing capacity), DART Athena (per-scan, est. $10–30/mo at expected query volume), B2B governance |
| End of Phase 5 | $300–400/mo | Adds Azure OpenAI tokens for `/ask` + `/act` (estimated 50K tokens/day @ $0.01/1K = $15/mo for GPT-4o-mini, or up to $150/mo at higher tier) plus OTel collector (Azure Monitor billed; ~$50/mo) plus Sustainability Manager free tier |
| End of Phase 6 | $300–400/mo | Phase 6 is reporting; no new infrastructure |

**If $300–400/mo is unacceptable**, descope Phase 5 `/ask` to pre-canned
KQL/SQL templates instead of LLM-driven RAG. Saves $150–200/mo at the
cost of natural-language UX.

---

## 7. 2026 Best-Practices Anchoring (V2: pruned)

Per redteam item: 11 frameworks signaled breadth, not depth. V2 commits
to **5 frameworks** to execute well:

1. **FinOps Foundation Maturity Model** — Cost domain framing (Crawl/Walk/Run).
2. **Domain-Driven Design** — Six bounded contexts as documented in §4.
3. **Data Mesh** — DART, `httbi`, governance platform are independent
   data products with contracts; federate, don't absorb.
4. **OpenTelemetry** — Replace bespoke instrumentation in Phase 1.5.
5. **Configuration-as-Code** (NEW emphasis from redteam item #8) —
   Lifecycle playbook is YAML reconciled by controller, audit log
   derives from git history.

The other six (IDP, CIEM as a self-built thing, AI-native, Wardley
mapping, DORA/SPACE, sustainability) are downgraded to **awareness**
not commitment. Each gets a one-paragraph defense in
`docs/best-practices.md` explaining why we don't chase it now.

---

## 8. Success Metrics (V2: NEW — quantitative per phase)

| Metric | Baseline | Target | Phase |
|---|---|---|---|
| Files >600 LOC in `app/` | 10 | 0 | End of Phase 1.5 |
| Domains with `DATA_CLASSIFICATION.md` | 0 | 6 | End of Phase 1 |
| Domains in formal `app/domains/` layout | 0 | 6 | End of Phase 2 |
| Cross-cloud cost reconciliation lag | manual | weekly | End of Phase 4 |
| Time-to-brand-onboard (TTBO) | unknown — measure first | <5 days | End of Phase 4 |
| Cost-anomaly MTTD | unknown — measure first | <24 hrs | End of Phase 5 |
| % of quarterly read-out auto-generated | 0% | >70% | End of Phase 6 |
| $-saved-attributed cumulative | $0 | tracked publicly | End of Phase 6 |
| Bus-factor (humans able to deploy) | 1 | 2 | End of Phase 0.5 |
| RTO documented | undefined | stated + tested | End of Phase 0.5 |

No phase is "done" until its metric is measured and recorded.

---

## 9. Open Decisions for Tyler (V2: revised set)

### D1. Ownership / framing alignment
**Recommendation:** Confirm in writing with HTT leadership that the
platform is HTT-owned, Tyler is lead engineer, and the V2 framing is
acceptable. Light-weight; not a legal review.

### D2. Predecessor `control-tower` repo fate
- **Recommendation:** Archive read-only with forwarding README, migrate
  IP into the unified platform during Phase 3.

### D3. DART relationship
- **Recommendation:** Federate via bi_bridge (Phase 4c). DART stays an
  independent product with its contractor users.

### D4. Brand-route generalization
- **Recommendation:** Generalize to `/portfolio/<brand>` parametric
  routes. Riverside-specific framing becomes one-time content pass.

### D5. Pax8 / CSP integration scope
- **Recommendation:** Read-only billing reconciliation first (Phase 4a);
  expand to provisioning only if signal warrants.

### D6. AI layer build vs buy
- **Recommendation:** Both — buy commodity (Microsoft Copilot for Azure
  general queries), build only the cross-tenant cross-cloud query layer
  no vendor offers. `/ask` and `/act` are the build scope.

### D7. ESG / sustainability accounting urgency
- **Recommendation:** Capture intent now (carbon column reserved on
  cost_facts), implement in Phase 5 if the column has consumers by then.
  Otherwise defer.

### D8. ✨ NEW: CIEM build-vs-buy
Microsoft Entra Permissions Management exists and does cross-tenant B2B
grant analysis natively.
- **(a)** Buy entirely — integrate Entra Permissions Management views
  into the platform UI; do not build custom B2B graph code.
- **(b)** Build entirely — custom domain code, full ownership of UX.
- **(c)** Hybrid — Entra Permissions Management is the data source;
  platform UI surfaces it alongside other platform data.
- **Recommendation:** (c). The unique value is the integration with
  cost/compliance/resources data, not the CIEM analytics themselves.

### D9. ✨ NEW: WIGGUM_ROADMAP relationship
The existing 75 KB `WIGGUM_ROADMAP.md` already drives the `/wiggum
ralph` autonomous protocol. V2 plan needs to declare its relationship.
- **(a)** Replace — V2 supersedes WIGGUM_ROADMAP entirely.
- **(b)** Supplement — WIGGUM_ROADMAP keeps its role for autonomous
  execution; V2 is the strategic document above it.
- **(c)** Merge — WIGGUM_ROADMAP gets restructured into V2's phase
  shape, autonomous protocol points at V2.
- **Recommendation:** (b). WIGGUM_ROADMAP is a tactical execution log;
  V2 is strategic intent. Different artifacts, different audiences,
  no conflict if labeled clearly.

### D10. ✨ NEW: Cross-tenant identity graph stance
Per redteam: is "TLL users in HTT Fabric" a feature or a finding?
- **(a)** Feature — formalize, expose, manage. Eliminate via
  documentation + governance, not removal.
- **(b)** Finding — eliminate the cross-tenant grants. Each brand's
  data stays in its own tenant.
- **(c)** Hybrid — keep the grants where business need is documented
  and signed off, eliminate where they were ad-hoc.
- **Recommendation:** (c). Run a security audit pass in Phase 4e to
  classify each cross-tenant grant as documented-need or ad-hoc.
  Documented stays + gets governance UI; ad-hoc gets deprovisioned.

---

## 10. Things V2 Now Addresses (was missing in V1)

Per redteam, these were absent in V1 and are now in V2:

1. ✅ **DPIA / data classification** — required `DATA_CLASSIFICATION.md`
   per domain (Phase 1).
2. ✅ **SBOM / supply-chain on platform itself** — already done in
   bd `7mk8` (SLSA Build L3 + SBOM + Cosign 4-claim verify); V2
   acknowledges and extends to all 5 repos in Phase 1.
3. ✅ **Bus-factor / continuity** — Phase 0.5.
4. ✅ **DR / RTO-RPO** — Phase 0.5 seeds, Phase 6 hardens.
5. ✅ **Change management for human users** — sub-domain
   `lifecycle :: change_management` planned for Phase 4d.
6. ✅ **Rollback for the rebrand** — Phase 3 includes documented
   rollback condition (helpdesk-tickets-per-week threshold).
7. ✅ **Quantitative success metrics** — §8.
8. ✅ **GitOps / Configuration-as-Code** — Phase 4d (lifecycle
   playbook becomes YAML+controller).
9. ✅ **Agentic ops (`/act`)** — Phase 5 in addition to `/ask`.
10. ✅ **Honesty pass on this plan's own claims** — see §13 below.
11. ✅ **WIGGUM_ROADMAP reconciliation** — D9.
12. ✅ **Sibling `control-tower-{4hn,rh1,tei,zp6}/` dirs** —
    Phase 0 cleanup task; investigation reveals they are stale agent
    worktrees, not failed consolidation attempts (redteam was wrong on
    this finding; harmless to clean up).

---

## 11. The Naming Exercise (D-Name) ← NEW IN V2

V1's "Control Tower" name collides with AWS Control Tower (a real Amazon
service for multi-account governance). Five candidates evaluated:

| # | Name | Pros | Cons | Risk |
|---|---|---|---|---|
| **1** | **Switchyard** | Railway hub-and-spoke metaphor; nearly zero collisions in cloud space; evocative for "many tracks converge here." | Less familiar metaphor for non-rail-fluent audience. | Low. |
| **2** | **Hangar** | Aviation continuity from "Control Tower" mental model; single-word; memorable. | `hangar.dev` exists (different product); HangarCI is a thing. | Medium. |
| **3** | **Aerie** | Eagle's nest — vision + height + brood-of-many (the brands). Very rare in tech. Tasteful. | Slightly precious; spelling not obvious. | Low. |
| **4** | **Dispatch** | Operations / central command vibe; clear meaning. | Microsoft Dispatch service exists; Slack uses "dispatch" as a verb. Confusable. | Medium-High. |
| **5** | **Meridian** | Navigation metaphor (line of position); evocative for "where everything is right now." | AT&T Meridian (legacy phone system); some credit-union usage. | Medium. |

**Provisional ranking:** Switchyard > Aerie > Hangar > Meridian > Dispatch.

**Tyler's call needed:** Pick one, ask for more candidates, or defer
binding decision until Phase 3 prep (which is fine; V2 can ship to
planning-agent without the naming locked).

**Note:** Final due-diligence search (trademark check, domain
availability, GitHub/PyPI namespace check) should happen at decision
time, not now.

---

## 12. The 12 Hygiene Items + Phase 0.5 Items (V2: revised)

| # | Win | Time | Owner | Phase |
|---|---|---|---|---|
| 1 | Repair local `.venv` | 5 min | Richard ✅ DONE | 0 |
| 2 | Delete dead `origin/staging` | 1 min | Richard ✅ DONE | 0 |
| 3 | Honesty pass on `INFRASTRUCTURE_END_TO_END.md` | 15 min | Richard ✅ DONE | 0 |
| 4 | Pointer-banner on `CHANGELOG.md` | 5 min | Richard ✅ DONE | 0 |
| 5 | Pointer-banner on `WIGGUM_ROADMAP.md` | 5 min | Richard ✅ DONE | 0 |
| 6 | Update `mvxt` issue with staging-green evidence | 5 min | Richard ✅ DONE | 0 |
| 7 | **Tyler dispatches prod deploy off `main`** | 2 min | Tyler ⏳ | 0 |
| 8 | Clean up stale `control-tower-{4hn,rh1,tei,zp6}/` worktrees | 10 min | Richard | 0 |
| 9 | Write `RUNBOOK.md` (Tyler-unavailable scenarios) | 1 hr | Richard | 0.5 |
| 10 | Write `SECRETS_OF_RECORD.md` | 30 min | Tyler ⏳ (only Tyler knows where they all live) | 0.5 |
| 11 | Write `AGENT_ONBOARDING.md` | 30 min | Richard | 0.5 |
| 12 | Define RTO/RPO + backup-restore-test cadence | 15 min | Richard + Tyler | 0.5 |
| 13 | Domain boundary paper exercise — six `domains/<x>/README.md` | 4 hr | Richard | 1 |
| 14 | Six `DATA_CLASSIFICATION.md` artifacts | 2 hr | Richard | 1 |
| 15–24 | File-size refactors along domain lines | ~12 hr | Richard | 1.5 |

**Total agent time through Phase 1.5:** ~22 hours of focused work
across ~3 weeks.
**Total Tyler time:** ~1 hour (D-decisions, prod deploy button,
SECRETS_OF_RECORD authorship).

---

## 13. Honesty Pass on V2's Own Claims ← NEW IN V2

| Claim | Evidence | Last verified |
|---|---|---|
| 4,192 tests | pytest --collect-only | 2026-04-28 |
| WCAG 2.2 AA | tests/accessibility/ + manual audit | March 2026 (per CHANGELOG) — needs re-audit |
| PKCE OAuth + refresh-token blacklisting | code review of `app/api/routes/auth.py` | March 2026 implementation; no penetration test on file |
| 138 tables, 222M rows | bi-migration-agent docs | quoted from bi-migration-agent — needs SQL `SELECT COUNT(*)` re-verification before Phase 4b |
| 44 collectors in predecessor | predecessor repo `backend/` | 2026-02 last commit; not re-verified |
| ~$53/mo today | Azure Cost Management April 2026 | 2026-04-16 |
| Five Azure tenants federated | OIDC trust relationships | 2026-03 deployments |

**Re-verification cadence:** Each claim above gets a quarterly check
in `docs/honesty-log.md`. Stale claims trigger a `bd` issue.

---

## 14. Summary for planning-agent

**V2 is ready for decomposition** subject to Tyler's calls on D1, D8,
D9, D10, and D-Name (§11). Recommended decomposition order:

1. **Phase 0 + Phase 0.5 in parallel** — already underway; handful of
   remaining tasks per §12.
2. **Phase -1 framing alignment** — one-paragraph confirmation conversation.
3. **Phase 1 domain boundaries** — paper exercise, single track.
4. **Phase 1.5 file refactors** — single track, gated by Phase 1.
5. **Phase 2 DDD relocation** — single track, gated by Phase 1.5.
6. **Phase 3 naming + rebrand** — gated by D-Name decision.
7. **Phase 4 bridges (a–e)** — five parallel tracks; explicit
   `httbi-before-DART` ordering for 4b/4c.
8. **Phase 5 AI layer** — gated by Phase 2 + Phase 4 substantially
   complete.
9. **Phase 6 evidence bundle** — gated by Phase 5 substantially
   complete.

Each task becomes a `bd` issue with proper dependency edges.
planning-agent's prompt is in §15.

---

## 15. Prompt for planning-agent (V2)

> Read `PORTFOLIO_PLATFORM_PLAN_V2.md` and decompose it into a `bd`
> issue tree.
>
> Constraints:
> - Phase 0 issues are mostly done; mark as such (see §12 status column).
> - Phase 0.5 issues should be ready-to-claim immediately and must
>   complete before Phase 6 starts.
> - Phase 1 issues depend on Phase 0 closure.
> - Phase 1.5 issues depend on Phase 1 closure.
> - Phase 2 issues depend on Phase 1.5 closure.
> - Phase 3 issues depend on D-Name decision (§11).
> - Phase 4 issues are five parallel tracks; 4c (DART) explicitly
>   depends on 4b (httbi).
> - Phase 5 issues depend on Phase 2 substantial completion AND Phase 4
>   substantial completion.
> - Phase 6 issues depend on Phase 5 substantial completion AND
>   Phase 0.5 closure.
> - Estimate effort per issue in agent-hours and identify the critical
>   path.
> - Respect the success metrics in §8 — each phase issue's acceptance
>   criteria should reference the relevant metric.
> - Do not lock the brand name into any issue title or branch name; use
>   "platform" generically until D-Name resolves.
>
> Output: a structured set of `bd create` commands (or equivalent), the
> dependency edges, the critical path, and the total agent-hour
> estimate.

---

*Drafted by Richard (code-puppy-ab8d6a) for Tyler Granlund, 2026-04-28.*
*V2 supersedes V1; both preserved as historical record.*
*Plan is sharper. Language is professional. Sequencing is correct.*
*Let's go ship the platform. 🐶*
