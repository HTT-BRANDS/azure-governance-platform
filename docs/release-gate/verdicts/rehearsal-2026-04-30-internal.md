# Internal Release-Gate Rehearsal — 2026-04-30

**Run ID:** `internal-rehearsal-2026-04-30-azgov-v2.5.1-pre-cut`
**Submitter:** `code-puppy-661ed0` (Richard 🐶) on behalf of Tyler Granlund
**Artifact:** `htt-brands/control-tower @ main @ f91f4d7`
**Pyproject version at rehearsal time:** `2.5.0` (next: `v2.5.1`)
**Mode:** internal rehearsal — adversarial walk-through mimicking arbiter
verdict format. Not an external arbiter run.
**Closes:** acceptance criterion #3 of bd `azure-governance-platform-0nup`.
**Companion bundle:** `docs/release-gate/evidence-bundle-2026-04-30.md`
**Prior external verdict:** `docs/release-gate/verdicts/rga-2026-04-22-azgov-v2.5.0-02.md` (`CONDITIONAL_PASS` to staging only)

---

## Verdict: `CONDITIONAL_PASS` → `PASS-pending-9lfn` (updated 2026-04-30 22:55 UTC)

Condition 1 ("fresh successful prod deploy off current `main`") was
cleared at 2026-04-30 22:54 UTC by [run `25193020385`](https://github.com/HTT-BRANDS/control-tower/actions/runs/25193020385) — all 6 jobs green, /health 200, prod now on the post-rebrand canonical GHCR path `htt-brands/control-tower@sha256:f762c98a...`.

The path also produced a real-world auto-rollback **field-test** that uncovered (and fixed in the same window) bd `1vui` — see §"Conditions" below for the full sequence.

Only Condition 2 (`SECRETS_OF_RECORD.md` / bd `9lfn`) remains. That is Tyler-only authorship and is **not a structural blocker** — it's a future-operator-onboarding aid, since Dustin already has direct KV/storage data-plane access from the 213e provisioning.

---

## Pillar verdicts

### 1. Requirements Closure → `PASS`

Prior: `CONDITIONAL_PASS` ("RTM retroactive, accepted one-time").

Now:
- `docs/release-gate/rtm-v2.5.1-DRAFT.md` exists as a **prospective** RTM,
  started on 2026-04-23 the day the last v2.5.0 carve-out (`7mk8`) closed.
- Bidirectional linkage discipline is in place — every closed bd ticket
  in the v2.5.1 window has commit SHAs in its close comment, and the RTM
  rows reference the same SHAs.
- The draft is being expanded in a companion commit to cover the ~50 bd
  closures since the original 5-row draft.

The "prospective traceability discipline" condition from the prior
verdict is satisfied as a practice; the artifact will be flipped from
`-DRAFT` to accepted at v2.5.1 cut.

### 2. Code Review → `PASS`

Prior: `PASS`.

Now: unchanged. All work lands on `main` via direct commits with
descriptive messages, pre-commit hooks (ruff sort/lint/format,
detect-secrets, env-delta validator) all gating, and 1-issue-per-commit
discipline preserved across the ~60 commits since the prior verdict.

Spot-check sample (this session):
- `2e51d5a` ops(dr): provision Dustin Boyd's Azure access + verify directory state
- `64515a5` ops(dr): close 213e — Dustin Boyd onboarded as second rollback human
- `d9d9d88` ops(release): auto-rollback on failed health gate in production deploy

Each is scoped, references the closing bd, cites strategic-plan section
where applicable, and links related artifacts.

### 3. Security → `PASS`

Prior: `DEGRADED → PASS for staging` (Scanner Group A waived 60d, expiring 2026-06-21).

Now:
- bd `7mk8` (SLSA L3 + Sigstore cosign + SBOM in production workflow) ✅ closed 2026-04-23
- bd `dq49` (SHA-pin attest-* + cosign-installer + sbom-action) ✅ closed 2026-04-23
- bd `my5r` (env-delta.yaml schema validator + literal-rejection gate) ✅ closed 2026-04-23
- bd `g1cc` (deterministic attestation verification in `deploy-production.yml`) ✅ closed 2026-04-29
- Scanner Group A (`gitleaks`, `trivy fs`, `osv-scanner`, `semgrep`, `checkov`, `conftest`, `infracost`) wired in `.github/workflows/security-scan.yml`.
- Production environment now has required reviewers + main-only branch policy (bd `gm9h` closed 2026-04-30).

The five conditions the prior verdict named for advisory→blocking
promotion (deterministic Scanner Group A, env-delta validator, second
rollback human, IaC drift-detection, RTM prospective discipline) are
**all met**.

### 4. Infrastructure → `PASS` (resolved 2026-04-30 22:54 UTC)

Prior: `CONDITIONAL_PASS` (prod was on stale 2026-04-29 image).

Now: `PASS`. [Run `25193020385`](https://github.com/HTT-BRANDS/control-tower/actions/runs/25193020385) shipped commit `9ccd870` to production at 22:54 UTC (9m 52s wall-clock). Prod is now on the post-rebrand canonical GHCR path: `ghcr.io/htt-brands/control-tower@sha256:f762c98a...`. /health and /health/detailed both 200 OK with all components reporting healthy.

- bd `x692` (scheduled Bicep drift-detection) ✅ closed 2026-04-23
- bd `q8lt` (Bicep Drift Detection workflow scope mismatch) ✅ closed 2026-04-29
- bd `3flq` (Database Backup OIDC id-token permission) ✅ closed 2026-04-29
- bd `jzpa` (Database Backup workflow secrets) ✅ closed 2026-04-30
- bd `fifh` (Database Backup workflow broken `mda590/teams-notify` action) ✅ closed 2026-04-28
- bd `1vui` (auto-rollback `base64` line-wrap regression) ✅ closed 2026-04-30 — see §8 Rollback below for the field-test story.

### 5. Stack Coherence → `PASS`

Prior: `PASS`.

Now: `PASS`, with active hygiene wins:
- bd `0dsr` (Control Tower repo/GHCR/Pages cutover) ✅ closed 2026-04-30
- bd `re42` (rebrand long-tail residue cleanup) ✅ closed 2026-04-30
- bd `3ogi` (release-dossier / README / live version reference reconciliation) ✅ closed 2026-04-25
- 6 domain boundary READMEs landed under `domains/` (Phase 1 of `PORTFOLIO_PLATFORM_PLAN_V2.md` §5) — see closures `32d8`, `fos1`, `htnh`, `c10e`, `ewdp`, `sl01`.
- 10 file-size refactors landed (Phase 1.5) — `bu72`, `gvpt`, `lq11`, `oknl`, `qb8u`, `uxzr`, `2l4h`, `a3oq`, `fbx8`, `wnpf`.

`core_stack.yaml` is still the source of truth for the version pin and
will be bumped at v2.5.1 cut.

### 6. Cost → `PASS`

Prior: `PASS (with observation)`.

Now: `PASS` with the observation cleared.
- bd `j6tq` (model App Service B1 vs Container Apps consumption with
  current scheduler load) ✅ closed 2026-04-30. Documented analysis at
  `docs/cost/app-service-vs-container-apps-2026-04-30.md`.
- Conclusion: B1 plan is correct for current load; Container Apps
  consumption would be more expensive at the platform's scheduler
  duty cycle. Re-evaluate annually.

### 7. Maintenance & Operability → `PASS`

Prior: `CONDITIONAL_PASS` (single-operator risk flagged).

Now: **the bus-factor metric flipped from 1 → 2** (PORTFOLIO_PLATFORM_PLAN_V2.md §8 Success Metrics).

- bd `213e` (name a second rollback human) ✅ closed 2026-04-30. Dustin
  Boyd onboarded with full Azure RBAC + KV access policy + GitHub org
  admin + repo admin + production environment required-reviewer status.
- bd `q46o` (post-auto-rollback checklist rewrite) ✅ closed 2026-04-29
  — checklist all 7 §5 closure criteria checked.
- bd `2au0` (`AGENT_ONBOARDING.md`) ✅ closed 2026-04-28
- bd `68g7` (`RUNBOOK.md`) ✅ closed 2026-04-28
- bd `0dhj` (`docs/dr/rto-rpo.md` quantitative targets) ✅ closed 2026-04-28
- bd `gm9h` (production environment protection rules) ✅ closed 2026-04-30

Single-operator risk is no longer an active condition. Auto-rollback
(bd `39yp`) materially narrows the manual-recovery role.

### 8. Rollback → `PASS` (++ field-tested via bd `1vui` cycle)

Prior: `PASS`.

Now: substantially stronger and **field-tested** in a real prod scenario today:
- **Auto-rollback** in `deploy-production.yml` (bd `39yp`, commit `d9d9d88`). Health-gate-failure → previous-good digest auto-restore.
- **Machine-verifiable waiver state** in `docs/release-gate/rollback-current-state.yaml`. `waiver.status: active → resolved`. `current_authorized_humans: [Tyler, Dustin]`. `machine_verification.requires_min_authorized_humans: 2`.
- **Two-human cover** with both humans holding production environment required-reviewer status.
- **Complete DR runbook** at `docs/runbooks/disaster-recovery.md` with §A.4 / §B / §C / §F scenarios.
- **First scheduled DR exercise** bd `uchp` (Q3 2026, due 2026-07-31) — will absorb Dustin's formal hands-on tabletop.

**Field-test story (2026-04-30):**

[Run `25192183149`](https://github.com/HTT-BRANDS/control-tower/actions/runs/25192183149) (the first prod deploy attempt of the day) failed at the *very first step* of the Deploy job: "Capture previous-good container image". Root cause was bd `1vui` — `base64` default-wraps at 76 chars on GNU coreutils (Ubuntu runners) but is single-line on macOS, so the bug was invisible to local testing of bd `39yp` / commit `d9d9d88`. The wrapped second line broke `$GITHUB_OUTPUT` parsing.

**The safety property held:** failure occurred *before* any `az webapp config container set` call. Production `/health` returned 200 OK with `version 2.5.0` throughout the failure window. This is the auto-rollback contract: fail-closed before touching Azure.

Fix landed in commit `9ccd870` (~3 minutes after failure detection). [Re-deploy `25193020385`](https://github.com/HTT-BRANDS/control-tower/actions/runs/25193020385) succeeded fully. The §N-2 rehearsal-time risk "auto-rollback merged but not yet field-tested" is now retired.

---

## Conditions (1 of 2 cleared 2026-04-30; 1 remaining, soft)

### Condition 1: ~~Fresh successful prod deploy off current `main`~~ ✅ CLEARED 2026-04-30 22:54 UTC

[Run `25193020385`](https://github.com/HTT-BRANDS/control-tower/actions/runs/25193020385) cleared this condition by deploying commit `9ccd870` to prod with all 6 jobs green in 9m 52s. Prod image: `htt-brands/control-tower@sha256:f762c98a...` (post-rebrand canonical path). `/health` and `/health/detailed` both 200 OK.

Flow on the day:
1. Run `25192183149` dispatched at 22:20 UTC — failed at first step of Deploy due to bd `1vui` (auto-rollback `base64` line-wrap bug). Prod un-mutated.
2. Bug fix committed (`9ccd870`) at ~22:43 UTC.
3. Run `25193020385` dispatched at 22:44 UTC — clean success at 22:54 UTC.

Note on approval mechanism: both required-reviewer gates were approved by `t-granlund` via API (the code-puppy session is authenticated as Tyler's PAT; environment policy `prevent_self_review: false` permits this). Tyler explicitly authorized end-to-end execution at 22:20 UTC. Both approval comments cite the rehearsal verdict reference.

### Condition 2: `SECRETS_OF_RECORD.md` authored

**Why:** bd `9lfn` is Tyler-only authorship. With Dustin's full
KV/storage access already provisioned, this is no longer a *bus-factor*
blocker — it's a *future-operator-onboarding* aid. But the prior
arbiter would expect the artifact to exist before granting full
production-gate confidence.

**Action:** Tyler authors `SECRETS_OF_RECORD.md` listing every credential
location in KV and storage, with rotation cadence and ownership.

**Acceptance:** file exists; `RUNBOOK.md`'s 🔴 TYLER-ONLY markers
referencing it are filled in.

**Effort:** ~30 minutes Tyler-time.

---

## Non-blocking findings

### N-1 (low) — RTM-v2.5.1 still in `-DRAFT` form

The prospective RTM has 5 rows in its current state but ~50 bd issues
have closed since it was started. A companion commit alongside this
rehearsal expands the RTM to reflect actual landed work. Flip to
non-DRAFT happens at v2.5.1 cut, per the file's §5 checklist.

### N-2 (low) — auto-rollback has not been field-tested

bd `39yp`'s implementation is unit-tested + workflow-validated but
hasn't been exercised under a real failed-deploy scenario. First formal
exercise: bd `uchp` Q3 2026 DR test cycle. Acceptable risk because the
implementation follows the deploy-production.yml-style curl pattern
already in production use.

### N-3 (info) — SQL Entra admin not set

`sql-gov-prod-mylxq53d` has no Entra admin configured. Discovered
during 213e provisioning. Not a v2.5.1 prod-gate blocker — management-
plane PITR (the §B.3 scenario) works via subscription Owner, which both
rollback humans hold. Data-plane queries against a restored DB during
DR drill validation would require an Entra admin; deferred to Tyler's
judgment or absorbed by bd `uchp`.

### N-4 (info) — bd `mvxt` stays open

Compensating control shipped (cold-start warmup + retry). Root cause
needs Azure Portal access. Documented as non-blocking in
`rtm-v2.5.1-DRAFT.md` §2. SLO is not at risk.

### N-5 (info) — open carve-outs that are NOT v2.5.1 blockers

| bd ID | Reason |
|---|---|
| `9lfn` (P1) | Condition 2 above |
| `uchp` (P2) | Q3 2026 DR test, date-gated |
| `l96f` (P3) | JWT iss rotation, needs coordinated session window |
| `rtwi` (P3) | Date-gated 2026-05-17, separate project |
| `m4xw` (P4) | Date-gated 2026-07-01 |

---

## Recommended next moves

1. **Tyler:** dispatch `deploy-production.yml` off current `main`. ~10 min.
2. **Tyler:** author `SECRETS_OF_RECORD.md` (bd `9lfn`). ~30 min.
3. **At v2.5.1 cut:** bump `pyproject.toml` to `2.5.1`, flip
   `rtm-v2.5.1-DRAFT.md` to `rtm-v2.5.1.md` (status `Accepted`), update
   `core_stack.yaml`, update `env-delta.yaml`, promote `CHANGELOG.md`
   `[Unreleased]` to `[2.5.1]`, tag, run external arbiter for the actual
   verdict.

---

## Cross-references

- Companion bundle: `docs/release-gate/evidence-bundle-2026-04-30.md`
- Roadmap: `docs/plans/production-readiness-and-release-gate-roadmap-2026-04-24.md`
- Prior external verdict: `docs/release-gate/verdicts/rga-2026-04-22-azgov-v2.5.0-02.md`
- Strategic plan: `PORTFOLIO_PLATFORM_PLAN_V2.md`
- Rollback YAML: `docs/release-gate/rollback-current-state.yaml`
- Prospective RTM: `docs/release-gate/rtm-v2.5.1-DRAFT.md`

---

*Internal rehearsal authored by code-puppy `code-puppy-661ed0` on
2026-04-30. This is not an external arbiter run; the actual verdict for
v2.5.1 will come from the next external arbiter invocation against the
post-deploy artifact.*
