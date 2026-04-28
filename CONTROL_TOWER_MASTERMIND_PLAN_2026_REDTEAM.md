# Adversarial Review — CONTROL_TOWER_MASTERMIND_PLAN_2026

**Reviewer:** epistemic-architect (session `epistemic-architect-session-d80ad3`)
**Requested by:** Tyler Granlund via code-puppy-ab8d6a
**Date:** 2026-04-28
**Target document:** [`CONTROL_TOWER_MASTERMIND_PLAN_2026.md`](./CONTROL_TOWER_MASTERMIND_PLAN_2026.md)
**Mode:** Hostile red-team — find what's wrong, do not rewrite, do not flatter.

---

## Verdict (one sentence)

The plan is *strategically coherent and tactically wrong* — the synthesis is
correct, the rebrand reasoning is half-correct, the phase ordering is
backwards, the cost ceiling is fantasy, and the political framing as written
would get Tyler in real career trouble if a Riverside operating partner
read the literal text of this document.

---

## Top 3 fatal flaws

### F1. The IP / employer-ownership question is hand-waved, and it's the only thing on this list that can actually destroy Tyler.

§10: *"Patent / IP strategy — there's defensible IP here ... Out of scope
for engineering. Tyler + legal call."*

This is not a footnote. This is **the** question. Every line of code, every
doc, every architectural pattern, every "44 collectors" that get migrated
forward, every ResilientAzureClient pattern, the cross-tenant identity
graph itself — all of it is being built by a salaried employee, on
employer time, on employer equipment, against employer tenants, using
employer data, in employer-owned GitHub repos. That is **work-for-hire
under default U.S. IP law**. HTT Brands owns it. By extension, Riverside
controls it.

The plan repeatedly frames Control Tower as Tyler's defensible position
("Tyler walks in and wins," "first-mover advantage at the portfolio
level," "the diligence package writes itself"). But Tyler does not own
this work and cannot extract it. If Riverside divests HTT or fires Tyler,
the platform stays. Worse: if Riverside's legal counsel ever reads the
phrasing in §1 ("Riverside is a customer of the platform, not its
brand") next to the §10 dodge on IP, that reads as an employee
positioning company IP as personal leverage. **That framing alone is
grounds for a difficult conversation.**

The "control-tower" name itself — used in a prior internal repo at HTT —
is already prior art owned by HTT. The rebrand isn't even the question;
the IP-extraction strategy is.

This is a **Phase -1** decision. Not a Phase 6 one.

### F2. "Compliance theater" cannot appear in writing in a doc that's about to spawn dozens of bd issues with searchable commit messages.

§1 literally says: *"Annual security read-outs (RISO) treated as compliance
theater."*
§7 Phase 6: *"Riverside read-out becomes a 30-minute demo with receipts,
not a 30-page slide deck. Tyler walks in and wins."*

planning-agent is going to decompose this into bd issues. Those issues
will have titles, descriptions, and acceptance criteria that descend from
this language. Commit messages will reference them. PRs will quote them.
That text is now permanent, indexed, grep-able, and discoverable by
anyone with repo access — including, eventually, a Riverside operating
partner doing diligence on a sibling portco, an MSP being onboarded, or
an outside counsel during an audit.

Calling your PE owner's compliance program "theater" in writing in a repo
*they ultimately own* is a self-inflicted political wound. The strategic
*insight* (current dashboards are surface-level; receipts > slides) is
correct. The *phrasing* is reckless. Sanitize before this leaves your
laptop.

### F3. The name "Control Tower" is partially poisoned and the plan treats this as validation.

§4: *"Industry-validated mental model (AWS Control Tower exists for similar
reason)."*

That's the wrong framing. **AWS Control Tower is an Amazon product** — a
specific, well-known AWS service for multi-account governance. Every
Azure governance practitioner, every cloud architect, every PE-side IT
consultant who hears "Control Tower" will assume you mean the AWS service
first. You are building an *Azure-primary, multi-cloud-bridging* product
whose name will be confused with the AWS-native equivalent that does
~30% of what you're proposing.

This isn't a trademark issue ("control tower" is generic enough that AWS
doesn't own the bare phrase). It's a **positioning** issue:

- Internal: fine. People at HTT will learn the name.
- Cross-portfolio: every external person hears "you built an AWS Control
  Tower clone for Azure?"
- Diligence package: "Control Tower" in a Riverside-portfolio doc next to
  AWS workloads (DART) reads as confused branding.

The plan's own logic argues against itself: §5 says "no multi-cloud
abstraction layer," yet the brand name *is* a multi-cloud abstraction (an
AWS-native term applied to an Azure-primary platform that bridges both).
Either commit to an Azure-native name or commit to a name nobody else
owns. Recommend killing this and picking something orthogonal —
`Hangar`, `Concourse` (taken by CI), `Beacon`, `Switchyard`, `Dispatch`,
anything that doesn't hand AWS half your Google searches.

---

## Hidden assumptions that are wrong or dangerous

1. **"The cross-tenant identity graph is a feature."** §1 brags about TLL
   users in HTT Fabric workspaces and §5 promises a `b2b_governance`
   module to formalize it. This is presented as capability. An external
   auditor would call it **lateral movement risk between brand
   boundaries**. The right question isn't "how do we make this graph
   queryable?" It's "should this graph exist?" If a TLL franchisee gets
   compromised, do they have a transitive read path into HTT Fabric data?
   If yes, that's a finding, not a feature. The plan formalizes the
   smell instead of interrogating it.

2. **"B2B governance tooling at this layer doesn't exist commercially."**
   (§11). False. **Microsoft Entra Permissions Management** (formerly
   CloudKnox) is exactly this — CIEM across Azure/AWS/GCP, including B2B
   guest analysis. Saviynt, BeyondTrust, and Sonrai also play here.
   You're proposing to build a CIEM that already exists in your *primary
   cloud vendor's catalog*. The build-vs-buy in §6 D6 (AI layer) is asked
   but not asked here, where it matters more.

3. **"Stay under $100/mo."** Pax8 ingestion + Azure OpenAI RAG endpoint +
   OTel collector + cross-tenant federated XMLA queries + Athena scans
   (per-query billing!) + Sustainability Manager + DCE
   PowerShell-as-a-service = nowhere near $100/mo. Realistic floor at
   full Phase-5 scope: **$250-450/mo**, dominated by Azure OpenAI tokens
   and Athena scan cost (which is unbounded per user-query if RAG layer
   hits it). The §1 brag "the kind of hardening big-co security teams
   brag about" is in tension with the §3 value "stay under $100/mo." You
   can't have both.

4. **"Tyler stays the single human in the loop indefinitely."** §11
   acknowledges bus-factor as a "why it might not work" but the plan has
   no mitigation. There is no Phase-0.5 for runbooks, no
   secrets-of-record handoff doc, no agent-onboarding doc that lets a
   *different* human pick this up. If Tyler is hit by a bus, promoted
   into a non-IC role, recruited away, or just on PTO during a
   Riverside-deadline crunch, **the platform has no operator**.

5. **"Microsoft + Azure remains the strategic primary cloud."** Riverside
   is a PE firm. PE firms standardize aggressively when they hit scale
   (it's a known cost lever for OpEx synergies across portcos). If
   Riverside's portfolio includes AWS-heavy companies — and they
   certainly do — there's a non-trivial probability of a corporate "all
   portcos on AWS" mandate within the 5-year window. The plan's deepest
   Azure SQL + Entra + UAMI + Cost Mgmt commitments would then be
   *liabilities*, not assets. The §6 "no multi-cloud abstraction layer"
   stance bets explicitly against this.

6. **"DART POS/MBO data has no privacy implications."** Not stated, but
   assumed — bi_bridge §5 federates DART data into Control Tower. DART
   ingests Mindbody/Zenoti/Autopay/CallRail. That includes **customer
   PII** (booking records, contact data, possibly payment metadata).
   Routing that through Control Tower gives Control Tower DPIA scope,
   retention obligations, breach-notification scope, and CCPA exposure
   (any CA salons). Plan says zero about this. PE-owned data products
   that quietly absorb customer PII without a DPA review is not a small
   problem.

7. **"Riverside's portfolio composition is stable."** Plan assumes 5
   brands, hub-and-spoke onboards N+1. What if HTT divests TLL
   mid-Phase-3? Half your B2B governance work is for a brand that's
   leaving. What if Riverside acquires 3 brands in a quarter and they're
   all on Square/Toast/non-Mindbody POS? DART's ingestion model assumes
   Mindbody/Zenoti — that won't generalize. Plan has no scenario
   branches.

8. **"Federate-don't-absorb has no compounding cost."** §9 D3 frames this
   as obvious. But you now permanently maintain 5 deploy chains, 5
   secret rotations, 5 dependency-upgrade cadences, 5 incident-response
   runbooks, 5 CI templates. That's an O(N) operational tax. It's the
   right call short-term *only if* you simultaneously extract a shared
   platform substrate (libraries, GH Actions reusable workflows,
   secrets-of-record) which the plan does not budget for.

---

## Sequencing / dependency errors

### S1. Phase 1 (Option C file splits) before Phase 2 (DDD domain extraction) is **backwards**.

§7 Phase 1 splits files like `riverside_sync.py` (1075 LOC) → "per-table
modules under `services/riverside_sync/`." Then Phase 2 moves domain code
from `app/services/` *into* `app/domains/cost/`,
`app/domains/identity/`, etc. So the same files get touched twice —
first split along guessed lines in Phase 1, then re-split and relocated
along domain lines in Phase 2.

**Correct ordering:** identify domain boundaries first (Phase 2 work),
then do the file-size refactor *within each domain* using the domain
boundary to inform the split. You only touch each LOC once, your tests
double as the boundary-validation harness, and PR review surfaces are
smaller.

The current ordering also creates a risk where Phase 1's "Strategy
pattern" splits get rejected in Phase 2 because a domain extraction
reveals a different cleavage. That's wasted refactor.

### S2. Phase 3 (rebrand) before Phase 4 (cross-repo bridges) — wrong cost/risk ratio.

The rebrand is the single highest-political-risk, lowest-engineering-value
step. It's also gated on D1 (your own open question). Doing it Week 7-8
*before* the cross-repo bridges (Phase 4) means:
- If a bridge fails / is descoped, you've already paid the rebrand tax
  for capability you no longer have.
- The narrative ("Control Tower unifies the portfolio") is hollow until
  at least one bridge is live.

**Correct ordering:** ship the first bridge (recommend `cost :: Pax8` —
pure read-only, no auth complexity) *first* to validate the unification
thesis, then rebrand on the back of a working unification, not ahead of
one.

### S3. Phase 5 (AI layer) is over-positioned in the timeline.

`/ask` over `cost_facts`, `identity_graph`, `compliance_state`,
`audit_log` — but `cost_facts` is a Phase-2-or-later artifact (it's
mentioned as new in §5). `identity_graph` is also new. So Phase 5
depends on Phases 2 AND 4 being substantially complete. The plan
presents these as sequential "weeks 13-16" but the real critical path
puts AI layer at week 18+ minimum. Calling it Phase 5 understates how
late it actually arrives.

### S4. What can run in parallel that's currently serial?

- **Phase 0 honesty pass + Phase 1 file splits** can be parallel. They
  don't share files.
- **Phase 4 bridges are presented as one phase but each is independent**
  — `cost :: Pax8`, `lifecycle :: DCE`, `bi_bridge :: DART`,
  `bi_bridge :: httbi`, `identity :: B2B governance` can run as five
  parallel tracks. The plan implicitly serializes them by phase
  numbering.
- **Documentation refresh (Phase 3)** can run continuously alongside
  Phases 1-2 instead of being deferred to one block.

### S5. What's parallel that should be serial?

- **`bi_bridge :: DART` and `bi_bridge :: httbi`** are listed as peers in
  Phase 4. They're not. They have different auth models (Cognito vs
  Entra), different query engines (Athena JDBC vs Power BI XMLA),
  different cost shapes (per-scan vs per-capacity). Doing both at once
  means debugging two auth bridges, two query optimizers, and two cost
  models simultaneously. **Do httbi first** (same tenant family, same
  identity, simpler), validate the federated-query pattern works at all,
  then do DART (cross-cloud, cross-identity) with the lessons learned.

---

## Things the plan misses entirely

1. **Data classification & PII flow analysis.** No DPIA, no
   data-classification rubric, no statement of which domains touch
   customer PII vs internal-only data. Phase 4 bi_bridges *will* move
   customer-adjacent data; somebody needs a tag system and a retention
   policy. Add a `domains/<x>/data_classification.md` artifact per
   domain.

2. **SBOM / supply-chain security.** A platform projecting to be the
   audit-evidence source-of-truth for a PE portfolio needs
   SLSA-Level-3-ish provenance on its own builds, signed container
   images (cosign), and dependency provenance. Not a single mention.
   This is 2026 table stakes — IRS, Treasury, SEC and most enterprise
   procurement now ask.

3. **Bus-factor / continuity.** No "what happens when Tyler stops" doc.
   No secrets-of-record. No designated successor. No agent-onboarding
   runbook for a different human. Plan is brittle to its single
   dependency.

4. **Disaster recovery / RTO-RPO statement.** App Service B1 + Azure SQL
   Basic is single-region, single-instance. The plan calls Control Tower
   a "Portfolio Operating System" and "the diligence package writes
   itself" — that implies it's load-bearing for executive decisions.
   Load-bearing systems have stated RTOs. This one doesn't.

5. **Change management for human users.** DART has contractor users.
   httbi has TLL franchisee users. The plan treats brands as
   configuration. Real humans will encounter URL changes, auth flow
   changes, dashboard reorgs. No comms plan, no change-window cadence,
   no helpdesk runbook.

6. **Rollback for the rebrand.** Plan says "301 redirect for ~90 days"
   then... what? What happens to bookmarks, webhook integrations, CSP
   allowlists pointing at the old hostname? What if at month 3 you
   decide the AWS Control Tower confusion was actually fatal? There is
   no exit.

7. **Success metrics that aren't vanity.** "Tyler walks in and wins" is
   not measurable. Need quantitative targets: TTBO
   (time-to-brand-onboard) baseline + target, MTTD on cost anomalies, %
   of Riverside read-out auto-generated, $-saved-attributed-to-Control-
   Tower per quarter. Without these, Phase 6 cannot be evaluated.

8. **GitOps / declarative state for the playbooks.** Phase 4 says "DCE
   template → parameterized PowerShell-via-Control-Tower workflow."
   That's imperative. The 2026 industry pattern is declarative: brand
   config as YAML in a repo, reconciled by a controller, audit log
   derived from git history. The plan's framework checklist (§6) lists
   "Policy-as-Code" but skips "Configuration-as-Code." The DCE playbook
   is the place this should land.

9. **Agentic ops / auto-remediation.** Plan has agentic *engineering*
   (Tyler + agents writing code) but zero agentic *operations* (agents
   responding to alerts, opening tickets, proposing fixes). For a
   1-human + agents shop, runtime agents are the actual leverage.
   `/ask` is read-only; the platform needs `/act` with appropriate
   guardrails — this is genuinely 2026.

10. **Honesty pass on this very document.** Plan calls itself out for
    `INFRASTRUCTURE_END_TO_END.md` lying. But: "4,000+ tests" (verified
    when?), "WCAG 2.2 AA" (last audited?), "PKCE OAuth + refresh token
    blacklisting" (penetration tested?), "138 tables, 222M rows"
    (counted today or quoted from a stale doc?). The honesty audit
    should include this plan's own claims before they get cited as
    evidence in Phase 6.

11. **Which sections of `WIGGUM_ROADMAP.md` get reconciled with this
    plan.** There's already a 75 KB roadmap. There's already a `/wiggum
    ralph` protocol in this repo's agent instructions. This new plan
    does not say how it interacts with WIGGUM_ROADMAP. Are the two
    merged? Does WIGGUM_ROADMAP get archived? Does this plan become a
    WIGGUM_ROADMAP supplement? Pick one before planning-agent decomposes
    anything, or you'll have two competing roadmaps.

12. **Existing `control-tower-{4hn,rh1,tei,zp6}/` artifacts in the
    predecessor repo.** A glance at
    `/Users/tygranlund/dev/01-htt-brands/control-tower/` shows 4 sibling
    directories with random suffixes — that looks like prior failed
    attempts at exactly this consolidation. The plan cites the
    predecessor repo's IP as battle-tested but doesn't acknowledge or
    learn from whatever produced those four parallel attempts. Why did
    they fail? Same question, same risk this round.

---

## Things the plan gets right (specific, not flattering)

1. **The "Riverside is a customer, not the brand" instinct is correct.**
   Embedding a single PE owner's name in a portfolio platform's identity
   is a real coupling. Decoupling is correct — the *implementation*
   (calling existing dashboards "compliance theater") is what's wrong.

2. **Federate-don't-absorb on DART (D3 Option A) is right** even with the
   tax I called out. DART has product-market fit with its actual users
   (contractors); rewriting it to live inside Control Tower would
   destroy real value for speculative ergonomic gains. The plan
   correctly resists this.

3. **DDD domain boundaries are the right structural target.** Six domains
   (cost, identity, compliance, resources, lifecycle, bi_bridge) is
   plausible and matches the data model. The plan just sequences the
   move wrong (see S1).

4. **"Boring tech for reliability, sharp tech for value path" is
   correctly stated.** Resisting Kubernetes/microservices/GraphQL at
   this scale is the right call. The platform is one App Service B1
   instance and that's *fine*.

5. **`/portfolio/<brand>` parametric routing (D4 Option B)** is the
   correct call. Generalizing from a Riverside-specific route is real
   architecture work that pays for itself the moment a second brand
   needs the same view.

6. **Phase 0 hygiene-first is correct.** Most plans skip this. Stopping
   the platform from lying ("0 open issues") before adding new features
   is unsexy and exactly right.

7. **Naming open decisions D1-D7 explicitly is good practice.** Most
   strategy docs hide the forks. This one surfaces them. The
   recommendations attached are also mostly sound (D1: A, D2: A, D3: A,
   D6: C are all defensible).

---

## Recommended changes BEFORE planning-agent decomposition

These are blocking. Do not let planning-agent touch this until they're
addressed.

1. **Resolve the IP question first.** Add a Phase -1: Tyler talks to
   HTT/Riverside legal about IP ownership, work-for-hire scope, and what
   (if anything) of Control Tower is portable in any divestiture or
   departure scenario. **This is non-optional.** The answer changes
   whether to build any of this further.

2. **Sanitize all PE-adversarial language.** Replace "compliance theater"
   with "current Riverside read-outs are point-in-time, not continuous."
   Replace "Tyler walks in and wins" with "deliverable: a 30-minute demo
   with traceable evidence." This is not about politeness; it's about
   not poisoning 100+ downstream bd issues with searchable language that
   reads as employee-vs-employer in any future review.

3. **Re-examine the "Control Tower" name.** Either (a) explicitly accept
   the AWS Control Tower confusion and document why, or (b) pick a
   non-colliding name. Recommend (b). Don't let planning-agent codify a
   name into hostnames, repo names, and DNS that you may need to walk
   back.

4. **Swap Phase 1 and Phase 2 ordering.** Domain extraction first,
   file-size refactor *inside* domain packages second. Update §7
   accordingly. Otherwise you double-touch every refactor.

5. **Add a CIEM build-vs-buy decision (new D8).** Microsoft Entra
   Permissions Management exists. Either justify why building beats
   buying, or descope `b2b_governance` to "integrate Entra Permissions
   Management views into Control Tower UI."

6. **Realistic cost ceiling.** Replace the "$100/mo" claim with phased
   numbers: $53/mo (today) → $80/mo (Phase 0-2) → $150/mo (Phase 3-4
   bridges) → $300-400/mo (Phase 5 AI + Phase 6 reporting). Or, if
   $100/mo is a hard ceiling, descope Phase 5 (`/ask`) to a much
   lighter implementation (no Azure OpenAI, just pre-canned KQL/SQL
   templates).

7. **Reconcile with `WIGGUM_ROADMAP.md`.** Pick one source of truth.
   State explicitly whether the new plan supplements, replaces, or
   coexists with WIGGUM_ROADMAP. The `/wiggum ralph` protocol in agent
   instructions is going to be confused by two roadmaps.

8. **Add Phase 0.5: continuity & bus-factor.** Secrets-of-record doc.
   Successor-onboarding doc. Runbook for "Tyler is unavailable for 2
   weeks." Without this, Phase 6's "load-bearing for portfolio
   decisions" claim is fiction.

9. **Re-examine the cross-tenant identity graph thesis.** Add an explicit
   security-auditor review of whether B2B grants like "TLL users in HTT
   Fabric" should be *eliminated* rather than formalized. If kept,
   document the threat model. If eliminated, the `b2b_governance`
   module changes from "expose & manage" to "discover & deprovision."

---

## Recommended changes for AFTER planning-agent (during execution)

1. **Run the first bridge (`cost :: Pax8`) before the rebrand.** Use it
   as a unification-thesis validator. If it doesn't ship cleanly, the
   rebrand is premature.

2. **Per-domain data-classification artifact.** Each `domains/<x>/`
   directory gets a `DATA_CLASSIFICATION.md` with PII scope, retention
   policy, and breach-notification scope. Zero exceptions for
   `bi_bridge`.

3. **SBOM + cosign + SLSA provenance** added to the Dockerfile + GitHub
   Actions pipeline as part of the Phase 1 hygiene. This is
   non-negotiable for any system claiming to be portfolio
   audit-evidence.

4. **Quantitative success metrics published per phase.** Each phase
   deliverable gets a numeric target (TTBO baseline + target, %
   auto-generated reports, MTTD on anomalies, $ saved attributed). No
   phase is "done" until its metric is measured.

5. **DR runbook + RTO statement** before Phase 6. Cannot showcase a
   "Portfolio Operating System" without one.

6. **Brand-user comms plan** before any URL change or auth-flow change
   touches contractor or franchisee users. Recommend a dedicated
   `lifecycle :: change_management` sub-domain.

7. **Quarterly Wardley map refresh** is overhead, not insight. Drop to
   **annual** unless the cross-cloud landscape genuinely shifts. Pick
   3-4 frameworks from §6 and execute well; the 11-framework checklist
   signals breadth, not depth.

8. **Sunset criteria for each bridge.** Every Phase 4 bridge should have
   a written "we'd kill this if X" condition. `bi_bridge :: DART`
   especially — if Athena costs exceed $X/mo or query latency exceeds Y
   seconds, the bridge gets cached or replaced with batch ETL.

---

**Bottom line for Tyler:** The synthesis (5 repos → 1 narrative) is
correct and worth pursuing. The structural refactor (DDD domains) is
correct and overdue. The rebrand and the Riverside showcase, *as
currently framed*, are the two parts that can hurt you — one (name) is a
positioning error, the other (showcase) is a political error. Fix the IP
question first, fix the language second, swap Phases 1↔2 third, then let
planning-agent decompose.

The plan is fundamentally sound at the engineering layer. It is
fundamentally exposed at the political and IP layer. Don't let agent
execution time get committed against the political exposure before it's
resolved.

---

*Filed by code-puppy-ab8d6a. Adversarial review served, plan stronger
for it.*
