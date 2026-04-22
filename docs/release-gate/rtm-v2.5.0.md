# Requirements Traceability Matrix — v2.5.0 Release

**Scope**: commits in `v2.5.0..79d72c4` (release promotion artifact).
**Tickets in scope**: 64 bd issues (61 closed, 3 open).
**Generated**: 2026-04-22, validated against `.beads/issues.jsonl` + `git log`.
**Consumer**: release-gate-arbiter (Pillar 1 — Requirements Closure).

> **How to read this**: each row is a requirement (bd ticket) with the 
> commits that implemented it and the evidence surface that validates it.
> Validation evidence is a *category* (tests/, alembic/, ci-workflow, bicep,
> app-code, docs) showing *where* the change landed — exhaustive per-test
> coverage is out of scope for a retroactive RTM.

---

## Summary

| Metric | Count |
|---|---|
| Total tickets in release window | 64 |
| Closed (work complete) | 61 |
| Open (carve-outs) | 3 (`7mk8`, `mvxt`, `rtwi`) |
| Themes | 9 |

### Work by theme

| Theme | Tickets |
|---|---|
| Design system overhaul (ADR-0005) | 27 |
| Other | 7 |
| Infrastructure / deployment | 6 |
| Ops / cost optimization | 6 |
| Cost modeling | 5 |
| CI / test infrastructure | 5 |
| Observability & health signals | 4 |
| Code hygiene / refactor | 3 |
| Security & supply chain | 1 |

---

## Detailed traceability

### Design system overhaul (ADR-0005)

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `bvvu` | P1 | ✅ closed | EPIC: Design system overhaul — adopt HTT ds-template standard (ADR-0005) | `6fa2e43` `c5c0f17` `d4f8ca9` | app-code, docs, tests |
| `iwok` | P1 | ✅ closed | Phase 1: Replace CSS foundation (design-tokens.css + Tailwind v3) | `6fa2e43` `9b04f96` `c5c0f17` | app-code, docs, tests |
| `oxfd` | P1 | ✅ closed | Phase 2: Build ds-template Jinja macros (10 primitives) | `6fa2e43` `b2803e3` | docs |
| `xdq6` | P1 | ✅ closed | Phase 3: Migrate all page templates to ds-template primitives | `4a8b0db` `6fa2e43` | docs |
| `py7u` | P2 | ✅ closed | Phase 4: Dark mode, WCAG audit, component docs, screenshot parity | `2dca84a` `2f539c4` `5c82c71` (+4 more) | ci-workflow, docs, tests |
| `py7u.1` | P2 | ✅ closed | Phase 4a: Migrate long-tail pages to ds primitives | `0142a2d` `37ec066` `97571df` (+2 more) | app-code, tests |
| `py7u.1.1` | P2 | ✅ closed | Phase 4a-i: Quick-win wm-* cleanup (4 files, 6 refs) | `0142a2d` `37ec066` `9bd9839` | tests |
| `py7u.1.2` | P2 | ✅ closed | Phase 4a-ii: Migrate loading.html component library off wm-* (21 refs) | `0142a2d` `37ec066` | _(no tracked surface)_ |
| `py7u.1.3` | P2 | ✅ closed | Phase 4a-iii: Migrate preflight.html to ds primitives (47 refs) | `0142a2d` `37ec066` `5640856` (+2 more) | app-code, tests |
| `py7u.1.4` | P2 | ✅ closed | Phase 4a-iv: Migrate Riverside pages + partials to ds primitives | `0142a2d` `091bf58` `37ec066` (+1 more) | app-code |
| `py7u.1.5` | P2 | ✅ closed | Phase 4a-v: Migrate dmarc_dashboard.html to ds primitives (21 refs, may split) | `0142a2d` `37ec066` `a038d91` | app-code |
| `py7u.2` | P2 | ✅ closed | Phase 4b: Add DataTable/Modal/Tabs/FormField/Toolbar ds primitives | `2dca84a` `78db6f3` `85be700` (+2 more) | app-code, tests |
| `py7u.2.1` | P2 | ✅ closed | Phase 4b-i: Split ds.html into layout/display/forms concern files (SERIAL GATE) | `08dd403` `683747b` `85be700` (+1 more) | app-code, tests |
| `py7u.2.2` | P2 | ✅ closed | Phase 4b-ii: Add ds_static_table primitive for pre-populated tables | `2dca84a` `dd1f176` `eed2629` (+1 more) | app-code, tests |
| `py7u.2.3` | P2 | ✅ closed | Phase 4b-iii: Add ds_modal primitive using native <dialog> | `2dca84a` `36916a0` `7b98901` (+1 more) | app-code, tests |
| `py7u.2.4` | P2 | ✅ closed | Phase 4b-iv: Add ds_tabs + ds_tab_panel primitives | `2dca84a` `85be700` `f0378f5` (+1 more) | app-code, tests |
| `py7u.2.5` | P2 | ✅ closed | Phase 4b-v: Add ds_form_field primitive + .ds-input utility | `0908876` `13458fa` `2dca84a` (+2 more) | app-code, tests |
| `py7u.2.6` | P2 | ✅ closed | Phase 4b-vi: Add ds_toolbar primitive for page action bars | `0908876` `1c6a483` `2dca84a` (+1 more) | app-code, tests |
| `py7u.2.7` | P2 | ✅ closed | Phase 4b-vii: Adopt ds_static_table across 9 files with bespoke tables | `2dca84a` `5e050e2` `6308b3d` (+9 more) | app-code, tests |
| `py7u.3` | P2 | ✅ closed | Phase 4c: WCAG 2.2 AA compliance audit | `15ec654` `2dca84a` `9feed8a` (+1 more) | app-code, docs, tests |
| `9v9u` | P3 | ✅ closed | fix(ds): normalize 'border-theme' ghost class (20 sites) to border-default | `5e050e2` `9133246` `fa11590` | app-code, tests |
| `dais` | P3 | ✅ closed | obs: c56t phase 2 — add remaining sync domains + Azure Monitor alert rule | `08a4735` `e35ec35` `f3e21da` | app-code, tests |
| `hikx` | P3 | ✅ closed | feat(ds): extend ds_table with header-slot pattern for badges & filter actions | `5e050e2` `8a0e503` `9133246` (+2 more) | app-code, tests |
| `py7u.4` | P3 | ✅ closed | Phase 4d: Playwright visual diff automation vs. Domain-Intelligence baseline | `15ec654` `2dca84a` `83d3ce9` (+1 more) | app-code, docs, tests |
| `py7u.5` | P3 | ✅ closed | Phase 4e: Remove css_generator.py fallback paths | `9feed8a` `e41b578` | app-code, tests |
| `cwxu` | P4 | ✅ closed | feat(ds): add danger/theme-variant support to ds_table for riverside_dashboard g | `5e050e2` `9133246` `d072fd9` (+1 more) | app-code, tests |
| `hbvt` | P4 | ✅ closed | feat(ds): add skeleton-row variant to ds_table for admin_dashboard users table | `17cc110` `5e050e2` `98cc71f` | app-code, tests |

### Other

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `acr` | P1 | ✅ closed | P7.25: Update inline documentation - docstrings and comments | `399c209` `6ab2261` | app-code, bicep, ci-workflow, docs |
| `2nd` | P2 | ✅ closed | Verify mobile nav script in all HTML files | `091bf58` `9133246` | app-code |
| `igi` | P2 | ✅ closed | Grant RBAC Reader role on BCC/FN/TLL subscriptions for multi-tenant sync SPs | `65517d8` | docs |
| `ddr1` | P3 | ✅ closed | Tyler decision: blue-green-deploy.yml disposition (see ADR 0001) | `b056303` `f4931b4` `f668ab3` | ci-workflow, docs |
| `hofd` | P3 | ✅ closed | arch: decide fate of `blue-green-deploy.yml` — deploy jobs silently failing on u | `2b9a220` `2d34596` `650cf56` (+6 more) | ci-workflow, docs |
| `77af` | P4 | ✅ closed | chore: refresh .secrets.baseline to fix line-number drift | `8e4d403` `a84b37b` | _(no tracked surface)_ |
| `ncxl` | P4 | ✅ closed | fix(api): FastAPI app description renders as code block in Swagger UI | `276ddf4` `e56b35f` | app-code, tests |

### Infrastructure / deployment

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `kj0p` | P2 | ✅ closed | Bicep: resolve remaining architectural/schema warnings (~40) | `1ec0b7c` `83e4e7e` `bbcc6b6` (+2 more) | bicep, tests |
| `sf24` | P2 | ✅ closed | infra: parameters.production.json has enableRedis=true booby trap — Bicep redepl | `0f47f33` `399c209` `650cf56` (+3 more) | app-code, bicep, ci-workflow, docs |
| `dv90` | P3 | ✅ closed | infra: fix 5 Bicep templates that fail az bicep build | `2b0d6ca` `5415662` | bicep, tests |
| `gz6i` | P3 | ✅ closed | ops: migrate dev app from acrgovernancedev → GHCR (then delete the ACR) | `08a4735` `d4f8ca9` `f9b906c` | bicep, docs |
| `mrgy` | P3 | ✅ closed | infra: Bicep param drift — enableAzureSql=false in dev+staging but SQL servers d | `92c5b1c` `f4931b4` | bicep |
| `265y` | P4 | ✅ closed | ops: GHCR repository path inconsistency (tygranlund vs htt-brands) | `399c209` `92c5b1c` `f4931b4` | app-code, bicep, ci-workflow, docs |

### Ops / cost optimization

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `mvxt` | P2 | 🟡 open | ops(staging): Deploy to Staging validation suite consistently times out on every | `a5fce6a` `aef22cf` | docs |
| `rtwi` | P3 | 🟡 open | ops: stop domain-intelligence App Service + pause PG if zero-traffic at 60-day m | `08a4735` `d4f8ca9` `f9b906c` | bicep, docs |
| `ajp1` | P2 | ✅ closed | ops: scheduler sync jobs were silently failing in prod for weeks (libodbc) | `1c1bd54` `2abafa4` `2d34596` (+3 more) | docs |
| `832c` | P3 | ✅ closed | ops: rename rg-identity-puppy-prod — contains shared HTT-brand secrets, not iden | `08a4735` `10b1d11` `46113ca` (+1 more) | _(no tracked surface)_ |
| `c7aa` | P3 | ✅ closed | ops: DCE tenant configured in tenants.yaml but missing from DB — reconcile confi | `143014e` `2d34596` `900c3dc` | _(no tracked surface)_ |
| `ll49` | P3 | ✅ closed | ops: verify dev ACR image lifecycle policy + clean up stale tags | `08a4735` `10b1d11` `6ab2261` (+2 more) | bicep, docs |

### Cost modeling

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `occx` | P2 | ✅ closed | cost: optimize Cosmos DB htt-domain-intel-db (13 containers × 400 RU/s = $148/mo | `3e325cf` `46113ca` | _(no tracked surface)_ |
| `zj9k` | P2 | ✅ closed | launch: build production cost model — starting tier + scaling inflection points  | `0f47f33` `17d411c` `2abafa4` (+6 more) | bicep, docs |
| `5xd5` | P3 | ✅ closed | ops: grant Cost Management Reader role on BCC/FN/TLL subscriptions — costs sync  | `2d34596` `65517d8` | docs |
| `fuy4` | P3 | ✅ closed | docs: sweep stale/wrong cost claims in research docs (B1 slots, S1 East US prici | `f2eaaf7` `f4931b4` | docs |
| `w1cc` | P3 | ✅ closed | ops: audit domain-intelligence RG for further cost optimization | `08a4735` `10b1d11` `f21f8d6` | _(no tracked surface)_ |

### CI / test infrastructure

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `6o4g` | P1 | ✅ closed | fix(tests): update test_frontend_e2e.py assertions after py7u design-system migr | `5c82c71` `79d72c4` `a5fce6a` | ci-workflow, docs, tests |
| `86l1` | P1 | ✅ closed | fix(ci): gh-pages-tests workflow cache-dependency-path after py7u package.json m | `a5fce6a` | docs |
| `6699` | P3 | ✅ closed | ci: add image-label guard to fail builds that produce dev image into :latest/:ma | `0850d9a` `08a4735` `1c1bd54` (+5 more) | ci-workflow, docs |
| `yil1` | P3 | ✅ closed | ci: extend a1sb guard coverage — container-registry-migration.yml + capture buil | `0850d9a` `2d34596` `4c7a75a` (+1 more) | ci-workflow |
| `zsf8` | P4 | ✅ closed | chore(tests): auto-set ENVIRONMENT=development in tests/conftest.py | `9bd9839` `a84b37b` | tests |

### Observability & health signals

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `c56t` | P2 | ✅ closed | obs: extend /api/v1/health/data to cover all 10 sync domains (DMARC + Riverside) | `2d34596` `e35ec35` `f3e21da` (+1 more) | app-code, tests |
| `3cs7` | P3 | ✅ closed | obs: deploy Azure Monitor alert for /health/data any_stale=true → governance-ale | `06d3b1e` `08a4735` `d4f8ca9` (+2 more) | app-code, bicep, docs, tests |
| `a1sb` | P3 | ✅ closed | ops: prod app-governance-prod /api/v1/health returns 500 | `0850d9a` `10b1d11` `1c1bd54` (+11 more) | app-code, ci-workflow, docs, tests |
| `6wyk` | P4 | ✅ closed | ops: add Teams incoming webhook to governance-alerts action group | `10b1d11` `d4f8ca9` `f9b906c` | bicep, docs |

### Code hygiene / refactor

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `6oj7` | P3 | ✅ closed | refactor: split 3 Python files that exceed the 600-line policy | `0aeb6c9` `81920a3` `88f1a1a` (+1 more) | app-code, tests |
| `f8f2` | P3 | ✅ closed | refactor(riverside): remove duplicate JS string-template tables (reuse HTMX part | `5e050e2` `9133246` `98cc71f` (+1 more) | app-code, tests |
| `t3re` | P3 | ✅ closed | refactor(chassis): migrate base.html + partials/nav.html off remaining wm-* toke | `37ec066` | _(no tracked surface)_ |

### Security & supply chain

| bd ID | P | Status | Title | Commits | Validation surface |
|---|---|---|---|---|---|
| `7mk8` | P1 | 🟡 open | security(supply-chain): implement SLSA L3 + Sigstore cosign + SBOM in release-pr | `aef22cf` | docs |

---

## Carve-outs (open tickets at gate time)

Three bd tickets remain open at submission time. Each has explicit
release-gate handling documented in `submission-v2.5.0.md §6`:

| bd ID | P | Title | Gate impact |
|---|---|---|---|
| `7mk8` | P1 | SLSA L3 + cosign + SBOM in release-production workflow | **HARD BLOCK for prod transition.** 1–2 engineer-days. Acceptable to defer for staging gate per HTT 'start advisory' posture. |
| `mvxt` | P2 | Staging validation suite intermittent ReadTimeouts | **Blocks full-green staging-workflow claim.** Environment-coupled (reproduces on docs-only commits); requires Application Insights access to root-cause. |
| `rtwi` | P3 | Stop domain-intelligence App Service at 60-day mark (~2026-05-17) | **None** — future-dated ops task. |

---

## RTM generation method (reproducible)

```bash
# 1. Enumerate bd short-IDs from current issues.jsonl
# 2. Grep commit messages in v2.5.0..HEAD for those IDs
# 3. Cross-reference each match with ticket status + priority + title
# 4. Bucket by theme via title keyword heuristics
# 5. Compute validation surface from `git show --name-only` touched dirs
```

This matrix was generated from 134 commits in the v2.5.0..79d72c4 range.
It is an **imperfect retroactive view** — HTT's SDLC methodology
(Epic 1-5 per `TRACEABILITY_MATRIX.md`) expects prospective RTMs where
the requirement row is created *before* implementation. This one is
backfilled for release-gate-arbiter Pillar 1 compliance. Going forward,
the generator script should run as part of the pre-release gate itself.