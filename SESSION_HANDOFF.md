# 🚀 SESSION_HANDOFF — Azure Governance Platform

## Current State — v2.5.0 + Critical Prod Fix (a1sb)

**Date:** April 17, 2026
**Agent:** Richard (code-puppy-bf0510) 🐶
**Branch:** main (clean, fully pushed)
**Session Status:** ✅ ALL WORK COMPLETE — PROD RESTORED TO HEALTHY STATE

---

## 🚨 Executive Summary — Prod Was Quietly Broken

What looked like a P3 bug (`/api/v1/health` returns 500) turned out to be a **container build pipeline misconfiguration** that has been silently shipping the **development stage** of the Dockerfile to production for weeks.

| Symptom | Reality |
|---------|---------|
| `/api/v1/health` → 500 | DB import was failing: `libodbc.so.2: cannot open shared object file` |
| `/health` → 200 | Lucky — no DB dependency, doesn't trigger the bad import |
| Dashboards looked sluggish | Scheduler was crashing on every sync run (libodbc) |
| Image labelled `version: 2.5.0` | Actually labelled `2.5.0-dev` — wrong stage entirely |

---

## 🔧 Root Cause + Fix

`.github/workflows/blue-green-deploy.yml` triggers on every push to `main` and builds the container image. Its `docker/build-push-action` step was missing the **`target:` field**.

When you don't specify a target on a multi-stage Dockerfile, Docker Buildx defaults to the **last stage**. The Dockerfile's last stage is `development` (intentional — for `docker compose --target development` workflows). That stage:

- Skips the entire ODBC apt-install layer
- Runs as `root` (not `appuser`)
- Uses `uvicorn ... --reload` (dev-only)
- Tags itself `version: 2.5.0-dev`

These bad images were getting pushed to GHCR as `:latest`, `:main`, and `:<short-sha>`. Production was pinned to `:f156391` (one of these). DB connections crashed at first query.

**Fix:** Added `target: production` to `blue-green-deploy.yml` and a giant warning comment so future-us doesn't break it again.

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    target: production   # ← THE FIX
    ...
```

Other workflows (`deploy-staging.yml`, `deploy-production.yml`) already had `target: production`, which is why **staging was healthy the whole time** — that was the giveaway.

---

## ✅ Verification

After repointing prod from `:f156391` → `:6a7306a` (commit with fix):

```json
GET https://app-governance-prod.azurewebsites.net/api/v1/health
{
  "status": "healthy",
  "version": "2.5.0",
  "environment": "production",
  "checks": {
    "database":  { "status": "healthy", "response_time_ms": 9.1 },
    "cache":     { "status": "healthy", "hit_rate_percent": 100.0 },
    "scheduler": { "status": "healthy", "active_jobs": 10 },
    "azure_configured": true
  }
}
```

3 consecutive smoke-test rounds: `/health` and `/api/v1/health` both 200 in ~400ms.

---

## 🐶 Bonus Discovery — Scheduler Was Dead

Because every DB connection was crashing, **all 10 scheduled sync jobs** (cost, compliance, identity, resources, etc.) had been failing for weeks. Cost/compliance dashboards in prod were stale.

**Filed as `ajp1` (P2):** Investigate data freshness, trigger manual full sync, verify nightly schedules now actually run.

---

## 📋 Open bd Issues

| ID | Pri | Type | Item | Notes |
|----|-----|------|------|-------|
| `ajp1` | **P2** | task | Verify scheduler caught up after libodbc fix | New — discovered this session |
| `832c` | P3 | task | Rename `rg-identity-puppy-prod` | Needs Tyler — RG renames are recreate-only |
| `ll49` | P3 | task | Migrate dev ACR → GHCR + cleanup | Needs decision — option 1 deletes ACR, may break dev |
| `w1cc` | P3 | task | Audit `domain-intelligence` RG ($65/mo idle) | Deferred — revisit when traffic exists |
| `6699` | P3 | task | Add CI guard: fail builds producing dev image into :latest | New — belt-and-suspenders for a1sb |
| `6wyk` | P4 | task | Add Teams webhook to `governance-alerts` action group | Needs Tyler — webhook URL |

---

## 📁 Files Touched This Session

| File | Change |
|------|--------|
| `.github/workflows/blue-green-deploy.yml` | Added `target: production` (the fix) |
| `SESSION_HANDOFF.md` | This rewrite |
| `.beads/issues.jsonl` | Closed `a1sb`, opened `ajp1` + `6699` |

**Azure side (no code):**
- `app-governance-prod` container image: `:f156391` → `:6a7306a`
- App restart triggered, smoke tested healthy

---

## 🛬 Session Landing Checklist

- [x] All commits pushed to `origin/main`
- [x] No stashes, no uncommitted files
- [x] Production verified healthy (`/api/v1/health` 200, DB 9ms, scheduler running)
- [x] bd issues synced (closed `a1sb`, opened `ajp1`, `6699`)
- [x] Docs updated (this file)
- [x] No open PRs

---

## 🎯 Next Session Starting Point

1. **Check `ajp1` first** — verify scheduler actually ran overnight, trigger backfill if data is stale
2. **`bd ready`** to see remaining 5 issues
3. Production is now on `:6a7306a` with the proper production image
4. `:latest` and `:main` GHCR tags are NOW SAFE — they'll point to production-stage images going forward
5. Remaining issues are housekeeping that need Tyler's input or deferred decisions

---

**Last Updated:** April 17, 2026
**Agent:** Richard (code-puppy-bf0510) 🐶
**Mood:** Tail-wagging satisfaction — found a sneaky weeks-long bug 🦴
