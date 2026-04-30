# Requirements Traceability Matrix — v2.5.1 Release (DRAFT)

> **Status:** 🚧 **DRAFT — prospective RTM** · **Target tag:** `v2.5.1`
> **Window start:** `v2.5.0` @ `b1137cb` (2026-04-15) → *(window end TBD at release cut)*
> **Consumer:** release-gate-arbiter (Pillar 1 — Requirements Closure)

## 0. Why this file exists early

The `v2.5.0` RTM was prepared **retroactively** — after the release commits
had landed. The arbiter accepted it with a `CONDITIONAL_PASS` caveat about
"prospective traceability discipline" that matters more at prod promotion.

This file is the **prospective RTM** for v2.5.1 — started on the day the
last `v2.5.0` carve-out (bd `7mk8`) closed. Every bd ticket merged to `main`
after `v2.5.0` gets a row here at close-time, so when v2.5.1 is cut the RTM
is already done.

**Process rule (prospective RTM discipline):**

1. When a bd ticket is closed with a commit on `main`, append a row here.
2. When the row is added, reference the commit SHA in the ticket's "close"
   comment (bidirectional linkage).
3. When v2.5.1 is cut (at whatever SHA), this file is renamed
   `rtm-v2.5.1.md` (drop the `-DRAFT` suffix), the top-of-doc status flips
   to "Accepted", and it becomes a binding artifact.

---

## 1. Summary (auto-updated at each row addition)

> **Update checklist:** when you append a row below, update these counts.

| Metric | Count |
|---|---|
| Total tickets in window | 56 |
| Closed (work complete) | 50 |
| Open (carve-outs) | 6 (`9lfn`, `mvxt`, `uchp`, `l96f`, `rtwi`, `m4xw` — all **NOT prod blockers**) |
| Themes | 8 |

### Work by theme

| Theme | Tickets |
|---|---|
| Supply-chain hardening | 4 (`7mk8`, `dq49`, `my5r`, `g1cc`) |
| Production-readiness blockers (Workstreams A–E of roadmap-2026-04-24) | 9 (`g1cc`, `aiob` + 5 sub-issues, `918b`, `0gz3`, `j875`, `213e`, `3ogi`, `gm9h`, `0nup`) |
| Domain boundary docs (Phase 1 of V2 plan) | 6 (`32d8`, `fos1`, `htnh`, `c10e`, `ewdp`, `sl01`) |
| Code organization (Phase 1.5 file-size refactors) | 10 (`bu72`, `gvpt`, `lq11`, `oknl`, `qb8u`, `uxzr`, `2l4h`, `a3oq`, `fbx8`, `wnpf`) |
| Operational continuity (Phase 0.5) | 6 (`2au0`, `68g7`, `0dhj`, `q46o`, `39yp`, `213e`) |
| Rebrand to Control Tower (Phase 3) | 3 (`0dsr`, `re42`, `q46o`) |
| Operations / infra / CI hygiene | 11 (`x692`, `q8lt`, `3flq`, `jzpa`, `fifh`, `tg2z`, `mf9r`, `x6uo`, `xkgp`, `tbvs`, `j6tq`) |
| Bug fixes | 3 (`jxts`, `w0p8`, `tbvs`) |

Note: some tickets count under more than one theme (e.g. `q46o` advances
both Phase 0.5 continuity and Phase 3 rebrand). The total-ticket count
in §1 is unique.

---

## 2. Detailed traceability (append rows as work closes)

### Supply-chain hardening

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `7mk8` | P1 | ✅ closed 2026-04-23 | security(supply-chain): implement SLSA L3 + Sigstore cosign + SBOM in release-production workflow | `7d816f6` `7921b92` `b28a9f2` `3042624` | ci-workflow, docs (arbiter/policies/verify.yaml), workflow-gate |
| `dq49` | P3 | ✅ closed 2026-04-23 | chore(supply-chain): SHA-pin attest-*, cosign-installer, sbom-action | `ebb2086` | ci-workflow |
| `my5r` | P2 | ✅ closed 2026-04-23 | feat(ci): env-delta.yaml schema validator + literal-rejection gate | `04d0d7b` | tests, ci-workflow, scripts |

### Production-readiness blockers (Workstreams A–E of `docs/plans/production-readiness-and-release-gate-roadmap-2026-04-24.md`)

| bd ID | P | Status | Title | Closing commit (or ref) | Validation surface |
|---|---|---|---|---|---|
| `g1cc` | P1 | ✅ closed 2026-04-29 | ci/release: deterministic + arbiter-aligned attestation verification in `deploy-production.yml` | (closure ref in bd) | `.github/workflows/deploy-production.yml`, `arbiter/policies/verify.yaml` |
| `aiob` | P1 | ✅ closed 2026-04-29 | meta(ci): no frontend smoke / visual-regression tests in CI — shipped broken UI through gates | (closure ref) | `.github/workflows/ci.yml`, `tests/browser_smoke/` |
| `aiob.1` | P1 | ✅ closed 2026-04-24 | tests: stabilize canonical browser session fixture | (closure ref) | `tests/browser_smoke/` |
| `aiob.2` | P1 | ✅ closed 2026-04-24 | tests: deterministic seeded/empty-state contract for browser smoke | (closure ref) | `tests/browser_smoke/` |
| `aiob.3` | P1 | ✅ closed 2026-04-24 | tests: focused browser smoke for critical pages + HTMX partials | (closure ref) | `tests/browser_smoke/` |
| `aiob.4` | P1 | ✅ closed 2026-04-24 | ci: wire browser-smoke job, sanitized artifacts, soak-promotion | (closure ref) | `.github/workflows/ci.yml` |
| `aiob.5` | P2 | ✅ closed 2026-04-24 | RBAC negative coverage for browser-gated routes | (closure ref) | `tests/browser_smoke/` |
| `918b` | P1 | ✅ closed 2026-04-29 | investigate persistent prod per-tenant Key Vault fallback failures | (closure ref) | `scripts/investigate_sync_tenant_auth.py`, `docs/runbooks/sync-recovery-verification.md` |
| `0gz3` | P1 | ✅ closed 2026-04-29 | post-deploy verify sync recovery + alert burn-down after tenant-eligibility fix | (closure ref) | `scripts/verify_sync_recovery_report.py`, `docs/runbooks/sync-recovery-verification.md` |
| `j875` | P1 | ✅ closed 2026-04-24 | migrate rollback waiver + rollback docs to machine-verifiable current-state artifacts | (closure ref) | `docs/release-gate/rollback-current-state.yaml` |
| `213e` | P2 | ✅ closed 2026-04-30 | name a second rollback human before 2026-06-22 waiver expiry | `64515a5` | `docs/release-gate/rollback-current-state.yaml`, `docs/dr/second-rollback-human-checklist.md` |
| `3ogi` | P2 | ✅ closed 2026-04-25 | reconcile release-dossier / README / live version + resource references | (closure ref) | docs |
| `gm9h` | P2 | ✅ closed 2026-04-30 | production GitHub environment had zero protection rules / required reviewers | `64515a5` | GitHub `production` environment config |
| `0nup` | P1 | ✅ closed 2026-04-30 | release: assemble production-readiness evidence bundle + rehearse strict gate | (this commit) | `docs/release-gate/evidence-bundle-2026-04-30.md`, `docs/release-gate/verdicts/rehearsal-2026-04-30-internal.md` |

### Domain boundary documentation (Phase 1 of `PORTFOLIO_PLATFORM_PLAN_V2.md` §5)

All 6 bounded contexts identified in V2 §6 now have boundary READMEs
under `domains/{name}/README.md` with purpose, entities/invariants,
current code locations (file paths + line ranges), inbound/outbound
contracts, and DATA_CLASSIFICATION:

| bd ID | P | Status | Domain |
|---|---|---|---|
| `32d8` | P2 | ✅ closed 2026-04-29 | `cost` |
| `fos1` | P2 | ✅ closed 2026-04-29 | `identity` |
| `htnh` | P2 | ✅ closed 2026-04-29 | `compliance` |
| `c10e` | P2 | ✅ closed 2026-04-29 | `resources` |
| `ewdp` | P2 | ✅ closed 2026-04-29 | `lifecycle` |
| `sl01` | P2 | ✅ closed 2026-04-29 | `bi_bridge` |

### Code organization (Phase 1.5 file-size refactors)

Mechanical splits along domain lines, all preserving public API:

| bd ID | P | Status | Refactor target | LOC delta |
|---|---|---|---|---|
| `bu72` | P2 | ✅ closed 2026-04-29 | `app/main.py` | 1050 → ~150 (wiring) + middleware/routers |
| `gvpt` | P2 | ✅ closed 2026-04-29 | `app/core/cache.py` | 1181 → cache/{inmemory,redis,decorators} |
| `lq11` | P2 | ✅ closed 2026-04-29 | `app/core/config.py` | 986 → config + keyvault |
| `oknl` | P2 | ✅ closed 2026-04-29 | `app/api/routes/auth.py` | 940 → routes + service |
| `qb8u` | P2 | ✅ closed 2026-04-29 | `app/api/services/budget_service.py` | 1026 → CRUD/sync/alerts |
| `uxzr` | P2 | ✅ closed 2026-04-29 | `app/services/backfill_service.py` | 999 → engine + handlers |
| `2l4h` | P2 | ✅ closed 2026-04-29 | `app/services/lighthouse_client.py` | 901 → request/response |
| `a3oq` | P2 | ✅ closed 2026-04-29 | `app/services/riverside_sync.py` | 1075 → per-table modules |
| `fbx8` | P2 | ✅ closed 2026-04-29 | `app/core/riverside_scheduler.py` | 1110 → 533 + per-check submodules |
| `wnpf` | P2 | ✅ closed 2026-04-29 | `app/preflight/admin_risk_checks.py` | 921 → Strategy pattern |

### Operational continuity (Phase 0.5)

Bus-factor and disaster-recovery readiness:

| bd ID | P | Status | Title | Commits / artifact |
|---|---|---|---|---|
| `2au0` | P2 | ✅ closed 2026-04-28 | docs(continuity): write `AGENT_ONBOARDING.md` | `AGENT_ONBOARDING.md` |
| `68g7` | P2 | ✅ closed 2026-04-28 | docs(continuity): write `RUNBOOK.md` | `RUNBOOK.md` |
| `0dhj` | P2 | ✅ closed 2026-04-28 | infra(dr): define platform RTO/RPO + backup-restore-test cadence | `docs/dr/rto-rpo.md` |
| `q46o` | P2 | ✅ closed 2026-04-29 | docs(continuity): rewrite second-rollback-human checklist for post-auto-rollback world | `a2a18bf` |
| `39yp` | P2 | ✅ closed 2026-04-30 | ops(release): auto-rollback on failed health gate in production deploy | `d9d9d88` |
| `213e` | P2 | ✅ closed 2026-04-30 | (also under Production-readiness blockers above) | `64515a5` |

### Rebrand to Control Tower (Phase 3)

| bd ID | P | Status | Title | Commits |
|---|---|---|---|---|
| `0dsr` | P2 | ✅ closed 2026-04-30 | execute GitHub repo / GHCR / Pages Control Tower cutover | (multiple) |
| `re42` | P2 | ✅ closed 2026-04-30 | clean up Control Tower cutover long-tail residue | `1fb1534` |
| `q46o` | P2 | ✅ closed 2026-04-29 | (cross-listed with Phase 0.5 above) | |

### Operations / infra / CI hygiene

| bd ID | P | Status | Title | Commits |
|---|---|---|---|---|
| `x692` | P3 | ✅ closed 2026-04-23 | feat(ops): scheduled Bicep drift detection | `fecf0fd` |
| `q8lt` | P2 | ✅ closed 2026-04-29 | ops(ci): Bicep Drift Detection workflow scope mismatch | (closure ref) |
| `3flq` | P2 | ✅ closed 2026-04-29 | ops(ci): Database Backup Azure login OIDC id-token permission | (closure ref) |
| `jzpa` | P1 | ✅ closed 2026-04-30 | ops(ci): Database Backup jobs missing environment backup secrets | (closure ref) |
| `fifh` | P2 | ✅ closed 2026-04-28 | ops(ci): Database Backup workflow `mda590/teams-notify` action removed | `41126f8` |
| `tg2z` | P2 | ✅ closed 2026-04-29 | investigate residual Riverside batch + DMARC alerts after `0gz3` | `a062345` |
| `mf9r` | P2 | ✅ closed 2026-04-24 | tests: disable background scheduler during browser/e2e app startup | (closure ref) |
| `x6uo` | P3 | ✅ closed 2026-04-29 | techdebt: replace `datetime.utcnow()` in app + scripts | (closure ref) |
| `xkgp` | P3 | ✅ closed 2026-04-29 | techdebt: replace `datetime.utcnow()` in tests + fixtures | (closure ref) |
| `tbvs` | P1 | ✅ closed 2026-04-23 | bug(ops): production sync jobs failing — 222 active alerts | (closure ref) |
| `j6tq` | P3 | ✅ closed 2026-04-30 | ops(cost): model B1 vs Container Apps consumption with current scheduler load | `a92cf9b` |

### Bug fixes

| bd ID | P | Status | Title | Commits |
|---|---|---|---|---|
| `jxts` | P1 | ✅ closed 2026-04-23 | bug(frontend): `/partials/sync-history-table` returns HTTP 500 in prod | (closure ref) |
| `w0p8` | P1 | ✅ closed 2026-04-23 | bug(frontend): sync status card job-type labels invisible in dark mode | (closure ref) |

### Staging reliability (mitigation-only, ticket stays open)

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `mvxt` | P2 | 🟡 open (mitigated) | ops(staging): Deploy to Staging validation suite consistently times out | `68c0baa` (mitigation), `a7557a4` (docs sweep) | tests/staging/conftest.py |

**Note:** `mvxt` is **intentionally kept open** — the shipped change is a
compensating control (cold-start warmup + retry adapter), not a root-cause
fix. Root cause needs Azure Portal / App Insights access. Does not block
v2.5.1 promotion because the mitigation reduces CI-failure rate to
acceptable levels and the SLO (per `docs/SLO.md`) is not at risk from
cold-start behavior.

### Open carve-outs (NOT in v2.5.1 — tracked only)

| bd ID | P | Status | Title | Reason / trigger | Blocks v2.5.1? |
|---|---|---|---|---|---|
| `9lfn` | P1 | 🟡 open (Tyler-only) | docs(continuity): Tyler authors `SECRETS_OF_RECORD.md` | Tyler-only authorship; no longer bus-factor blocker because Dustin has direct KV/storage access | ❌ No — soft condition in rehearsal verdict |
| `uchp` | P2 | 🟡 open (date-gated) | infra(dr): execute Q3 2026 quarterly DR test cycle | Due 2026-07-31; absorbs Dustin's formal hands-on tabletop | ❌ No — post-release |
| `l96f` | P3 | 🟡 open (deferred) | ops(rebrand): rotate JWT iss claim from `azure-governance-platform` to `control-tower` | Logs all users out; needs coordinated session window | ❌ No — Phase 3 cleanup |
| `rtwi` | P3 | 🟡 open (date-gated) | ops: stop domain-intelligence App Service at 60d zero-traffic | 2026-05-17 | ❌ No — separate project resource group |
| `m4xw` | P4 | 🟡 open (date-gated) | ops: automate quarterly audit-log archive to Azure Blob Archive tier | 2026-07-01 | ❌ No — post-release |

---

## 3. Governance / non-ticket changes

Changes that landed without their own bd ticket but are in the release window:

| Date | Commit | Summary | Rationale for no ticket |
|---|---|---|---|
| 2026-04-23 | `a7557a4` | Close stale SBOM/SLSA/cosign gap references across 4 docs | Follow-through on `7mk8`; within same work session |
| 2026-04-23 | `59aecda` | 2026-04-23 session log | Governance artifact; session log is per-session, not per-ticket |
| 2026-04-23 | `874bc02` | README badge bump 2.3.0 → 2.5.0 | Stale badge fix; trivial |
| 2026-04-23 | _(pending)_ | SLO + Data Retention + GitHub Seat Audit policy docs | Close COST_MODEL Q1/Q5/Q6; no bd ticket because they're policy commitments, not code |
| 2026-04-23 | _(pending)_ | Stale-root-doc archive sweep (10 files to docs/archive/) | Governance hygiene; pure doc move |
| 2026-04-23 | _(pending)_ | INFRASTRUCTURE_INVENTORY.md SUPERSEDED banner | Doc correction; 11 live refs made banner preferable to archive |

---

## 4. Scope boundary — what's explicitly NOT in v2.5.1

For arbiter clarity: the following work is **known to exist** but will NOT
land in v2.5.1. Each has a declared home.

| Item | Where it lives | Why deferred |
|---|---|---|
| `mvxt` root-cause (App Insights investigation) | Stays in bd `mvxt` (open) | Needs Azure Portal access — Tyler-only activity |
| `rtwi` domain-intelligence shutdown | Stays in bd `rtwi` (open) | Date-gated 2026-05-17 — triggers AFTER v2.5.1 cut |
| Dev env auto-pause (COST_MODEL Q3) | Not yet filed | Awaiting product decision |
| Zero-downtime blue-green (COST_MODEL Q4) | Tracked in prior-session context as `bd-hofd` | Awaiting SLO-driven trigger per `docs/SLO.md` §2.2 |
| Multi-region deployment | No ticket | SLO is 99.9%, doesn't require it |

---

## 5. Pre-submission checklist (before flipping to rtm-v2.5.1.md)

- [ ] All ticket rows point at commits present in the `v2.5.0..<release-sha>` range
- [ ] Summary counts (§1) updated to match the table row counts in §2
- [ ] Governance changes (§3) all cited with commit SHA
- [ ] `mvxt` + `rtwi` explicitly documented as non-blocking in §4
- [ ] Arbiter policy file (`arbiter/policies/verify.yaml`) references v2.5.1 if any supply-chain policy diff
- [ ] `CHANGELOG.md` `[Unreleased]` section promoted to `[2.5.1] - <date>`
- [ ] `pyproject.toml` version bumped to `2.5.1`
- [ ] `core_stack.yaml` `version:` line bumped to `2.5.1`
- [ ] `env-delta.yaml` `deltas_since_previous_release` block updated
- [ ] Top-of-doc status flipped from `🚧 DRAFT` to `Accepted`
- [ ] File renamed `rtm-v2.5.1.md`
- [ ] Committed with message `docs(release-gate): promote rtm-v2.5.1 from draft`

---

## 6. References

- `docs/release-gate/rtm-v2.5.0.md` — previous (retroactive) RTM, template
- `docs/release-gate/submission-v2.5.0.md` — full release-gate dossier pattern
- `docs/release-gate/verdicts/rga-2026-04-22-azgov-v2.5.0-02.md` — previous arbiter verdict
- `arbiter/policies/verify.yaml` — production supply-chain verification policy (machine-readable)
- `docs/SLO.md` — SLO that governs what counts as "good enough for prod"
- `docs/DATA_RETENTION_POLICY.md` — retention contract
- `docs/GITHUB_SEAT_AUDIT.md` — seat-management procedure
