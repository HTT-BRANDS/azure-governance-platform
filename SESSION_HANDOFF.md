# Session Handoff — Azure Governance Platform

## Current State (v1.8.1) — Auth Transition In Progress

**Date:** 2026-03-31
**Branch:** main (clean, fully pushed)
**Agent:** code-puppy-eb4bc4

### Live Environments

| Environment | Version | DB | Scheduler | Cache | Azure Auth |
|-------------|---------|-------|-----------|-------|------------|
| **Production** | 1.8.1 ✅ | ✅ healthy | ✅ running | ✅ memory | ⚠️ OIDC broken (AADSTS700236) |
| **Staging** | 1.7.0 ✅ | ✅ healthy | ✅ running | ✅ memory | ⚠️ Same issue |

### Security Posture

| Metric | Value |
|--------|-------|
| CodeQL open alerts | **0** |
| Dependabot open alerts | **0** |
| pip-audit CVEs | **0** |
| Security headers | 7/7 present |
| Auth wall | All protected endpoints return 401 |

### Critical Path — Get Real Data Flowing

**Problem:** `AADSTS700236` — per-tenant OIDC federation is architecturally
broken. Microsoft prohibits Entra ID-issued tokens as FIC assertions across
tenants.

**Solution:** Flip `USE_OIDC_FEDERATION=false` and use client secrets via
Key Vault. The fallback path is fully implemented and tested.

**Runbook:** `docs/runbooks/enable-secret-fallback.md`

**Future roadmap:** `docs/AUTH_TRANSITION_ROADMAP.md`
- Phase A: Client secrets (immediate fix) ← DO THIS NOW
- Phase B: Multi-tenant app + single secret (3-6 months)
- Phase C: UAMI zero-secrets (6-12 months)

### Open Issues (7 total)

| ID | Priority | Type | Title |
|----|----------|------|-------|
| `bn7` | P0 | task | Flip USE_OIDC_FEDERATION=false + configure secrets |
| `oim` | P0 | task | Verify live data flow after auth fix |
| `70l` | P0 | bug | AADSTS700236 cross-tenant token failure (workaround: bn7) |
| `yfs` | P2 | task | Phase B: Multi-tenant app registration |
| `9gl` | P3 | task | Migrate ACR to GHCR |
| `sun` | P3 | task | Phase C: Zero-secrets via UAMI |
| `l5i` | P4 | task | Evaluate Azure SQL Free Tier for staging |

### What Was Done This Session

1. **Full codebase analysis** — 65 route/service files, 40 core modules,
   18 models, 2,975 tests, 239/239 roadmap tasks complete
2. **Root cause identified** — AADSTS700236 is a platform limitation, not config
3. **Created runbook** — `docs/runbooks/enable-secret-fallback.md` (step-by-step)
4. **Created auth transition roadmap** — `docs/AUTH_TRANSITION_ROADMAP.md`
   (3 phases: secrets → multi-tenant app → UAMI zero-secrets)
5. **Updated tenants.yaml.example** — shows `oidc_enabled: false` + KV secret pattern
6. **Filed 3 bd issues** — immediate fix (bn7), Phase B (yfs), Phase C (sun)

## Quick Resume Commands

```bash
cd /Users/tygranlund/dev/azure-governance-platform
# Follow the runbook to get data flowing:
cat docs/runbooks/enable-secret-fallback.md
# Check production health:
curl -s https://app-governance-prod.azurewebsites.net/health/detailed | python3 -m json.tool
# View all open issues:
bd ready
```
