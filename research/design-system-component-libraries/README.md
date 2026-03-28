# Design Systems & Component Libraries for Internal Governance Tools

**Research Date:** March 27, 2026  
**Researcher:** web-puppy-b82181  
**Project Context:** Azure Governance Platform — Jinja2 + HTMX + Tailwind CSS v4.2, 5 brand themes, no JS framework

---

## Executive Summary

### The Bottom Line

**Keep and enhance your custom design system.** After evaluating 7 component libraries against your Jinja2 + HTMX + Tailwind CSS v4.2 stack, the best path forward is:

1. **Primary recommendation: DaisyUI 5.x** as a Tailwind CSS plugin to replace hand-written component CSS (buttons, cards, badges, etc.) while keeping your custom brand token system intact
2. **Secondary source: Tailwind Plus** ($299–$979) for professionally designed HTML component patterns to adapt into Jinja2 macros
3. **Do NOT adopt** React-dependent libraries (shadcn/ui, Radix, Headless UI) — they require a fundamental architecture change

### Critical Finding: Most Libraries Require React

| Library | Framework Dependency | Usable with Jinja2+HTMX? |
|---------|---------------------|--------------------------|
| **DaisyUI 5.5.19** | None (CSS-only) | ✅ **YES — Best fit** |
| **Flowbite 4.0.1** | None (vanilla JS) | ✅ **YES — Good fit** |
| **Tailwind Plus** | HTML / React / Vue | ⚠️ **Partial — HTML blocks only** |
| **Carbon Web Components** | None (Web Components) | ⚠️ **Partial — Heavy overhead** |
| **shadcn/ui** | React required | ❌ **NO** |
| **Radix Primitives** | React required | ❌ **NO** |
| **Headless UI 2.1** | React or Vue required | ❌ **NO** |

### Key Answers

1. **Is maintaining 47+ CSS custom properties × 5 brands sustainable?** — Yes, and it's actually a strength. Your Pydantic-validated, server-generated approach is more secure and maintainable than most client-side theming systems. DaisyUI's `data-theme` approach validates this pattern.

2. **Which libraries work with Jinja2 + HTMX?** — Only DaisyUI and Flowbite work natively. Tailwind Plus provides copyable HTML patterns.

3. **Best WCAG 2.2 AA compliance?** — Your custom system (with color_utils.py WCAG validation) is already better than DaisyUI or Flowbite. Carbon Design System has the best out-of-box accessibility, but requires Web Components overhead.

4. **Migration cost assessment?** — DaisyUI integration: ~2-3 days. Full React migration: 3-6 months. Recommendation: Don't migrate, augment.

---

## Detailed Comparison Matrix

| Dimension | DaisyUI 5.x | Flowbite 4.x | Tailwind Plus | Carbon WC | shadcn/ui | Radix | Headless UI |
|-----------|------------|-------------|---------------|-----------|-----------|-------|-------------|
| **Version** | 5.5.19 | 4.0.1 | N/A (product) | 11.104.0 | Latest | Latest | 2.1 |
| **GitHub Stars** | 40.6k | 9.2k | N/A | 9k (mono) | 111k | — | — |
| **License** | MIT | MIT | Commercial | Apache 2.0 | MIT | MIT | MIT |
| **Cost** | Free | Free (Pro: paid) | $299/$979 | Free | Free | Free | Free |
| **Tailwind v4** | ✅ Native | ✅ v4 support | ✅ Native | ❌ Own CSS | ✅ | N/A | N/A |
| **No JS Framework** | ✅ CSS-only | ✅ Vanilla JS | ✅ HTML blocks | ⚠️ Web Components | ❌ React | ❌ React | ❌ React/Vue |
| **Custom Theming** | ✅ CSS vars | ⚠️ Limited | ❌ Manual | ✅ Tokens | ✅ CSS vars | N/A | N/A |
| **Multi-brand** | ✅ data-theme | ⚠️ Manual | ❌ | ⚠️ Tokens | ✅ | N/A | N/A |
| **WCAG AA** | ⚠️ Partial | ⚠️ Partial | ⚠️ Partial | ✅ Strong | ✅ Good | ✅ Excellent | ✅ Excellent |
| **Dark Mode** | ✅ Built-in | ✅ Built-in | ✅ | ✅ | ✅ | N/A | N/A |
| **Components** | 55+ | 56+ | 500+ | 40+ | 50+ | 30+ | 10+ |
| **Server-render** | ✅ | ✅ | ✅ HTML | ⚠️ | ❌ | ❌ | ❌ |
| **Active Maint.** | ✅ 2 days ago | ⚠️ Nov 2025 | ✅ | ✅ 3 days ago | ✅ | ✅ | ⚠️ |

---

## Recommendation for This Project

### Tier 1: Immediate Value (Week 1)

**Integrate DaisyUI 5.x as a Tailwind plugin alongside your existing token system.**

Why:
- Zero architecture change — adds `@plugin "daisyui"` to your existing CSS
- CSS-only components (`class="btn"`, `class="card"`) work directly in Jinja2 macros
- `data-theme` attribute mirrors your existing `data-brand` attribute
- Custom themes via CSS variables align with your `css_generator.py` approach
- 40.6k stars, MIT license, actively maintained
- Eliminates ~200 lines of hand-written component CSS (btn-brand, card-brand, etc.)

### Tier 2: Design Reference (Month 1)

**Purchase Tailwind Plus ($299 personal) for design patterns.**

Why:
- 500+ professionally designed HTML component examples
- Copy-paste HTML into Jinja2 macros
- Accessibility patterns to reference
- One-time cost, lifetime updates

### Tier 3: Do Not Adopt

**shadcn/ui, Radix Primitives, and Headless UI are eliminated.**

Why:
- All require React or Vue as a runtime dependency
- Would require adding ~40-100KB of JavaScript framework
- Fundamental architecture change from server-rendered to client-rendered
- Contradicts the HTMX philosophy of the current stack

See [analysis.md](./analysis.md) for detailed per-library analysis.  
See [sources.md](./sources.md) for source credibility assessments.  
See [recommendations.md](./recommendations.md) for implementation guidance.
