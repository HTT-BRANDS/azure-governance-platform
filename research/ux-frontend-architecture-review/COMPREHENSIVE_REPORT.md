# UX/Frontend Architecture Review & Competitive Analysis
## Azure Multi-Tenant Governance Platform v1.7.0

**Author:** Experience Architect (experience-architect-5c9811)
**Date:** March 27, 2026
**Scope:** Full frontend architecture review with competitive analysis across 8 research areas
**Research Method:** All findings verified via web-puppy agent (see research/ directory for raw data)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Area 1: Dashboard Design Patterns](#area-1-dashboard-design-patterns)
3. [Area 2: HTMX vs Modern Alternatives](#area-2-htmx-vs-modern-alternatives)
4. [Area 3: Design System & Component Libraries](#area-3-design-system--component-libraries)
5. [Area 4: Data Visualization](#area-4-data-visualization)
6. [Area 5: Accessibility at Scale](#area-5-accessibility-at-scale)
7. [Area 6: Performance & UX Patterns](#area-6-performance--ux-patterns)
8. [Area 7: Mobile & Responsive](#area-7-mobile--responsive)
9. [Area 8: Competitor UX Analysis](#area-8-competitor-ux-analysis)
10. [Effort vs Impact Matrix](#effort-vs-impact-matrix)
11. [Final Verdict](#final-verdict)
12. [WCAG 2.2 AA Manual Audit Checklist](#wcag-22-aa-manual-audit-checklist)

---

## Executive Summary

### The Bottom Line

**The current frontend architecture (HTMX + Jinja2 + Tailwind CSS v4) is fundamentally sound and appropriate for this use case.** For an internal IT governance tool serving 10-30 power users, this stack delivers the right balance of simplicity, performance, and maintainability. A migration to React/Vue/Svelte would cost 3-6 months and $75K-$150K with zero measurable benefit for this user base.

However, the implementation has significant gaps that should be addressed:

| Category | Current Grade | Target Grade | Effort to Close Gap |
|----------|:---:|:---:|---|
| **Architecture** | A- | A | Low (HTMX 2.0 upgrade) |
| **Design System** | C+ | B+ | Medium (DaisyUI + token restructuring) |
| **Accessibility** | C | A- | Medium (automated CI + manual checklist) |
| **Dashboard UX** | C+ | B+ | Medium (3-level hierarchy + tenant filter) |
| **Data Visualization** | B- | B+ | Low-Medium (a11y plugins + data tables) |
| **Performance** | B | A- | Low (SSE + skeleton screens) |
| **Mobile/Responsive** | C+ | B | Low (responsive tables + touch targets) |
| **Privacy/Consent** | A- | A | Low (already has GPC + consent banner) |

### Top 10 Recommendations (Priority Order)

| # | Recommendation | Effort | Impact | Area |
|---|----------------|--------|--------|------|
| 1 | Fix WCAG critical violations (invisible text, focus conflicts) | 2-4 hours | 🔴 Critical | A11y |
| 2 | Add tenant scope selector to dashboard header | 2-4 hours | High | UX |
| 3 | Upgrade HTMX 1.9.12 → 2.0.7 | 2-4 hours | Medium | Architecture |
| 4 | Add Alpine.js 3.15.9 for client-side interactivity | 1 day | High | Architecture |
| 5 | Install axe-playwright-python for automated a11y CI | 2 hours | High | A11y |
| 6 | Adopt DaisyUI 5.5.x as component library | 1 day | High | Design System |
| 7 | Redesign dashboard with 3-level info hierarchy | 1-2 days | High | UX |
| 8 | Add Chart.js a11y plugins + data table fallbacks | 2-3 days | High | Charts |
| 9 | Replace sync dashboard polling with SSE | 4-6 hours | Medium | Performance |
| 10 | Create WCAG 2.2 manual testing checklist + schedule | 1 hour | High | A11y |

**Total estimated effort: ~3-4 weeks of focused development**
**Expected outcome: Grade improvements across all 8 areas**

---

## Area 1: Dashboard Design Patterns

### Current Approach
- 4 summary cards (cost, compliance, resources, identity) in a flat grid
- 2 charts side-by-side (cost trend, compliance by tenant)
- 2 data tables (top services, top violations)
- No tenant filtering on main dashboard
- No data freshness indicators
- No drill-down panels — full page navigation only
- All sections load simultaneously

### Best Alternatives Found (via web-puppy research)

**Azure Portal (★★★★★ UX maturity):**
- 3-level hierarchy: KPI bar → 2×2 grid sections → detail blades
- Scope selector at top (subscription/resource group filter)
- Insights panel with AI-generated anomaly callouts
- "Smart Views" for cost analysis with presets
- Tab-based multi-view (up to 5 simultaneous analyses)

**Vantage.sh (★★★★☆ UX maturity):**
- Percentage change badges on every KPI (+12.78% / -15.89%)
- Workspace selector as primary navigation element
- Clean, minimal design with progressive disclosure
- Goal-based information architecture

**Datadog/Grafana (★★★★☆ UX maturity):**
- 12-column grid layout with collapsible sections
- Template variables as global filters
- Inline sparklines within metric widgets
- Density toggle (comfortable / compact / dense)

### Recommendations

| Change | Effort | Impact | Complexity |
|--------|--------|--------|------------|
| Add tenant scope selector (dropdown in header) | Low (2-4h) | 🔴 High | Trivial — HTMX select + query param |
| Add % change badges to all KPI cards | Low (1-2h) | High | Requires previous-period data in API |
| Implement 3-level hierarchy (KPI → grid → detail) | Medium (1-2d) | 🔴 High | Template restructuring |
| Add collapsible sections with `hx-trigger="revealed"` lazy loading | Low-Med (2-3d) | Medium | `<details>` + HTMX |
| Add side-panel detail view (Azure-style blade) | Medium (4-5d) | High | New partial templates |
| Add "Last synced" timestamp per section | Low (1-2h) | Medium | API endpoint + HTMX polling |
| Add sparklines in KPI cards | Medium (2-3d) | Low | Chart.js mini charts |
| Density toggle (comfortable/compact/dense) | Low (1-2d) | Low-Med | CSS custom properties |

### Key Insight
> **NNg research confirms: for 10-30 expert users, favor high density with progressive disclosure.** "Reduce clutter without reducing capability." Default to compact table mode. Show numbers + change + sparklines (3 data points per card, not 1).

---

## Area 2: HTMX vs Modern Alternatives

### Current Approach
- HTMX 1.9.12 (CDN-loaded) for partial page updates
- Jinja2 server-side templates (no SPA, no client-side routing)
- Vanilla JS bundled into `navigation.bundle.js` (toast, confirm, progress, nav highlight)
- No client-side framework
- HTMX polling for sync dashboard updates (`hx-trigger="every 5s"`)

### Framework Comparison (Weighted for THIS Project)

| Framework | Latest Version | Bundle (gzip) | Migration Effort | Weighted Score |
|-----------|---------------|---------------|------------------|:-:|
| **HTMX 2.0 + Alpine.js** | 2.0.7 + 3.15.9 | 33 kB | ~1 week | **42.0** ⭐ |
| HTMX 2.0 (alone) | 2.0.7 | 17.6 kB | 2-4 hours | 40.5 |
| Vue/Nuxt | 3.5.31 / 4.4.2 | ~33 kB | 2-4 months | 32.0 |
| Svelte/SvelteKit | 5.55.0 | ~3 kB runtime | 3-6 months | 32.5 |
| React/Next.js | 19.2.4 / 16.2.1 | ~42 kB | 3-6 months | 30.5 |
| Solid.js | 1.9.12 | ~7 kB | 3-6 months | 30.0 |
| Qwik | 1.19.2 | ~1 kB initial | 3-6 months | 26.5 |

### Recommendation: **HTMX 2.0 + Alpine.js**

**Why this wins decisively:**
- ~$5,700 estimated cost vs $75,000-$150,000 for SPA migration
- Zero architectural changes — same FastAPI + Jinja2 + Tailwind stack
- 33 kB combined — less than React-DOM alone
- Project already has Alpine.js `x-data` syntax in `riverside.html` (not loaded!)
- HTMX SSE extension replaces polling for real-time updates
- Alpine.js eliminates 4 custom JS files (darkMode.js, mobileMenu.js, confirmDialog.js, toast.js)

**HTMX 2.0 migration specifics:**
- `selfRequestsOnly: true` is now default (security improvement)
- Extensions separated from core (need separate `<script>` tags)
- `htmx-1-compat` extension available as safety net
- Shadow DOM support added (useful for web components)

**Alpine.js use cases in this project:**
- Dark mode toggle: `x-data="{ dark: false }"` (replaces darkMode.js)
- Mobile menu: `@click="open = !open"` (replaces mobileMenu.js)
- Tab switching: `x-data="{ tab: 'overview' }"` (currently not possible)
- Filter dropdowns: `x-show + x-model` (currently not possible)
- Riverside countdown: `x-data` + `x-init` (already has syntax, just needs loading)

### Migration Complexity: **Very Low**
- Add Alpine.js CDN to `base.html`: 30 minutes
- Add `alpine-morph` extension for HTMX↔Alpine state preservation: 30 minutes
- Upgrade HTMX to 2.0.7: 2-4 hours
- Replace custom JS files with Alpine.js: 4-8 hours

---

## Area 3: Design System & Component Libraries

### Current Approach
- Tailwind CSS v4.2 with custom `@theme` tokens
- 47+ CSS custom properties per brand × 5 brands = 235+ managed values
- Server-side CSS generation via `css_generator.py`
- Jinja2 macros for UI components (10 macros in `macros/ui.html`)
- **52 design system violations** documented in DESIGN_SYSTEM_AUDIT.md
- Hardcoded `text-gray-100` rendering invisible text (contrast ~1.04:1)
- Conflicting `:focus-visible` rules between CSS files

### Library Comparison (HTMX-Compatible Only)

| Library | Version | Works Without React? | Tailwind v4? | Custom Themes? | WCAG Coverage |
|---------|---------|:---:|:---:|:---:|---|
| **DaisyUI** | 5.5.19 | ✅ Pure CSS | ✅ Native | ✅ CSS vars + 35 themes | ⚠️ Visual only |
| Flowbite | 4.0.1 | ⚠️ Needs JS reinit | ✅ Migration guide | ❌ No token system | ⚠️ Partial |
| shadcn/ui | latest | ❌ React required | ✅ | ✅ Pattern extractable | ✅ Radix a11y |
| Pico CSS | 2.1.1 | ✅ Classless | N/A | ✅ CSS vars | ✅ Semantic HTML |
| Web Awesome | 3.4.0 | ✅ Web components | N/A | ✅ Themes | ✅ Built-in |

### Recommendation: **DaisyUI 5.5.x + Restructured Token Architecture**

**Why DaisyUI wins:**
1. **Pure CSS** — zero JavaScript, no HTMX reinitialization problems
2. **Tailwind v4 native** — `@plugin "daisyui"`, first-class support
3. **Semantic classes** — `btn btn-primary`, `card`, `badge badge-success` (replaces verbose Tailwind)
4. **Custom themes via CSS vars** — maps to existing `[data-brand]` injection
5. **40.6k stars, 37 open issues** — actively maintained, MIT license
6. **Additive adoption** — coexists with existing tokens

**Token restructuring (3-tier architecture):**

| Tier | Purpose | Count | Example |
|------|---------|-------|---------|
| 1: Brand Primitives | Raw brand colors (per-brand) | ~5 × 5 brands = 25 | `--brand-primary: oklch(0.30 0.12 350)` |
| 2: Semantic Aliases | Shared purpose-based tokens | ~15 shared | `--color-success: #10B981` |
| 3: Tailwind Bridge | `@theme` references to Tier 1+2 | ~20 | `--color-brand-primary: var(--brand-primary)` |

**Result: 235+ managed values → ~60 managed values (74% reduction)**

Use oklch relative color syntax for shade generation:
```css
--color-brand-primary-light: oklch(from var(--brand-primary) calc(l + 0.3) c h);
```
This reduces 50 shade tokens to 3 while maintaining visual consistency.

### Migration Complexity: **Low-Medium**
- Week 1: Install DaisyUI, create 5 brand themes (4 hours)
- Week 2: Migrate buttons, badges, alerts to DaisyUI classes (4 hours)
- Week 3: Restructure tokens to 3-tier architecture (4 hours)
- Week 4: WCAG contrast audit with DaisyUI themes (2 hours)

---

## Area 4: Data Visualization

### Current Approach
- Chart.js 4.4.7 with 2 chart types: line (cost trend), bar (compliance by tenant)
- Manual ARIA labels on canvas elements (`role="img"`, `aria-label`)
- Fallback text inside `<canvas>` tags
- Red/green color scheme for pass/fail (problematic for color-blind users)
- No keyboard navigation in charts
- No data table fallback alongside charts
- No sonification or screen reader data traversal

### Library Comparison

| Library | Version | Bundle (gzip) | Framework-free? | Gauge Chart | Accessibility |
|---------|---------|--------------|:---:|:---:|---|
| **Chart.js** | 4.5.1 | 68 kB | ✅ | ❌ No native | ❌ Zero built-in a11y |
| Apache ECharts | 6.0.0 | 380 kB | ✅ | ✅ 8+ types | ✅ Built-in ARIA, decal patterns |
| Highcharts | 12.5.0 | 280 kB | ✅ | ✅ Solid | ✅✅ Gold standard (sonification!) |
| D3.js | 7.x | 85 kB | ✅ | Manual | Manual (full control) |
| Observable Plot | 0.6.x | 45 kB | ✅ | ❌ | ⚠️ Limited |

### Recommendation: **Stay on Chart.js + Enhance Accessibility**

**Why not migrate:**
- Chart.js is already working and integrated with HTMX
- Migration introduces bugs and testing burden
- Plugins + data tables get 80% of Highcharts' a11y at $0 cost
- Highcharts licensing: $366-732/year/developer

**Enhancements to implement:**

1. **Install `chartjs-plugin-a11y-legend`** — keyboard-accessible legends (Tab, Arrow, Space/Enter)
2. **Install `chart2music`** — sonification + keyboard data navigation for screen readers
3. **Add `<details>/<summary>` data tables alongside every chart** — critical Chartability heuristic
4. **Replace red/green palette:**
   - Pass: `#0369A1` (blue) + ✅ icon + solid fill
   - Warning: `#D97706` (amber) + ⚠️ icon + diagonal stripe pattern
   - Fail: `#C2410C` (red-orange) + ❌ icon + crosshatch pattern
5. **Add pattern fills** for categorical differentiation (not just color)
6. **Ensure every `<canvas>` has `role="img"` + descriptive `aria-label`**

**Future consideration: Hybrid approach**
If gauge charts become needed (compliance maturity), add ECharts for gauges/radar only:
```
Chart.js (keep) → cost trends, identity stats
ECharts (add)   → compliance gauges, maturity radar
```
They coexist on the same page.

### Migration Complexity: **Low**
- Phase 1 (Week 1): ARIA attributes + data tables + color fix — 1-2 days
- Phase 2 (Week 2): Plugin integration (a11y-legend + chart2music) — 1-2 days
- Phase 3 (Week 3-4): Pattern fills + high contrast mode — 1-2 days

---

## Area 5: Accessibility at Scale

### Current Approach
- Skip link (`<a href="#main-content" class="skip-link">`)
- `aria-live="polite"` announcer region
- `scope` on table headers, `role="navigation"` on nav
- `aria-label` on charts and interactive elements
- `focus-visible` styles (but conflicting rules between CSS files!)
- `prefers-reduced-motion` respect
- `forced-colors` support for Windows High Contrast Mode
- **43% of WCAG issues require manual testing** — NO manual testing process exists

### Critical Findings

**The existing design system audit found 52 distinct violations:**
- `text-gray-100` renders **invisible text** (contrast ~1.04:1) — used in 4 places in `macros/ui.html`
- `text-gray-160` is a **dead class** that doesn't exist in CSS — text inherits randomly
- Conflicting `:focus-visible` rules: `accessibility.css` overrides `theme.src.css` with hardcoded Walmart blue (#0053e2) across ALL brands
- `focus:outline-none` without adequate ring replacement on login inputs
- `--text-muted` (#9CA3AF) fails contrast on white backgrounds (2.54:1 vs 4.5:1 required)
- ~30+ interactive elements have ZERO focus styles

### Tool Versions Confirmed (March 2026)

| Tool | Version | License | Coverage |
|------|---------|---------|----------|
| axe-core | 4.11.1 | MPL-2.0 | ~30-40% of WCAG (57% with manual judgment) |
| Pa11y | 9.1.1 | LGPL-3.0 | Uses axe runner for WCAG 2.2 |
| axe-playwright-python | 0.1.7 | — | Python integration for Playwright |
| Lighthouse | 12.x | Apache-2.0 | Performance + partial a11y |

### Recommendations

**P0 — This Week:**
1. Fix invisible text: `text-gray-100` → `text-muted-theme` in `macros/ui.html` (4 lines)
2. Fix dead class: `text-gray-160` → `text-primary-theme` (2 lines)
3. Fix focus conflicts: `accessibility.css` → use `var(--brand-primary)` instead of `#0053e2`
4. Fix login inputs: Add `focus:ring-brand-primary` color
5. Fix button focus: Replace `outline: none; box-shadow` with `outline: 2px solid transparent` + `box-shadow`
6. Install `axe-playwright-python` + create CI test covering all pages

**P1 — Next Sprint:**
7. Create WCAG 2.2 manual testing checklist (see Section 12)
8. Add HTMX focus management to `accessibility.js` (`htmx:afterSwap` → focus heading)
9. Add `aria-busy="true"` during HTMX requests
10. Throttle `aria-live` announcements (30s minimum between SSE updates)

**⚠️ Important Discovery:** The project's axe config explicitly limits to 9 rules. Removing the `rules` filter would enable ALL rules for `wcag2a/wcag2aa/wcag22aa` tags — significantly more coverage.

### Migration Complexity: **Low for automated, Medium for manual**
- CI pipeline: 2 hours to set up
- WCAG fixes: 2-4 hours for P0 items
- Manual testing: 2-3 hours per quarterly audit
- Focus management: 2 hours one-time

---

## Area 6: Performance & UX Patterns

### Current Approach
- HTMX polling (`hx-trigger="every 5s"`) for sync dashboard
- Loading spinner via `.htmx-indicator` CSS class
- Full page content loads immediately (no lazy loading)
- No skeleton screens
- No optimistic UI updates
- No virtual scrolling for large tables

### Recommendations

| Pattern | Current | Recommended | Effort | Impact |
|---------|---------|-------------|--------|--------|
| Sync updates | Polling every 5s | **SSE via sse-starlette** | 4-6h | 🔴 High (eliminates 360 req/min at 30 users) |
| Page loading | Spinner | **Skeleton screens** for full-page, spinners for inline | 3h | Medium |
| Large tables | Full render | **Server-side pagination** (not virtual scroll) | 2-3d | Medium |
| Section loading | Eager | **Lazy via `hx-trigger="revealed"`** | 2-3d | Medium |
| Safe operations | Full round-trip | **Optimistic UI** (dark mode, filters) | 2h | Low |
| Destructive ops | No change | Keep confirmation dialog | — | — |
| PWA | None | **Skip** — ROI too low for 10-30 users | — | — |

**SSE implementation:**
```python
# sse-starlette 3.3.3 (released 10 days ago) + htmx-ext-sse 2.2.2
from sse_starlette import EventSourceResponse
# + HTMX: hx-ext="sse" sse-connect="/api/v1/sync-events"
```

**Skeleton screen pattern:**
```html
<div hx-get="/dashboard/content" hx-trigger="load" aria-busy="true">
  <div class="animate-pulse space-y-6" aria-hidden="true">
    <div class="grid grid-cols-4 gap-4">
      {% for _ in range(4) %}
      <div class="h-28 bg-surface-secondary rounded-lg"></div>
      {% endfor %}
    </div>
  </div>
  <div class="sr-only" aria-live="polite">Loading dashboard data...</div>
</div>
```

---

## Area 7: Mobile & Responsive

### Current Approach
- Responsive grid (1→2→4 columns via Tailwind breakpoints)
- Mobile hamburger menu with toggle
- `overflow-x-auto` on some tables
- No dedicated mobile table patterns
- Touch targets may be below 24x24 CSS px minimum (WCAG 2.5.8)

### Recommendations

| Change | Effort | Impact |
|--------|--------|--------|
| **Roselli responsive table pattern** — `<div role="region" tabindex="0">` wrapper | 1 hour | High (WCAG 1.4.10 Reflow) |
| Audit all touch targets for 24×24px minimum (WCAG 2.5.8) | 2 hours | High (WCAG compliance) |
| Default to compact table density for desktop | 1-2 hours | Medium |
| Add column priority (hide low-priority columns on mobile) | 2-3 days | Medium |
| **Skip PWA** — not worth it for 10-30 internal users | — | — |

**Responsive table macro:**
```html
{% macro responsive_table(caption_id, caption_text) %}
<div role="region" aria-labelledby="{{ caption_id }}" tabindex="0"
     class="overflow-auto rounded-lg">
  <table class="min-w-full">
    <caption id="{{ caption_id }}" class="sr-only">{{ caption_text }}</caption>
    {{ caller() }}
  </table>
</div>
{% endmacro %}
```

---

## Area 8: Competitor UX Analysis

### Competitors Evaluated

| Platform | UX Maturity | Key Differentiator |
|----------|:---:|---|
| Azure Portal (native) | ★★★★★ | Smart views, insights panel, scope selectors |
| Vantage.sh | ★★★★☆ | Clean, cost-focused, % change badges |
| CloudHealth (Broadcom) | ★★★★☆ | AI co-pilot (Intelligent Assist), FlexOrgs |
| Flexera One | ★★★½☆ | Card-based automation catalog, sidebar nav |
| CoreStack | ★★★☆☆ | AI-focused, Accounts Governance Dashboard |
| Turbot/Guardrails | ★★★☆☆ | Prevention-first (PSPM), less dashboard-oriented |

### Our Unique Differentiators (Double Down on These)

1. **Unified cross-tenant view** — Azure Portal fragments into 5 separate blades; we aggregate
2. **Riverside compliance deadline tracker** — unique to our use case
3. **Multi-brand design system** — no competitor handles franchise branding
4. **Lightweight HTMX approach** — faster perceived performance than React SPAs
5. **Cost + Compliance + Identity + DMARC in one place** — no competitor offers this combination

### What NOT to Copy
- Don't add AI chatbot yet (P3 at best — our 10-30 users know what they want)
- Don't build FlexOrgs-level hierarchy (4-5 tenants don't need it)
- Don't replicate Azure Portal blade-by-blade (our value is aggregation)

---

## Effort vs Impact Matrix

```
                        HIGH IMPACT
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    │  ★ WCAG critical      │  ★ 3-level dashboard  │
    │    fixes (2-4h)       │    hierarchy (1-2d)   │
    │                       │                       │
    │  ★ Tenant scope       │  ★ DaisyUI adoption   │
    │    selector (2-4h)    │    (1d)               │
    │                       │                       │
    │  ★ % change badges    │  ★ Chart a11y         │
    │    (1-2h)             │    plugins (2-3d)     │
    │                       │                       │
    │  ★ axe-core CI (2h)   │  ★ SSE for sync (4-6h)│
    │                       │                       │
    │  ★ HTMX 2.0 (2-4h)   │  ★ Side panel detail  │
    │                       │    view (4-5d)        │
    │  ★ Alpine.js (1d)     │                       │
LOW ├───────────────────────┼───────────────────────┤ HIGH
EFFORT  ★ Manual a11y       │  ★ Skeleton screens   │ EFFORT
    │    checklist (1h)     │    (3h)               │
    │                       │                       │
    │  ★ Last synced        │  ★ Token restructure  │
    │    timestamps (1-2h)  │    (4h)               │
    │                       │                       │
    │  ★ Responsive table   │  ★ Card-based rule    │
    │    macro (1h)         │    catalog (1-2d)     │
    │                       │                       │
    │  ★ Density toggle     │  ★ Bulk operations    │
    │    (1-2d)             │    (3-4d)             │
    │                       │                       │
    │                       │  ★ Insights panel     │
    │                       │    (4-8h)             │
    │                       │                       │
    └───────────────────────┼───────────────────────┘
                            │
                       LOW IMPACT
```

### Prioritized Implementation Roadmap

**Sprint 1 — Week 1-2 (Foundation & Critical Fixes)**
- [ ] Fix 5 WCAG critical violations (invisible text, focus conflicts) — 4h
- [ ] Upgrade HTMX 1.9.12 → 2.0.7 — 4h
- [ ] Add Alpine.js 3.15.9 to base.html — 4h
- [ ] Install axe-playwright-python CI pipeline — 2h
- [ ] Add tenant scope selector — 4h
- [ ] Add % change badges to KPIs — 2h
- [ ] Create manual a11y testing checklist — 1h

**Sprint 2 — Week 3-4 (UX Improvements)**
- [ ] Install DaisyUI 5.5.x + create 5 brand themes — 4h
- [ ] Redesign dashboard with 3-level hierarchy — 2d
- [ ] Replace sync polling with SSE — 6h
- [ ] Add Chart.js a11y plugins + data tables — 2d
- [ ] Add responsive table macro — 1h
- [ ] Add HTMX focus management — 2h

**Sprint 3 — Week 5-6 (Polish)**
- [ ] Migrate components to DaisyUI classes — 1d
- [ ] Restructure tokens to 3-tier architecture — 4h
- [ ] Add side panel detail view — 5d
- [ ] Replace red/green chart palette with accessible colors — 4h
- [ ] Add skeleton screens for dashboard — 3h
- [ ] Add collapsible sections with lazy loading — 3d

**Sprint 4 — Week 7-8 (Refinement)**
- [ ] Migrate dmarc_dashboard.html + riverside_dashboard.html violations — 2d
- [ ] Add insights/anomaly slide-in panel — 8h
- [ ] Add card-based compliance rule catalog — 2d
- [ ] Add density toggle — 2d
- [ ] Full WCAG 2.2 manual audit — 3h

---

## Final Verdict

### Is the Current Frontend Architecture Appropriate?

**Yes — with targeted improvements.**

The HTMX + Jinja2 + Tailwind CSS stack is architecturally correct for this use case. The evidence is overwhelming:

1. **User count (10-30)** — SPA frameworks provide zero measurable benefit at this scale
2. **Desktop-primary power users** — HTMX's server-rendered approach gives faster perceived performance than SPAs with hydration overhead
3. **Data-heavy tables + charts** — Server-side pagination + HTMX partial swaps is the optimal pattern
4. **Multi-brand theming** — CSS custom properties with server-side injection works perfectly; SPA frameworks would require rewriting the entire theme system
5. **Python team** — Full-stack ownership with FastAPI + Jinja2; SPA would split into Python backend + JavaScript frontend teams
6. **Cost** — $15-50/month hosting; SPA would add Node.js infrastructure and build pipeline costs

### Should It Evolve?

**Yes, in 3 specific ways:**

1. **Upgrade to HTMX 2.0 + Alpine.js** — This is the "95% of SPA benefits at 5% of the cost" solution. Alpine.js fills the client-side interactivity gap (tabs, toggles, dropdowns, form validation) that HTMX can't handle. Combined bundle: 33 kB.

2. **Adopt DaisyUI as component library** — The custom design system has 52 violations and is expensive to maintain. DaisyUI gives pre-built, themeable components with zero JavaScript overhead. Migrate incrementally.

3. **Invest in accessibility infrastructure** — The #1 gap is not the architecture, it's the quality of the implementation. Automated CI testing + quarterly manual audits + the 7 WCAG 2.2 manual criteria will close this gap.

### What Should NOT Change

- **Don't migrate to React/Vue/Svelte** — The research is clear: $75K-$150K migration cost, 3-6 month feature freeze, zero user benefit at this scale
- **Don't add a bundler (Vite/webpack)** — The current no-build-step approach for JS is fine; Tailwind CLI for CSS is sufficient
- **Don't add PWA** — ROI is too low for 10-30 internal users on corporate LAN
- **Don't add AI chatbot** — Power users who live in this tool daily don't need a chatbot; they need faster drill-down and better data density

---

## WCAG 2.2 AA Manual Audit Checklist

**⚠️ This checklist MUST accompany every UI deliverable. Automated tools (axe-core 4.11.1) catch approximately 30-40% of WCAG issues. The following 7 criteria REQUIRE manual testing.**

### 1. Focus Not Obscured (SC 2.4.11 / 2.4.12)
- [ ] Tab through every page — focused element is NEVER obscured by sticky nav or modals
- [ ] Test with mobile menu open — focus doesn't go behind overlay
- [ ] Test consent banner — focus ring visible when tabbing past it
- [ ] Test side panel (if implemented) — focus moves to panel, not behind it

### 2. Focus Appearance (SC 2.4.13)
- [ ] Focus indicator is visible on ALL interactive elements in BOTH light and dark mode
- [ ] Focus ring contrast ≥ 3:1 against adjacent colors
- [ ] Focus ring area ≥ 2px outline (current: 3px in accessibility.css — verify it's not overridden)
- [ ] Focus indicator visible in Windows High Contrast Mode

### 3. Dragging Movements (SC 2.5.7)
- [ ] No drag-only interactions exist in the entire application
- [ ] If chart zoom requires drag, an alternative exists (zoom buttons)
- [ ] Any sortable lists have button-based reordering alternatives

### 4. Target Size (SC 2.5.8)
- [ ] ALL interactive targets are ≥ 24×24 CSS pixels
- [ ] Inline text links are exempt but must have sufficient spacing
- [ ] Icon-only buttons (theme toggle, mobile hamburger, refresh) meet 24×24px
- [ ] Table row action links/buttons meet 24×24px

### 5. Consistent Help (SC 3.2.6)
- [ ] Footer links (Privacy Policy, version) appear in same order on ALL pages
- [ ] Help mechanisms (if any) are in the same relative position across pages
- [ ] Error recovery guidance follows consistent patterns

### 6. Redundant Entry (SC 3.3.7)
- [ ] Tenant selection persists across page navigations (via cookie/URL param)
- [ ] Filter settings don't require re-entry when navigating back
- [ ] Multi-step operations auto-populate already-provided information

### 7. Accessible Authentication (SC 3.3.8 / 3.3.9)
- [ ] Login uses standard username/password (✅ exempt) or Azure AD OAuth (✅ exempt)
- [ ] No CAPTCHA or cognitive function test required
- [ ] If MFA added in future: must support paste, authenticator apps, passkeys
- [ ] Password managers can autofill login form

### Testing Schedule
| Cadence | Scope | Who |
|---------|-------|-----|
| Monthly | 30-min keyboard walkthrough of changed pages | Any developer |
| Quarterly | Full checklist above | Designated a11y champion (rotate) |
| Per release | axe-playwright-python CI on all pages | Automated |
| Annually | Third-party WCAG 2.2 audit | External auditor |

---

## Research Sources

All research was conducted via the web-puppy agent on March 27, 2026. Raw findings, source credibility assessments, and detailed analysis are saved in:

| Directory | Files | Size | Coverage |
|-----------|-------|------|----------|
| `research/htmx-vs-frameworks-2026/` | 8 files | ~52 KB | Area 2: HTMX vs frameworks |
| `research/dashboard-design-patterns-2026/` | 8 files | ~97 KB | Area 1: Dashboard patterns |
| `research/design-systems-2026/` | 8+ files | ~65 KB | Area 3: Design systems |
| `research/chart-libraries-2026/` | 10 files | ~72 KB | Area 4: Data visualization |
| `research/a11y-performance-2026/` | 8 files | ~68 KB | Areas 5+6: A11y + Performance |
| `research/competitor-ux-2026/` | 11 files | ~85 KB | Area 8: Competitor UX |
| `DESIGN_SYSTEM_AUDIT.md` | 1 file | 18 KB | Design system violations |

**Total research corpus: ~457 KB across 54+ files**
