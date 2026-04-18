# Weekly Retro — 2026-04-11 → 2026-04-17

**Branch state at end of week:** `main` clean + pushed (`06d3b1e`), no stale branches, no stashes
**Open issues:** 4 (all P3/P4, all genuinely needing human input — see "Why we stopped" below)

---

## By the numbers

| Metric | Count |
|---|---|
| Commits (no merges) | **91** |
| Issues closed | **30** (P1: 2, P2: 12, P3: 15, P4: 1) |
| Lines added / removed | **+16,651 / −2,747** (net +13,904) |
| Releases shipped | **2** — v2.3.0, v2.5.0 |
| Worktrees / stashes leaked | 0 |

---

## What shipped, by theme

### 1. Two minor releases (Apr 14)

- **v2.3.0** — Granular RBAC (ADR-0011), admin dashboard with user management, role assignment, audit logging. Plus security findings F-01 through F-08 fixed in one sweep (rate-limiting, audit logging on role changes, HTMX partial endpoint, etc.).
- **v2.5.0** — Phase 21+22 "Operational Excellence + Platform Polish" — configurable sync thresholds, Node 22→24 LTS, CodeQL v3→v4, Python 3.11→3.12 active LTS, design-system token enforcement, WCAG 2.2 AA full audit (all 6 new success criteria covered).

### 2. CI hardening week (Apr 14–15)

Repaired four broken workflows in one go (`af15342`, `4bce833`):
- Cross-browser: webkit was choking on >32767px fullPage screenshots
- Accessibility: Chrome/ChromeDriver version mismatch
- Trivy: needed table-format debug step for CVE visibility
- backup.yml: corrupted YAML had a duplicated job definition

Plus security: `apt-get upgrade` in Dockerfile for **CVE-2026-28390 (libssl3)**.

### 3. Strategic launch readiness (Apr 15)

`f156391` — comprehensive launch readiness, costs, and 2-year roadmap doc. Then `2bad295` immediately executed every recommendation it produced. Followup `5a2a7b9`: "strategic audit fully resolved — zero remaining items."

### 4. The big incident response (Apr 17 morning)

This is the spicy part of the week. Three deeply linked discoveries:

- **`a1sb`** — `/api/v1/health` had been returning **500 in prod** because of a SQL query bug. Smoke tests passed because they targeted `/health` (the unauthenticated alias), not `/api/v1/health`.
- **`ajp1`** — Investigation revealed scheduler sync jobs had been **silently failing in prod for weeks** because the prod container was missing `libodbc` (a dev image had been promoted to `:latest`).
- **`6699`** — Root cause: nothing in CI was preventing a dev-tagged image from being deployed as production. Fixed by adding a `verify-production-image` composite action that pins-by-digest before deploy. Wired into both `deploy-production.yml` and `container-registry-migration.yml` (`yil1`).

### 5. Observability sprint (Apr 17 afternoon)

`/api/v1/health/data` evolved from "**doesn't exist / is broken**" to "**monitors all 10 sync domains across 3 timestamp conventions, never 500s, has CI regression guard**":

- **`c56t` Phase 1** — Built the endpoint with 6 domains (resources, costs, compliance, identity, dmarc, riverside_mfa), self-describing `domains_covered` field, isolated per-domain queries (one bad domain doesn't 500 the whole endpoint).
- **`dais` Phase 2** — Added the remaining 4 (dkim, riverside_compliance with `updated_at`, riverside_device_compliance + riverside_threat_data with `snapshot_date`). Three timestamp conventions now coexist in one registry — validates the `(name, Model, ts_col)` tuple design.
- 98/98 health tests pass.

### 6. Cost + infra cleanup (Apr 16–17)

| | What | Saved |
|---|---|---|
| `3e325cf` | Control-tower cleanup + prod SQL downgrade | ~$110/mo |
| `75ac237` | Batch 2 cost optimization | ~$19/mo |
| `46113ca` | Deleted `rg-identity-puppy-dev` | small |
| `occx` | Cosmos DB throughput optimization | (significant) |
| `sf24` | **Defused $80/mo Redis booby trap** in `parameters.production.json` (would have provisioned unused Redis on next infra deploy) | $80/mo deferred |
| `ll49` | Purged 21 stale tags + 54 manifests from dev ACR | 52% storage reduction |
| `w1cc` | Audited `rg-htt-domain-intelligence` — found original cost claim was **2x too high** ($65/mo claimed → $30/mo real, Cosmos is on free tier) | docs corrected |
| `832c` | Renamed `rg-identity-puppy-prod` → `rg-httbrands-identity-prod` via `az resource move`. Zero downtime, 19 secrets + 4 access policies intact. | naming clarity |
| `5xd5` | Granted Cost Management Reader to BCC/FN/TLL SPNs | unblocks cross-tenant cost discovery |

### 7. Doc + governance cleanup (Apr 17 PM)

- **`fuy4`** — Sweep of stale/wrong cost claims across 3 docs (B1 slot pricing, S1 East US pricing).
- **`265y`** — GHCR repo path inconsistency (`tygranlund` vs `htt-brands`) standardized across **13 active files**.
- **`mrgy`** — Documented the Bicep-vs-reality drift table (ADR 0002 Option C). The truth: parameters say `enableAzureSql=false` in dev+staging but the SQL servers exist anyway from earlier provisioning. Now we own that knowledge instead of pretending IaC is the source of truth.
- **`c7aa`** — Built `scripts/reconcile_tenants.py` — YAML↔DB tenant drift detector. Now also detects `is_active` drift (`900c3dc`).
- **`ddr1` + `hofd`** — ADR 0001 produced, then executed (`f668ab3` deletes the dead `blue-green-deploy.yml`).

---

## Why we stopped (the 4 remaining open issues)

| ID | Pri | Why it can't be autonomously closed |
|---|---|---|
| `gz6i` | P3 | Migrate dev app to GHCR — **needs your GHCR PAT** for `DOCKER_REGISTRY_SERVER_PASSWORD` (lives in GitHub secrets, not local). |
| `3cs7` | P3 | Azure Monitor alert for `/health/data` stale data — design choice gated. Audit this session ruled out Option B (auth blocks unauth web test) and weakened Option C (always-200 endpoint can't be distinguished by status code). **Option A (telemetry-driven) is the clear winner** but requires app code change + Bicep deploy — wants your review. Sharpened skeleton + effort estimate (~2h) in the issue notes. |
| `rtwi` | P3 | Calendar-triggered: re-check domain-intelligence-prod traffic on **~2026-05-17**. If still zero → run the stop recipe in the issue body. Saves $28-30/mo while paused. |
| `6wyk` | P4 | Add Teams incoming webhook to `governance-alerts` action group — **needs you in the Teams admin UI** to mint the webhook URL. One `az monitor action-group update` away once you have it. |

**No P0/P1/P2 issues remain open.** Backlog is genuinely low-priority and human-gated.

---

## What got better, structurally

1. **Observability is no longer cosmetic.** A silent 6-week prod outage taught us to treat health endpoints as first-class — `/health/data` now has CI regression guards, never-500 isolation, self-describing payloads, and 10-of-10 domain coverage.
2. **Cost claims are now grounded.** Multiple "we'll save $X/mo" claims got walked back during sweeps. The new bar: don't claim cost numbers without verifying the SKU + free-tier flags.
3. **CI catches dev images going to prod.** The `verify-production-image` composite action is wired into every deploy workflow that targets prod.
4. **Tenant drift is automated.** `scripts/reconcile_tenants.py` flags any YAML↔DB divergence (including soft-delete `is_active` drift).
5. **Bicep-vs-reality drift is now explicit.** No longer pretending IaC is canonical when it isn't.
6. **bd hygiene is excellent.** Every closed issue this week has a closure note explaining what shipped + what was deliberately deferred. New work that grows out of closures is filed as fresh discoverable issues, never lost.

---

## What I'd want next session

In rough priority order (all currently human-gated):
1. **`gz6i`** — drop the GHCR PAT in and let the agent execute the migration.
2. **`3cs7`** — say "go Option A" and the implementation is ~2h of focused work.
3. **`6wyk`** — easy 2-minute follow-up after a Teams admin trip.
4. (Wait until ~May 17 for `rtwi`.)

After those four, the platform is in a state where the only work is feature work or upcoming maintenance windows.

— Richard 🐶
