# Session Handoff — 2026-04-17 (late afternoon)

**Branch:** `main` · clean · pushed (HEAD `c321525`)
**Backlog:** 4 ready issues, all P3/P4, all genuinely deferrable
**Stashes:** none

---

## What got done this session

### Closed (5 issues, 6 commits)

| Commit | Issue | What |
|---|---|---|
| `0f47f33` | `sf24` | **P0 Redis booby trap defused** — `enableRedis=false` in staging+prod params (was provisioning $80/mo unused Redis cache on next infra deploy) |
| `f668ab3` | (no issue) | Executed ADR 0001 Option C — deleted dead `blue-green-deploy.yml` |
| `f2eaaf7` | `fuy4` | Sweep of stale/wrong cost claims in docs (3 files corrected) |
| `399c209` | `265y` | GHCR path standardized on `htt-brands` across 13 active files |
| `65517d8` | `5xd5` | Cost Management Reader role granted to BCC/FN/TLL SPNs (cross-tenant cost discovery) |
| `143014e` | (carry-over) | Built `scripts/reconcile_tenants.py` — YAML↔DB tenant drift detector |
| `900c3dc` | `c7aa` | Extended reconciler to detect `is_active` drift |
| `92c5b1c` | `mrgy` | Documented Bicep-vs-reality drift table (ADR 0002 Option C) |
| `e35ec35` | `c56t` | `/health/data` Phase 1 — DMARC + Riverside MFA freshness monitoring + 6699 CI guard |
| `6ab2261` | `ll49` | Purged 21 stale tags + 54 manifests from dev ACR (52% storage reduction) |
| `f3e21da` | `dais` | `/health/data` Phase 2 — now monitors **10 sync domains** (DKIM + 3 Riverside snapshot tables added). 98/98 tests pass. |
| `f21f8d6` | `w1cc` | Audited `rg-htt-domain-intelligence` — original cost estimate was **2x overstated** (Cosmos is on free tier). Real spend ~$30/mo, not $65/mo. |
| `c321525` | `832c` | **Renamed** `rg-identity-puppy-prod` → `rg-httbrands-identity-prod` via `az resource move`. Zero downtime, 19 secrets + 4 access policies intact. |

### Filed (carry-outs from completed work)

| ID | Why |
|---|---|
| `gz6i` | Migrate dev app `acrgovernancedev` → GHCR (carved out of `ll49`) |
| `3cs7` | Deploy Azure Monitor alert for `/health/data any_stale=true` (carved out of `dais`) |
| `rtwi` | Stop domain-intelligence App Service if zero-traffic at 60-day mark (~2026-05-17, carved out of `w1cc`) |

---

## Ready backlog (4 issues, all P3/P4)

```
1. [P3] gz6i  ops: migrate dev app acrgovernancedev → GHCR (then delete ACR)
2. [P3] 3cs7  obs: deploy Azure Monitor alert for /health/data any_stale=true → governance-alerts
3. [P3] rtwi  ops: stop domain-intelligence App Service + pause PG if zero-traffic at ~2026-05-17
4. [P4] 6wyk  ops: add Teams incoming webhook to governance-alerts action group
```

**No urgent work.** All P0/P1/P2 issues are closed. The platform is in steady state.

---

## Next session pickup notes

### If you want to keep momentum:
- **`gz6i`** is the highest-leverage P3 — saves $5/mo and unifies image source. Needs a GHCR PAT setup (Tyler-gated). The hard work was already done in `ll49` (ACR is purged of stale junk; only the "current" image needs migrating).

### If you want strategic work instead:
- **`3cs7`** has a 3-option design discussion baked into the issue body (telemetry-driven vs availability test vs scheduled query). Pick A/B/C and execute. Recommended: Option A (telemetry-driven).

### Cron-style follow-up:
- **`rtwi`** is calendar-triggered. Run the verification command in the issue body around 2026-05-17. If still zero traffic → execute the stop recipe.

### Whenever Tyler is in the Teams admin UI:
- **`6wyk`** is the only thing blocked on a UI click (incoming webhook setup). Drop it in conversation when you're already there.

---

## Health of the platform

✅ All P0/P1/P2 closed
✅ Tests: 98/98 health passing (was 94 at session start)
✅ `/health/data` now monitors **10 of 10 sync domains** (was 4 at session start)
✅ Infra docs reflect reality (no more inflated $65/mo claims, no more stale RG names)
✅ Tenant drift detection automated (`scripts/reconcile_tenants.py`)
✅ Cross-tenant cost discovery wired up (BCC/FN/TLL SPNs have Cost Mgmt Reader)
✅ ACR storage cleaned (52% reduction in dev ACR)
✅ KV moved to properly-named RG (no more "identity-puppy" misnomer)

The boring kind of healthy. Good thing.

— Richard 🐶
