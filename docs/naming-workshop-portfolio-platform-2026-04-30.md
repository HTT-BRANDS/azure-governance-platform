# Naming Workshop — HTT Portfolio Platform

**Date:** 2026-04-30  
**Branch:** `naming-workshop-portfolio-platform`  
**Author:** Richard (`code-puppy-661ed0`)  
**Status:** Discovery artifact, not final naming decision  

> This is a naming discovery exercise grounded in repo reality and lightweight
> public collision checks. It is **not** legal advice, trademark clearance, or a
> substitute for counsel / paid clearance databases. We are avoiding obvious
> collisions, not pretending a shell script is a lawyer in a tiny hat.

---

## 1. Product truth from the repo

The current repo is more than an Azure dashboard. It is an HTT-owned platform
that is already operating as a multi-tenant governance hub and is strategically
moving toward a multi-provider portfolio operations layer.

Evidence from current docs/code:

- `PORTFOLIO_PLATFORM_PLAN_V2.md` defines the platform as an HTT-owned
  Portfolio Platform, with Riverside as one evidence consumer rather than the
  product identity.
- `AGENT_ONBOARDING.md` describes the current platform as a FastAPI/HTMX
  multi-tenant governance hub reading five HTT tenants with zero stored client
  secrets.
- `INFRASTRUCTURE_END_TO_END.md` documents live production/staging/dev Azure
  infrastructure, GitHub Actions, OIDC federation, and 5 brand tenants.
- `domains/*/README.md` defines six bounded contexts:
  - `cost`
  - `identity`
  - `compliance`
  - `resources`
  - `lifecycle`
  - `bi_bridge`
- `.github/workflows/backup.yml`, deploy workflows, Bicep IaC, runbooks, and
  status docs show this is an operational platform, not a slideware concept.

Current HTT tenants / brands documented in the repo:

| Code | Brand / tenant |
|---|---|
| `HTT` | Head-To-Toe |
| `BCC` | Bishops |
| `FN` | Frenchies |
| `TLL` | The Lash Lounge |
| `DCE` | Delta Crown Extensions |

Current capability clusters:

| Cluster | Current / planned value |
|---|---|
| Cost | Azure cost aggregation, budgets, anomalies, reservations, chargeback/showback; future Pax8/SaaS reconciliation. |
| Identity | Entra user/admin/MFA/guest/license/cross-tenant access visibility; future CIEM-style governance. |
| Compliance | Continuous evidence, policy/compliance scoring, Riverside-ready views, custom rules. |
| Resources | Inventory, tagging, quotas, lifecycle events, recommendations, provisioning standards. |
| Lifecycle | Brand/tenant onboarding, self-service Lighthouse delegation, config-as-code reconciliation, future acquisition playbooks. |
| BI bridge | Safe exports, dashboards, future bridges to `httbi` and `DART`. |
| Operations | CI/CD, health checks, backup/RPO evidence, DR/runbook/onboarding continuity docs. |

The strongest naming direction should therefore support:

1. **Multi-brand portfolio management** — not just one tenant, not just one brand.
2. **Hub-and-spoke / orchestration** — many providers, tenants, brands, evidence
   streams, and operators converge.
3. **Provider-neutral growth** — starts in Azure/M365, but should not sound
   Azure-only if Google Cloud, AWS, Pax8, SaaS, Power BI, DART, or other systems
   join later.
4. **Evidence and governance** — the platform produces receipts, not vibes.
5. **Health/beauty friendliness** — HTT's portfolio is service/beauty/franchise
   oriented, so the name should not sound like a missile system unless we want
   salon operators to quietly hate us.

---

## 2. Market / buyer framing

HTT is the immediate owner and first user. But the pattern generalizes.

Potential future audiences:

| Audience | Why this platform matters |
|---|---|
| Multi-brand franchisors | Need cross-brand visibility without flattening every brand into one tenant or one operating model. |
| Franchise operators in beauty/wellness | Need cost, identity, compliance, and onboarding repeatability across locations and brand concepts. |
| Portfolio companies | Need evidence-ready reporting for PE owners, leadership, auditors, and MSP partners. |
| Azure-first orgs | Need Entra/Azure Cost/Azure Policy/Azure Resource Graph visibility across tenants/subscriptions. |
| Google-first orgs | Could use the same bounded contexts with Google Cloud Billing/IAM/Asset Inventory/SCC adapters. |
| Hybrid orgs | Need one portfolio hub across Azure, Google Cloud, AWS, M365, Pax8, SaaS, BI systems, and acquisition playbooks. |

The category is not simply "cloud management." More precise category language:

- portfolio operations hub
- multi-brand infrastructure governance
- multi-tenant evidence platform
- franchise portfolio ops layer
- cross-provider governance and evidence hub
- brand lifecycle and cloud governance platform

---

## 3. Naming principles

A good name should be:

1. **Provider-neutral** — avoid `Azure`, `Entra`, `CloudOps` if we want Google / AWS / SaaS coverage later.
2. **Portfolio-native** — imply many brands/tenants/locations feeding one operating surface.
3. **Operational, not theatrical** — `Control Tower` was evocative but collides with AWS and over-indexes on command/control.
4. **Human enough for health/beauty** — salon/franchise leaders should not need a Kubernetes dictionary to say it.
5. **Extensible** — should support modules like Cost, Identity, Compliance, Lifecycle, BI Bridge.
6. **Diligence-friendly** — low obvious collision across domains/packages/repos/search snippets.

Names to avoid by principle:

- `Control Tower` — direct AWS Control Tower collision.
- `Dispatch` — too generic and already used heavily in tech/product language.
- `CloudFolio` / `CloudOps` / `Nexus` / `Atlas` / `Prism` / `Aegis` — too crowded.
- Any name implying Azure-only scope.

---

## 4. Collision-check methodology

I added two reproducible local research scripts:

- `research/naming_collision_check.py`
- `research/naming_web_snippet_check.py`

Generated outputs:

- `research/naming_collision_check_2026-04-30.json`
- `research/naming_web_snippet_check_2026-04-30.md`

Signals checked:

| Signal | What it catches | Limitation |
|---|---|---|
| DNS resolution for `.com`, `.io`, `.app`, `.dev`, `.cloud`, `.ai` | Common-domain occupation / obvious domain conflicts | DNS presence does not mean trademark conflict; no DNS does not mean available to register. |
| PyPI exact project lookup | Python package exact-name collision | Package name collision is not trademark clearance. |
| npm exact package lookup | JavaScript package exact-name collision | Same limitation. |
| GitHub repository search | Rough open-source/project-name crowding | GitHub unauthenticated API can rate-limit; counts are approximate. |
| DuckDuckGo HTML snippets for shortlist | Obvious public product/search collisions | Search results vary and are incomplete. |

Required next steps before final external/commercial use:

1. USPTO TESS / Trademark Center search.
2. State trademark / business entity search if selling in US.
3. Domain registrar availability check for chosen TLDs.
4. Legal review for final mark and category.
5. Social handle check.
6. Customer confusion check against cloud/provider ecosystem names.

---

## 5. Collision results summary

Raw output lives in `research/naming_collision_check_2026-04-30.json`. Summary:

| Name | DNS hits checked common TLDs | PyPI | npm | GitHub repo count | Initial risk read |
|---|---:|---|---|---:|---|
| `switchyard` | 5/6 | exists | exists | 157 | Worse than V2 assumed. Still conceptually good, but not unique. |
| `aerie` | 6/6 | exists | exists | 532 | Too occupied; also strong consumer/retail association. |
| `hangar` | 6/6 | exists | exists | 1403 | Too crowded; known tech usages. |
| `dispatch` | 6/6 | exists | exists | 21305 | Avoid. Very crowded. |
| `meridian` | 6/6 | exists | exists | 3390 | Too crowded for a distinctive platform mark. |
| `concourse` | 5/6 | exists | exists | 3631 | Strong metaphor, but very crowded. |
| `waypoint` | 6/6 | exists | exists | 3537 | Crowded; HashiCorp association risk. |
| `switchboard` | 6/6 | exists | exists | 1256 | Good metaphor, too occupied. |
| `crossdock` | 4/6 | clear | clear | 46 | Logistics meaning; some cloud/search overlap. Medium. |
| `yardmaster` | 2/6 | clear | clear | 17 | Railway ops metaphor; distinctive-ish, but maybe too industrial. |
| `relaydeck` | 2/6 | clear | clear | unavailable in run | Good coined ops metaphor; needs deeper search. |
| `loomline` | 2/6 | clear | clear | 2 | Soft/brand-friendly, but less governance-specific. |
| `brandyard` | 0/6 | clear | clear | 0 | Strong uniqueness signal; brand/yard metaphor is relevant. |
| `tenantforge` | 3/6 | clear | clear | 6 | Descriptive; possibly too technical / tenant-specific. |
| `fleetglass` | 1/6 | clear | clear | 0 | Good "single pane" metaphor; fleet may imply vehicles/devices. |
| `hubwright` | 0/6 | clear | clear | 2 | Very low collision; implies crafted hub. Maybe obscure. |
| `brandplane` | 2/6 | clear | clear | 2 | Simple but slightly generic / awkward. |
| `operatorium` | 0/6 | clear | clear | 1 | Unique and memorable; maybe too clever/Latin. |

Important correction to V2 §11:

> V2 says Switchyard had "nearly zero collisions in cloud space." The lightweight
> check does **not** support treating Switchyard as uniquely clear. It has common
> domains resolving, exact PyPI/npm packages, and 157 GitHub repo hits. That does
> not automatically kill it, but it means it needs real diligence before use.

---

## 6. Candidate families

### Family A — Hub / convergence metaphors

Best for: central platform across providers, tenants, brands, and evidence streams.

| Candidate | Notes |
|---|---|
| `Hubwright` | Coined-ish: someone/something that builds and maintains the hub. Very low collision. Works for multi-cloud and portfolio operations. Slightly obscure, but learnable. |
| `Portico` | Welcoming entryway metaphor; too crowded in collision sweep. Not recommended. |
| `Concourse` | Beautiful hub metaphor; too crowded. Not recommended unless internal-only. |
| `Switchboard` | Very clear central routing metaphor; too crowded. Not recommended. |

### Family B — Brand portfolio metaphors

Best for: franchisors, health/beauty portfolios, multi-brand operations.

| Candidate | Notes |
|---|---|
| `Brandyard` | Strong uniqueness signal: 0 DNS hits across checked TLDs, no PyPI/npm, 0 GitHub repo hits. Suggests a place where brands are organized, routed, serviced. Slightly industrial because of "yard," but less cold than Switchyard. |
| `BrandPlane` | Provider-neutral and brand-aware, but awkward. Could be confused with planning software. |
| `Portfolium` | Sounds right, but avoid: already an established education/portfolio product name. |
| `CloudFolio` | Too cloud-literal and multiple DNS hits; also provider scope narrower than desired. |

### Family C — Operations / orchestration metaphors

Best for: infrastructure governance, routing, execution, operator workflow.

| Candidate | Notes |
|---|---|
| `RelayDeck` | Good operational metaphor: relays signals/actions, deck as operator surface. Low package collision, but DNS partially occupied. Needs deeper search. |
| `Yardmaster` | Railway operator controlling switching yards. Low package collision. Maybe too male/industrial and not health/beauty friendly. |
| `Crossdock` | Logistics hub metaphor for fast transfer between systems/providers. Could be useful for integrations, but may sound too warehouse-specific. |
| `Operatorium` | Unique, memorable, playful. But may be too whimsical for an enterprise governance platform. |

### Family D — Visibility / evidence metaphors

Best for: single pane, auditability, receipts, executive visibility.

| Candidate | Notes |
|---|---|
| `FleetGlass` | "Glass" = visibility, "fleet" = managed estate. Very low collision. More enterprise/infrastructure than beauty/franchise. |
| `Aerie` | Vision/nest metaphor, but collision sweep says too occupied and spelling may be annoying. |
| `Meridian` | Navigation/status metaphor, but too crowded. |
| `Tessera` | Mosaic tile metaphor for many brands forming one picture, but too crowded. |
| `Loomline` | Soft, beauty-friendly, implies woven data/brands. Low collision. Less obviously infra/governance. |

---

## 7. Recommended shortlist

### 1. Brandyard

**Positioning:** The operating yard where every brand's cloud, identity,
compliance, cost, and lifecycle signals are organized and routed.

Why it fits:

- Explicitly portfolio / brand-aware.
- Works for franchisors and multi-brand companies.
- Provider-neutral: does not say Azure, Google, AWS, cloud, or tenant.
- Keeps a faint echo of `Switchyard` without the direct collision load.
- Very strong initial collision signal in this check:
  - 0/6 checked common TLDs resolved.
  - PyPI exact: clear.
  - npm exact: clear.
  - GitHub repo count: 0.

Risks:

- "Yard" may feel industrial/logistics, not premium health/beauty.
- Needs trademark/domain/social diligence.
- Might need a more polished visual identity to avoid sounding like inventory software.

Possible tagline:

> Brandyard — portfolio operations for multi-brand cloud estates.

Verdict: **Best uniqueness + strategic fit. My top recommendation.**

---

### 2. Hubwright

**Positioning:** A crafted hub for operating multi-brand, multi-provider infrastructure.

Why it fits:

- Provider-neutral.
- Low collision signal:
  - 0/6 checked common TLDs resolved.
  - PyPI/npm clear.
  - GitHub repo count: 2.
- Implies intentional construction, governance, and maintenance.
- Avoids sounding like a generic cloud/SaaS product.

Risks:

- Less instantly obvious. People may ask "what is a hubwright?"
- More artisan/tooling vibe than portfolio/franchise vibe.
- Could feel like an agency/service brand rather than software platform.

Possible tagline:

> Hubwright — the crafted operating hub for brand portfolios.

Verdict: **Best uniqueness + platform-craft vibe. Strong second choice.**

---

### 3. FleetGlass

**Positioning:** A clear pane of glass across the whole managed estate.

Why it fits:

- Excellent for infrastructure visibility and governance.
- Provider-neutral.
- Low collision signal:
  - 1/6 checked domains resolved.
  - PyPI/npm clear.
  - GitHub repo count: 0.
- Makes sense for Azure/GCP/AWS/SaaS inventory, cost, identity, compliance.

Risks:

- "Fleet" may imply vehicles/devices rather than brands/franchises.
- Less emotionally aligned with health/beauty portfolio.
- More infrastructure-SaaS sounding than brand-portfolio sounding.

Possible tagline:

> FleetGlass — one view across every brand, tenant, and provider.

Verdict: **Best if we want a more enterprise/infrastructure product feel.**

---

### 4. RelayDeck

**Positioning:** The operator deck where provider signals are routed, reviewed,
and acted on.

Why it fits:

- Strong operator metaphor.
- Works for future `/ask` and `/act` agentic operations.
- PyPI/npm clear.
- Better than `Dispatch` because it is more distinctive.

Risks:

- DNS partially occupied.
- GitHub count unavailable in the run, so needs another pass.
- Less explicitly multi-brand/franchise.

Possible tagline:

> RelayDeck — route every cloud signal to the right brand action.

Verdict: **Interesting, but needs deeper diligence.**

---

### 5. Loomline

**Positioning:** The line that weaves brand, cloud, identity, cost, and evidence
together.

Why it fits:

- More health/beauty friendly than industrial names.
- Low collision signal:
  - 2/6 checked domains resolved.
  - PyPI/npm clear.
  - GitHub repo count: 2.
- Could support a polished brand identity.

Risks:

- Does not immediately say governance/ops/infra.
- May sound like a textile or beauty product rather than platform software.
- Might under-communicate enterprise seriousness.

Possible tagline:

> Loomline — woven operations for multi-brand portfolios.

Verdict: **Best beauty-friendly name, weaker infra clarity.**

---

## 8. Names I would not pick now

| Name | Why not |
|---|---|
| `Control Tower` | AWS Control Tower collision. Dead. Stop poking it. |
| `Switchyard` | Still conceptually good, but collision sweep is much heavier than V2 assumed. Use only after formal clearance. |
| `Aerie` | Very occupied across domains/packages/repos; spelling friction; retail association risk. |
| `Hangar` | Very crowded. |
| `Dispatch` | Extremely crowded and generic. |
| `Meridian` | Crowded and already associated with many companies/products. |
| `Concourse` | Strong but too crowded. |
| `Waypoint` | Crowded; HashiCorp/product association risk. |
| `Portfolium` | Existing known product name. Avoid. |
| `TenantForge` | Clear enough, but too technical and tenant-specific; underplays brands/compliance/BI/lifecycle. |
| `Operatorium` | Unique, but probably too cute unless this becomes a deliberately playful internal product. |

---

## 9. Recommendation

Pick **Brandyard** for the next diligence round.

Why:

1. It is the only candidate in this pass with a clean sweep across checked DNS,
   PyPI, npm, and GitHub repo count.
2. It is portfolio-native: the product manages brands, not just clouds.
3. It keeps the hub/switchyard concept without borrowing `Control Tower` or a
   heavily occupied generic cloud metaphor.
4. It can stretch beyond Azure to Google Cloud, AWS, M365, Pax8, SaaS, BI, and
   acquisition playbooks.
5. It is easier to explain to franchisors than `CIEMHub`, `CloudOps360`, or other
   beige-enterprise oatmeal.

Recommended provisional language:

> **Brandyard** is a portfolio operations hub for multi-brand companies. It gives
> franchisors and portfolio operators one evidence-backed view of cost,
> identity, compliance, resources, lifecycle, and BI signals across Azure,
> Google Cloud, AWS, M365, SaaS, and brand-specific systems.

Internal module naming could become:

- Brandyard Cost
- Brandyard Identity
- Brandyard Compliance
- Brandyard Resources
- Brandyard Lifecycle
- Brandyard BI Bridge
- Brandyard Evidence Bundles

If Tyler dislikes the industrial note in `yard`, choose **Hubwright** as the next
best uniqueness-first fallback.

---

## 10. Next diligence checklist

Before renaming repo/product or buying domains:

1. Search USPTO Trademark Center for exact and similar marks:
   - `BRANDYARD`
   - `BRAND YARD`
   - `BRAND-YARD`
   - `HUBWRIGHT`
   - `FLEETGLASS`
2. Search state business entities where HTT operates if external sale is likely.
3. Check domain registrar availability, not just DNS:
   - `brandyard.com`
   - `brandyard.io`
   - `brandyard.app`
   - `brandyard.dev`
   - `brandyard.cloud`
   - `brandyard.ai`
4. Check social handles:
   - GitHub org/project
   - LinkedIn company page
   - X/Twitter
   - YouTube
5. Search cloud/provider ecosystems:
   - Microsoft marketplace
   - Google Cloud Marketplace
   - AWS Marketplace
   - Azure docs
   - GitHub Marketplace
6. Ask counsel for trademark clearance before any external commercialization.

---

## 11. Proposed decision options for Tyler

| Option | Decision |
|---|---|
| A | Use `Brandyard` as the provisional product name pending formal clearance. |
| B | Use `Hubwright` as the provisional product name pending formal clearance. |
| C | Keep `Portfolio Platform` as working title and run a third naming sprint. |
| D | Keep naming internal-only until Phase 3, but reject the original V2 list as insufficiently unique. |

Richard's recommendation: **A**.

But if your gut says `Brandyard` sounds too warehouse-y for health/beauty,
choose **B** or run a third sprint around softer portfolio words. Do not fall
back to `Switchyard` without real clearance. That cute little train name is more
crowded than it looked. Choo-choo, lawsuit-adjacent caboose.
