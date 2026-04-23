# Session log — 2026-04-23 · Supply-chain + CI-gate sprint

**Window:** 2026-04-23 (post-v2.5.0-release-gate session)
**Driver:** code-puppy-a5a944 (autonomous)
**Previous session log:** `docs/sessions/2026-04-22-v2.5.0-release-gate.md`

## TL;DR

Closed every P1/P2/P3 ticket that didn't require Azure Portal access or a
time-gated trigger. Production-gate blockers dropped from 1 → 0. Next
arbiter submission should land a clean `PASS` instead of
`CONDITIONAL_PASS`.

## By the numbers

| | |
|---|---|
| Commits | 10 (this session) + 6 (earlier 7mk8 work) = 16 |
| Files changed | 15 |
| Lines | +2,096 / −55 (net +2,041) |
| bd closed | 4 (7mk8, dq49, my5r, x692) |
| bd filed | 1 (dq49 — filed + closed same session) |
| bd mitigated (still open) | 1 (mvxt) |
| bd untouched (date-gated) | 1 (rtwi, trigger 2026-05-17) |
| Unit tests added | 24 (all pass) |
| Workflows touched | 3 (deploy-production, security-scan, bicep-drift-detection) |
| Workflows added | 1 (bicep-drift-detection.yml) |

## Tickets worked

### 🎯 7mk8 — SLSA L3 + Sigstore cosign + SBOM (P1) ✅ CLOSED

Four incremental commits, in produce→consume order:

1. `7d816f6` — **SBOM** via `anchore/sbom-action` (Syft / SPDX-JSON) +
   `actions/attest-sbom@v2` attestation as OCI referrer.
2. `7921b92` — **SLSA L3 build provenance** via
   `actions/attest-build-provenance@v2`. SLSA conformance rationale
   captured in `arbiter/policies/verify.yaml`.
3. `b28a9f2` — **cosign 4-claim verify** in deploy job (fail-closed) +
   `az webapp config container set` pinned to `@<digest>` instead of
   `:<sha-tag>` (closes TOCTOU between verify and pull).
4. `3042624` — **arbiter policy file** + `arbiter/README.md`. The policy
   is the source of truth; the workflow steps mirror it; drift detectable.

The 4 claims enforced on every production attestation:

| # | Claim | Value |
|---|---|---|
| 1 | subject | immutable `sha256:...` digest |
| 2 | predicate type | `slsaprovenance1` AND `spdxjson` (both required) |
| 3 | certificate identity | regex pin: workflow path + `refs/heads/(main\|release/*)` |
| 4 | OIDC issuer | `https://token.actions.githubusercontent.com` exact |

### 🔗 dq49 — SHA-pin supply-chain actions (P3) ✅ CLOSED

Filed + closed same session. `ebb2086`:

- `actions/attest-build-provenance@e8998f94` (v2.4.0)
- `actions/attest-sbom@bd218ad0` (v2.4.0)
- `sigstore/cosign-installer@7e8b541e` (v3.10.1)
- `anchore/sbom-action@e22c3899` (v0.24.0)

Dependabot's `github-actions` ecosystem understands SHA + version-comment
format, so no `dependabot.yml` change. Closes the last
supply-chain-of-trust loop (the tooling itself).

### 📋 my5r — env-delta.yaml schema validator + literal rejection (P2) ✅ CLOSED

`04d0d7b`. 488-line Pydantic v2 validator + 24-test suite.

Key design decisions:

- **StrictBool / StrictInt** on security-sensitive flags. Pydantic v2's
  default would silently coerce `"no"` → `False` on `enable_redis`, which
  is a terrifying category of silent-config-drift bug for a security gate.
- **Path-scoped allowlist** for legitimate long-strings (`container_image`,
  `cors_origins`, commit SHAs). Connection-string rule (`AccountKey=`,
  `Password=`, etc.) fires **even on allowlisted paths** — so a
  `container_image` that somehow ended with `:AccountKey=...` still fails.
- **4 exit codes:** `OK=0 / SCHEMA=1 / LITERAL=2 / IO=3`. Tests assert on
  each boundary.
- **Dual wiring:** pre-commit hook (local Python) + CI job in
  `security-scan.yml` (feeds into `security-summary` overall-status gate).

The test fixtures intentionally look like secrets to prove the validator
catches them — marked `# pragma: allowlist secret` so our own
detect-secrets hook doesn't flag them (peak DevSecOps irony).

### 🏗️ x692 — Scheduled Bicep drift detection (P3) ✅ CLOSED

`fecf0fd`. New workflow `.github/workflows/bicep-drift-detection.yml`.

Runs `az deployment group what-if` weekly (Mon 13:00 UTC / ~9 AM Central)
across a dev/staging/production matrix. `fail-fast: false` so one env's
infra-auth issue doesn't mask another env's real drift.

Triple-notification on drift:

1. **Rolling GitHub issue** — existing open `[drift]` issue gets a new
   comment; no new issue is created per week. Avoids the "every Monday
   I get another issue" noise antipattern.
2. **Optional Teams webhook** gated on `vars.TEAMS_WEBHOOK_CONFIGURED`
   (same pattern `deploy-production.yml` already uses for the prod
   Teams webhook secret).
3. **Workflow failure** so drift shows up in branch-protection /
   required-check views without anyone having to remember to look at
   action runs.

Closes the arbiter's Finding N-3 (IaC-vs-runtime-deploy disconnect, the
latent-footgun pattern that `sf24` and `265y` already demonstrated).

### 🔧 mvxt — staging cold-start timeouts (P2) 🟡 MITIGATED (stays open)

`68c0baa`. `tests/staging/conftest.py` rewrite.

Diagnosis without Azure Portal: a single 10-second health check in the
fixture was being used as a binary is-staging-up gate. On the post-April-16
B1 plan, post-deploy cold-starts routinely exceed 60s, so this fixture
timed out and cascaded into 30+ ReadTimeout errors.

Two-part mitigation:

- **`_warmup_staging()`** — 5 attempts with progressively longer
  timeouts (10/30/60/90/120s) and exponentially longer sleeps between
  (5/10/20/30s). Worst-case ~5 minutes before giving up. Prints progress
  on attempts > 1 so CI logs capture the cold-start trend (useful data
  for the eventual root-cause work).
- **`_build_session()`** — urllib3 `Retry` adapter on the shared session
  for 502/503/504 + connect/read timeouts, **GET/HEAD/OPTIONS only**
  (no silent auto-retry of POST/PUT/DELETE — idempotency is the test's
  concern, not ours).

Ticket stays **OPEN**. This is a compensating control, not a fix. Real
fix needs Application Insights to see the boot logs during cold-start,
plus likely a plan-tier upsize or scheduler-liveness work — both need
Azure Portal access.

## Doc hygiene sweep (same day)

`a7557a4`. Five documents were claiming gaps that no longer exist:

- `core_stack.yaml` — SLSA/cosign/SBOM moved from `absent` → `present`,
  `absent: []` with a policy comment for future additions.
- `docs/security/production-audit.md` — M-3 (No SBOM) marked ✅ CLOSED
  with commit refs; top-of-doc ASVS coverage line updated; conclusion
  verdict rephrased.
- `docs/security/production-audit-v2.md` — M-3 row flipped from
  🔶 DEFERRED to ✅ RESOLVED (resolving an internal inconsistency with
  the top-of-doc summary). OBS-2 struck through. Phase-17 roadmap SBOM
  row marked DONE.
- `CHANGELOG.md` — two new `[Unreleased]` sections capturing the day's
  work + mvxt mitigation under Fixed.

Left intentionally untouched:

- `docs/release-gate/submission-v2.5.0.md` — historical submission;
  updating it would rewrite history. Next submission (v2.5.1) should
  cite the closures prospectively.
- `docs/release-gate/verdicts/rga-2026-04-22-azgov-v2.5.0-02.md` —
  same reasoning; it's an archived arbiter verdict.
- `docs/release-gate/rtm-v2.5.0.md` — same.
- `docs/sessions/2026-04-22-v2.5.0-release-gate.md` — previous session
  log; snapshot in time.

## State of the kingdom

```
Before session:  5 open tickets, 1 prod-gate blocker (7mk8)
After session:   2 open tickets, 0 prod-gate blockers
                 ↳ mvxt   (P2, needs Azure Portal for root-cause)
                 ↳ rtwi   (P3, date-gated to 2026-05-17)
```

**Working tree:** clean.
**Remote `main`:** up-to-date with local after this session.

## What's still Tyler-only

1. **mvxt root cause** — App Insights cold-start inspection. The warmup
   mitigation masks the symptom; real fix probably involves (a) plan
   tier upsize from B1, or (b) scheduler-liveness scaffolding that the
   arbiter waiver notes reference.
2. **rtwi trigger date (2026-05-17)** — at 60-day mark, re-run the
   zero-traffic audit query in the ticket and, if still zero, execute
   the shutdown/pause commands.
3. **Next arbiter submission for v2.5.1** — the prospective RTM should
   cite today's closures. With `7mk8` + `my5r` + `x692` all closed, the
   binding verdict should be `PASS` (not `CONDITIONAL_PASS`). This is
   a Tyler-level authorization decision, not a puppy-level one.

## Artifacts for next session

- New workflow: `.github/workflows/bicep-drift-detection.yml` — first
  scheduled run: Monday 2026-04-27 13:00 UTC. Check that it worked.
- New pre-commit hook: `env-delta-validate` — local runs only fire when
  `env-delta.yaml` or `scripts/validate_env_delta.py` change.
- New CI job: `env-delta-validate` in `security-scan.yml` — runs on every
  push/PR; verify green on first push after this session.
- New policy: `arbiter/policies/verify.yaml` — the 4-claim source of
  truth. If a new predicate type is added to the workflow, add it here
  too.

🐶 Session complete, plane landed, Richard signing off.
