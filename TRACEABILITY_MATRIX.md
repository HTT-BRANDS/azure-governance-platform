# Traceability Matrix — Code Puppy Agile SDLC Implementation

**Last Updated:** March 7, 2026
**Managed By:** Planning Agent 📋 (planning-agent-cbc7e7) + Pack Leader 🐺
**Methodology:** Tyler Granlund's Agile SDLC Framework
**Research Date Validation:** All tools/versions confirmed current as of March 6, 2026

---

## How to Read This Matrix

Each row traces a requirement from **origin → implementation → testing → sign-off**. Every cell has an accountable agent. If something breaks, you can trace backwards from the defect to the exact requirement, test case, and responsible agent.

| Column | What It Contains | Who Owns It |
|--------|-----------------|-------------|
| Req ID | Unique requirement identifier | Planning Agent 📋 |
| Epic | Parent epic grouping | Planning Agent 📋 |
| User Story | What the user needs | Planning Agent 📋 |
| Acceptance Criteria | How we know it's done | Planning Agent 📋 + Pack Leader 🐺 |
| Implementation Agent | Who builds it | Assigned per task |
| Review Agent | Who reviews the code | Shepherd 🐕 + domain reviewers |
| Test Type | Unit / Integration / E2E / Manual | QA Expert 🐾 |
| Test Agent | Who runs the tests | Watchdog 🐕‍🦺 / QA Kitten 🐱 / Terminal QA 🖥️ |
| Security Review | STRIDE analysis status | Security Auditor 🛡️ |
| Sign-Off Agent | Who approves completion | Pack Leader 🐺 or Planning Agent 📋 |
| Status | Not Started / In Progress / Passed / Failed | Auto-updated via bd |
| bd Issue | Linked issue ID | Bloodhound 🐕‍🦺 |

---

## Epic 1: Agent Catalog Completion

| Req ID | User Story | Acceptance Criteria | Impl Agent | Review Agent | Test Type | Test Agent | Security | Sign-Off | Status | bd Issue |
|--------|-----------|-------------------|------------|-------------|-----------|-----------|----------|----------|--------|----------|
| REQ-101 | Create Solutions Architect JSON agent | Agent loads in `/agents` catalog; can invoke web-puppy; produces MADR 4.0 ADRs | Agent Creator 🏗️ | Prompt Reviewer 📝 | Smoke + Integration | Terminal QA 🖥️ | N/A (no new attack surface) | Planning Agent 📋 | ✅ Passed | — |
| REQ-102 | Create Experience Architect JSON agent | Agent loads in catalog; can invoke web-puppy; flags manual a11y gaps; includes GPC as P0 | Agent Creator 🏗️ | Prompt Reviewer 📝 | Smoke + Integration | Terminal QA 🖥️ | N/A (no new attack surface) | Planning Agent 📋 | ✅ Passed | — |
| REQ-103 | Audit all agent tool permissions | Every agent's tool list reviewed; no excess permissions; audit documented | Security Auditor 🛡️ | Code Reviewer 🛡️ | Manual Audit | Watchdog 🐕‍🦺 | STRIDE analysis required | Pack Leader 🐺 | ✅ Passed | — |

## Epic 2: Traceability Matrix & Roadmap

| Req ID | User Story | Acceptance Criteria | Impl Agent | Review Agent | Test Type | Test Agent | Security | Sign-Off | Status | bd Issue |
|--------|-----------|-------------------|------------|-------------|-----------|-----------|----------|----------|--------|----------|
| REQ-201 | Create TRACEABILITY_MATRIX.md | File exists; every task type represented; agent accountability chains documented | Planning Agent 📋 | Solutions Architect 🏛️ | Manual Review | QA Expert 🐾 | N/A | Planning Agent 📋 | ✅ Passed | — |
| REQ-202 | Create WIGGUM_ROADMAP.md | Checkbox task tree; sync_roadmap.py --verify returns valid state | Planning Agent 📋 | Python Reviewer 🐍 | Automated | Terminal QA 🖥️ | N/A | Pack Leader 🐺 | ✅ Passed | — |
| REQ-203 | Create scripts/sync_roadmap.py | Supports --verify --json and --update --task; exits non-zero on invalid state; Python 3.11+ | Python Programmer 🐍 | Python Reviewer 🐍 | Unit + Integration | Watchdog 🐕‍🦺 | N/A | Pack Leader 🐺 | ✅ Passed | — |
| REQ-204 | Wire callback hooks for audit trail | Agent actions logged to bd issues; audit trail queryable; no performance degradation | Husky 🐺 | Shepherd 🐕 + Code Reviewer 🛡️ | Integration | Watchdog 🐕‍🦺 | Review required | Pack Leader 🐺 | ✅ Passed | — |

## Epic 3: 13-Step Testing Methodology

| Req ID | Step | Phase | Owner Agent(s) | Review Agent | Validation | Status |
|--------|------|-------|---------------|-------------|------------|--------|
| REQ-301 | 1. Review US/AC | Test Prep | QA Expert 🐾 + Experience Architect 🎨 | Planning Agent 📋 | AC coverage report | ✅ Passed |
| REQ-302 | 2. Draft test cases | Test Prep | QA Expert 🐾 | Shepherd 🐕 | Test case specs exist | ✅ Passed |
| REQ-303 | 3. Set up test env | Test Prep | Terrier 🐕 + Husky 🐺 | Watchdog 🐕‍🦺 | Env boots clean | ✅ Passed |
| REQ-304 | 4. Automate test setup | Test Prep | Python Programmer 🐍 | Python Reviewer 🐍 | CI config valid | ✅ Passed |
| REQ-305 | 5. Manual testing | Execution | QA Kitten 🐱 (web) / Terminal QA 🖥️ (CLI) | QA Expert 🐾 | Manual test log | ✅ Passed |
| REQ-306 | 6. Automated testing | Execution | Watchdog 🐕‍🦺 | QA Expert 🐾 | All tests pass | ✅ Passed |
| REQ-307 | 7. Execute all planned | Execution | Pack Leader 🐺 | Planning Agent 📋 | Full test report | ✅ Passed |
| REQ-308 | 8. Log defects | Issue Mgmt | Bloodhound 🐕‍🦺 | Pack Leader 🐺 | bd issues created | ✅ Passed |
| REQ-309 | 9. Verify fixes | Issue Mgmt | Watchdog 🐕‍🦺 + Shepherd 🐕 | QA Expert 🐾 | Regression tests pass | ✅ Passed |
| REQ-310 | 10. Performance testing | Perf & Security | QA Expert 🐾 | Solutions Architect 🏛️ | Perf metrics met | ✅ Passed |
| REQ-311 | 11. Security testing | Perf & Security | Security Auditor 🛡️ + Solutions Architect 🏛️ | Pack Leader 🐺 | STRIDE + OWASP clear | ✅ Passed |
| REQ-312 | 12. Update documentation | Documentation | Planning Agent 📋 | Code Reviewer 🛡️ | Docs current | ✅ Passed |
| REQ-313 | 13. Stakeholder feedback | Closure | Pack Leader 🐺 + Planning Agent 📋 | N/A (final step) | Sign-off recorded | ✅ Passed |

## Epic 4: Requirements Flow (9 Roles → Agents)

| Artifact Role | Mapped Agent | Responsibility | Validation | Status |
|--------------|-------------|---------------|------------|--------|
| Backlog | Bloodhound 🐕‍🦺 | bd create for incoming requests | Issues created with proper labels | ✅ Passed |
| Business Analyst | Planning Agent 📋 | Decompose requests → epics → US → tasks | Breakdown documented | ✅ Passed |
| Subject Matter Experts | Solutions Architect 🏛️ + Experience Architect 🎨 | Domain expertise (backend + frontend) | ADRs and UX specs produced | ✅ Passed |
| External Contributors | Web Puppy 🕵️‍♂️ | Evidence-based research | Research saved to ./research/ | ✅ Passed |
| Product Owner | Pack Leader 🐺 | Review, refine, prioritize | bd ready shows prioritized work | ✅ Passed |
| Sprint/Dev Goals | Pack Leader 🐺 | Base branch, parallel coordination | Worktrees organized | ✅ Passed |
| Team Collaboration | All agents via invoke_agent | Session-based delegation | Invoke chains traced | ✅ Passed |
| Implementation Reqs | Solutions Architect 🏛️ + Experience Architect 🎨 | BRDs → user stories → technical scope | Specs produced | ✅ Passed |
| Product Manager | Planning Agent 📋 | Strategic oversight, roadmap alignment | Roadmap current | ✅ Passed |

## Epic 5: Dual-Scale Project Management

| Req ID | User Story | Owner | Acceptance Criteria | Status |
|--------|-----------|-------|-------------------|--------|
| REQ-501 | Sprint-scale track management | Pack Leader 🐺 | bd issues with sprint labels; worktree-per-task; shepherd+watchdog gates | ✅ Passed |
| REQ-502 | Large-scale track management | Planning Agent 📋 | Dedicated bd issue tree; isolated from sprint; WIGGUM_ROADMAP tracks progress | ✅ Passed |
| REQ-503 | Cross-track synchronization | Planning Agent 📋 + Pack Leader 🐺 | Shared bd labels for cross-deps; sync protocol documented | ✅ Passed |

## Epic 6: Security & Compliance

| Req ID | User Story | Owner | Reviewer | Acceptance Criteria | Status |
|--------|-----------|-------|---------|-------------------|--------|
| REQ-601 | STRIDE analysis for all agents | Security Auditor 🛡️ | Solutions Architect 🏛️ | 29 agents have STRIDE rows documented | ✅ Passed |
| REQ-602 | YOLO_MODE audit | Security Auditor 🛡️ | Code Reviewer 🛡️ | Default=false confirmed; risk documented | ✅ Passed |
| REQ-603 | MCP trust boundary audit | Security Auditor 🛡️ | Solutions Architect 🏛️ | All MCP servers documented with trust level | ✅ Passed |
| REQ-604 | Self-modification protections | Security Auditor 🛡️ | Code Reviewer 🛡️ | Only agent-creator can write to agents dir | ✅ Passed |
| REQ-605 | GPC compliance validation | Experience Architect 🎨 | Security Auditor 🛡️ | Sec-GPC:1 honored; documented as P0 | ✅ Passed |

## Epic 7: Architecture Governance

| Req ID | User Story | Owner | Reviewer | Acceptance Criteria | Status |
|--------|-----------|-------|---------|-------------------|--------|
| REQ-701 | MADR 4.0 ADR workflow | Solutions Architect 🏛️ | Security Auditor 🛡️ | docs/decisions/ created; ADR template with STRIDE; 3 retroactive ADRs | ✅ Passed |
| REQ-702 | Spectral API governance | Solutions Architect 🏛️ | Code Reviewer 🛡️ | .spectral.yaml created; integrated in pre-commit | ✅ Passed |
| REQ-703 | Architecture fitness functions | Solutions Architect 🏛️ + Python Programmer 🐍 | Python Reviewer 🐍 | tests/architecture/ with 3+ fitness functions; runs in CI | ✅ Passed |
| REQ-704 | Research-first protocol | Solutions Architect 🏛️ → Web Puppy 🕵️‍♂️ | Planning Agent 📋 | Every decision preceded by web-puppy research | ✅ Passed |

## Epic 8: UX/Accessibility Governance

| Req ID | User Story | Owner | Reviewer | Acceptance Criteria | Status |
|--------|-----------|-------|---------|-------------------|--------|
| REQ-801 | WCAG 2.2 AA baseline | Experience Architect 🎨 | QA Expert 🐾 | System prompt mandates WCAG 2.2 AA; manual checklist covers 7 criteria | ✅ Passed |
| REQ-802 | axe-core + Pa11y 9.1.1 in CI | Experience Architect 🎨 + Python Programmer 🐍 | QA Expert 🐾 | CI includes both tools; coverage report on every PR | ✅ Passed |
| REQ-803 | Privacy-by-design patterns | Experience Architect 🎨 → Web Puppy 🕵️‍♂️ | Security Auditor 🛡️ | Documented: layered consent, JIT consent, progressive profiling, consent receipts, GPC | ✅ Passed |
| REQ-804 | Accessibility API metadata contract | Experience Architect 🎨 | Solutions Architect 🏛️ + Code Reviewer 🛡️ | JSON schema for ARIA-compatible errors; integration guide | ✅ Passed |

## Epic 9: Design System Migration (DNS → Governance Platform)

| Req ID | User Story | Acceptance Criteria | Impl Agent | Review Agent | Test Type | Test Agent | Security | Sign-Off | Status | bd Issue |
|--------|-----------|-------------------|------------|-------------|-----------|-----------|----------|----------|--------|----------|
| REQ-901 | Port design token architecture from DNS project | Pydantic models for BrandConfig, BrandColors, BrandTypography, BrandDesignSystem; YAML loader; CSS generator | Python Programmer 🐍 | Python Reviewer 🐍 + Solutions Architect 🏛️ | Unit + Integration | Watchdog 🐕‍🦺 | N/A | Planning Agent 📋 | ✅ Passed | — |
| REQ-902 | WCAG color utilities in Python | hex↔RGB↔HSL conversion; WCAG luminance/contrast; auto text color; lighten/darken; 25+ test cases | Python Programmer 🐍 | Python Reviewer 🐍 + Security Auditor 🛡️ | Unit | Watchdog 🐕‍🦺 | WCAG 2.2 AA compliance | Pack Leader 🐺 | ✅ Passed | — |
| REQ-903 | Server-side CSS generation pipeline | Generate full CSS custom property sets from brand config; scoped brand CSS; all-brands CSS output | Python Programmer 🐍 | Python Reviewer 🐍 | Unit | Watchdog 🐕‍🦺 | XSS sanitization | Planning Agent 📋 | ✅ Passed | — |
| REQ-904 | Brand YAML config as single source of truth | config/brands.yaml with 5 brands; colors, typography, logos, design tokens; Pydantic validation on load; BrandConfig model extended | Experience Architect 🎨 + Python Programmer 🐍 | Solutions Architect 🏛️ | Unit + Integration | QA Expert 🐾 | N/A | Pack Leader 🐺 | ✅ Passed | — |
| REQ-905 | Brand logo/asset organization | All 5 brands have logo-primary, logo-white, icon files in app/static/assets/brands/; HTT horizontal logos copied | Code-Puppy 🐶 | Experience Architect 🎨 | Manual | Terminal QA 🖥️ | N/A | Planning Agent 📋 | ✅ Passed | — |
| REQ-906 | Theme middleware for server-side injection | FastAPI middleware reads tenant context; generates CSS variables via css_generator; injects brand/fonts/logo into Jinja2 context | Python Programmer 🐍 | Solutions Architect 🏛️ + Python Reviewer 🐍 | Unit + Integration | Watchdog 🐕‍🦺 | Tenant isolation review | Pack Leader 🐺 | ✅ Passed | — |
| REQ-907 | Jinja2 UI component macro library | Macros for button, card, badge, alert, stat_card, table, tabs, dialog, progress, skeleton; ARIA attributes; design token CSS vars only | Experience Architect 🎨 | QA Expert 🐾 + Security Auditor 🛡️ | Manual + Unit | Terminal QA 🖥️ | ARIA + keyboard a11y | Planning Agent 📋 | ✅ Passed | — |

---

## Agent Accountability Summary

| Agent | Owns (Primary) | Reviews | Tests/Validates | Signs Off |
|-------|---------------|---------|----------------|----------|
| Planning Agent 📋 | REQ-201, 202, 312, 313, 502, 503 | REQ-301, 307, 704 | — | REQ-101, 102, 201, 601, 603, 605, 701, 801 |
| Pack Leader 🐺 | REQ-307, 501, 503 | — | — | REQ-103, 202, 203, 204, 502, 602, 604, 804 |
| Solutions Architect 🏛️ | REQ-701, 702, 703, 704 | REQ-201, 310, 601, 603, 804 | — | — |
| Experience Architect 🎨 | REQ-605, 801, 802, 803, 804 | — | — | — |
| Security Auditor 🛡️ | REQ-103, 311, 601, 602, 603, 604 | REQ-605, 701, 803 | — | — |
| Web Puppy 🕵️‍♂️ | Research backbone for 704, 803 | — | — | — |
| QA Expert 🐾 | REQ-301, 302, 305, 310 | REQ-306, 309, 801, 802 | REQ-201 | — |
| QA Kitten 🐱 | REQ-305 (web) | — | — | — |
| Terminal QA 🖥️ | REQ-305 (CLI) | — | REQ-101, 102, 202 | — |
| Watchdog 🐕‍🦺 | REQ-306, 309 | REQ-303 | REQ-103, 203, 204 | REQ-703 |
| Shepherd 🐕 | — | REQ-204, 302 | REQ-309 | — |
| Bloodhound 🐕‍🦺 | REQ-308 | — | — | — |
| Terrier 🐕 | REQ-303 | — | — | — |
| Husky 🐺 | REQ-204, 303 | — | — | — |
| Python Programmer 🐍 | REQ-203, 304, 703, 802 | — | — | — |
| Code Reviewer 🛡️ | — | REQ-103, 204, 312, 602, 604, 702, 804 | — | — |
| Python Reviewer 🐍 | — | REQ-202, 203, 304, 703 | — | — |
| Prompt Reviewer 📝 | — | REQ-101, 102 | — | — |
| Agent Creator 🏗️ | REQ-101, 102 | — | — | — |

---

## Status Legend

| Symbol | Meaning |
|--------|--------|
| ⬜ | Not Started |
| 🔄 | In Progress |
| ✅ | Passed |
| ❌ | Failed |
| 🔴 | Blocked |

---

## Research Validation Status

| Tool/Framework | Expected Version | Confirmed Version | Confirmed Date | Status |
|---------------|-----------------|------------------|---------------|--------|
| axe-core | 4.11.1 | 4.11.1 | Jan 6, 2026 | ✅ Current |
| Spectral CLI | 6.15.0 | 6.15.0 | Apr 22, 2025 | ✅ Current |
| Pa11y | 9.1.1 | 9.1.1 | Feb 2026 | ✅ Current |
| MADR | 4.0.0 | 4.0.0 | Sep 17, 2024 | ✅ Current |
| WCAG | 2.2 | 2.2 (3.0 still draft) | Oct 5, 2023 | ✅ Current |
| IBM Carbon | v11 | Updated March 2026 | March 6, 2026 | ✅ Current |
| Salesforce SLDS | Winter '26 v2.3.0 | Winter '26 v2.3.0 | Feb 2026 | ✅ Current |

---

*This matrix is the single source of truth for requirement-to-agent accountability. Updated by Planning Agent 📋 and Pack Leader 🐺.*
