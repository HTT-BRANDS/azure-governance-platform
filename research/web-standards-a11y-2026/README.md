# Web Standards & Accessibility Research - March 2026

## Executive Summary

This research provides current (March 2026) web standards and accessibility guidance for a comprehensive UI/UX audit of the Azure Governance Platform. The platform uses **HTMX with server-side rendering**, **Tailwind CSS v4**, and requires compliance with **WCAG 2.2 AA**, **Core Web Vitals**, **GPC (Global Privacy Control)**, and modern accessibility tooling.

### Project Context
- **Tech Stack**: Python/FastAPI, HTMX 1.9.12, Tailwind CSS v4+, Chart.js
- **Architecture**: Server-side rendered with HTMX for dynamic interactions
- **Accessibility Requirements**: WCAG 2.2 AA compliance
- **Privacy Requirements**: GPC (Global Privacy Control) - CCPA/CPRA compliant

---

## Key Findings Summary

### 1. WCAG 2.2 AA Status (October 2023 → Current)
**Current Status**: WCAG 2.2 published October 5, 2023 - no major changes since 2025

**Critical Update**: Seven criteria require manual testing (43% of WCAG 2.2 AA issues):
- 2.4.11 Focus Not Obscured (AA) - **Requires manual testing**
- 2.4.13 Focus Appearance (AAA) - **Cannot be automated**
- 2.5.7 Dragging Movements (AA) - **Requires manual testing**
- 2.5.8 Target Size (AA) - **Partial automation**
- 3.2.6 Consistent Help (A) - **Cannot be automated**
- 3.3.7 Redundant Entry (A) - **Limited automation**
- 3.3.8 Accessible Authentication (AA) - **Cannot be automated**

### 2. Core Web Vitals 2026
**No changes from 2025 thresholds**:
- **LCP**: ≤ 2.5s (Good), 2.5-4.0s (Needs Improvement), > 4.0s (Poor)
- **INP**: ≤ 200ms (Good), 200-500ms (Needs Improvement), > 500ms (Poor)
- **CLS**: ≤ 0.1 (Good), 0.1-0.25 (Needs Improvement), > 0.25 (Poor)

**Note**: INP (Interaction to Next Paint) replaced FID in 2024 and is now stable. TBT remains a lab proxy for INP.

### 3. HTMX Accessibility Patterns
- Use `aria-live` regions for dynamic content announcements
- Implement focus management for HTMX swaps
- Ensure keyboard navigation works with HTMX-boosted links
- Screen reader announcements via `hx-swap-oob`

### 4. GPC (Global Privacy Control) - CRITICAL
**Status**: As of January 2025, **4 states** (CA, CO, CT, NJ) explicitly require GPC compliance:
- `Sec-GPC: 1` header must be honored as legally binding opt-out
- **$2,500-$7,500 per violation** under CCPA §1798.155
- Implementation requires: header detection, session persistence, cookie filtering

### 5. Tailwind CSS v4
**Released**: January 2025
- CSS-first configuration (no JavaScript config file needed)
- Built-in `@import` support
- Improved accessibility utilities
- Built-in `prefers-reduced-motion` and `prefers-contrast` support

### 6. axe-core 4.11.1
**Released**: January 2025
- Latest ruleset with improved WCAG 2.2 support
- New rules for focus management and semantic HTML
- Better support for custom elements

### 7. Manual Testing Requirements
**43% of accessibility issues require manual testing**:
- Keyboard navigation flows
- Screen reader testing (NVDA, JAWS, VoiceOver)
- Color contrast verification
- Focus indicator visibility
- Cognitive accessibility assessment

---

## Immediate Action Items

### P0 - Critical (Legal/Compliance Risk)
1. **GPC Implementation**: Implement middleware to detect `Sec-GPC: 1` header
2. **WCAG 2.2 Manual Testing**: Audit 7 non-automatable criteria
3. **axe-core 4.11.1 Update**: Upgrade from 4.10.x to latest

### P1 - High Priority
1. **Focus Not Obscured**: Audit sticky headers/footers in HTMX app
2. **INP Optimization**: Review HTMX interactions for responsiveness
3. **Target Size**: Verify 24x24px minimum for all interactive elements

### P2 - Medium Priority
1. **Tailwind v4 Accessibility**: Leverage new `prefers-reduced-motion` utilities
2. **Consistent Help**: Review help placement across pages
3. **Redundant Entry**: Implement form auto-population

---

## Research Files

- `sources.md` - All sources with credibility assessments
- `analysis.md` - Multi-dimensional analysis
- `recommendations.md` - Project-specific actionable recommendations
- `raw-findings/` - Extracted content from authoritative sources

---

## Source Credibility Assessment

| Source | Tier | Currency | Notes |
|--------|------|----------|-------|
| W3C WCAG 2.2 | Tier 1 | Oct 2023 (stable) | Official specification |
| web.dev Core Web Vitals | Tier 1 | Sept 2025 (updated) | Google official |
| GPC Global Privacy Control | Tier 1 | Jan 2025 (legal updates) | Official specification |
| HTMX Documentation | Tier 2 | Current | Authoritative but community |
| axe-core GitHub | Tier 1 | Jan 2025 | Official releases |
| Tailwind CSS Blog | Tier 2 | Current | Vendor documentation |

---

*Research conducted: March 2026*  
*Researcher: Web-Puppy (web-puppy-9875c1)*
*Project: Azure Governance Platform UI/UX Audit*
