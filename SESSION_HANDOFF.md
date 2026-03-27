# Session Handoff — Azure Governance Platform

## Current State (v1.7.0) ✅ FULLY DEPLOYED

**Date:** 2026-03-27
**Branch:** main (clean, fully pushed)
**Tag:** v1.7.0

### Live Environments

| Environment | URL | Version | Status |
|-------------|-----|---------|--------|
| **Production** | https://app-governance-prod.azurewebsites.net | v1.7.0 | ✅ healthy |
| **Staging** | https://app-governance-staging-xnczpwyv.azurewebsites.net | v1.7.0 | ✅ healthy |

### Test Results

| Suite | Result |
|-------|--------|
| Unit + Integration | ✅ 2934 passed |
| E2E Headless Audit | ✅ 285 passed, 15 skipped |
| Staging Validation | ✅ 73 passed, 31 skipped |
| Production Smoke | ✅ all passed |
| ruff check | ✅ 0 errors |
| ruff format | ✅ 0 drift |

### CI/CD Pipeline Status

| Workflow | Status |
|----------|--------|
| Deploy to Production | ✅ success (10m53s) |
| Deploy to Staging | ✅ success (10m47s) |

## What Was Fixed This Session

### Blocker 1: pip-audit CVE (CVE-2026-34073)
- `cryptography 46.0.5 → 46.0.6`
- pip-audit now reports: "No known vulnerabilities found"

### Blocker 2: Staging OIDC → ACR Access
Root cause was TWO issues:
1. **Missing `environment: staging`** on `build-image` job — OIDC token subject
   didn't match the `github-actions-staging` federated credential
2. **Missing environment secrets** — staging GitHub environment had NO Azure
   secrets, falling back to repo-level secrets (wrong SP). Fixed by setting
   `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` on the
   staging environment to match the correct SP.

### Blocker 3: Smoke/Validation Test CORS Error
- CI test runners imported app code → triggered `Settings()` validation
- Production mode requires `CORS_ORIGINS` but tests don't need it
- Fixed: added `ENVIRONMENT: development` to smoke/validation test env

### Blocker 4: Staging Container Not Updating
- `az webapp restart` only restarts with cached image
- Added `az webapp config container set` to point to new `:staging` tag
- Now matches production's deploy pattern

## Quick Resume Commands
```bash
cd /Users/tygranlund/dev/azure-governance-platform
git status && git log --oneline -5

# Full test suite
ENVIRONMENT=development uv run pytest tests/unit/ tests/integration/ -q
ENVIRONMENT=development uv run pytest tests/e2e/test_headless_full_audit.py -v

# Verify live
curl -s https://app-governance-prod.azurewebsites.net/health | python3 -m json.tool
curl -s https://app-governance-staging-xnczpwyv.azurewebsites.net/health | python3 -m json.tool

# Deploy status
gh run list --workflow=deploy-staging.yml --limit=3
gh run list --workflow=deploy-production.yml --limit=3
```
