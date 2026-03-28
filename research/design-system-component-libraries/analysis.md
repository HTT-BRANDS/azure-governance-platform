# Multi-Dimensional Analysis: Component Libraries

**Research Date:** March 27, 2026  
**Project:** Azure Governance Platform (Jinja2 + HTMX + Tailwind CSS v4.2)

---

## 1. DaisyUI 5.5.19

### Overview
The most popular free and open-source Tailwind CSS component library. Pure CSS components with no JavaScript dependencies. Uses Tailwind v4's `@plugin` directive.

### Framework Compatibility: ✅ EXCELLENT
- **Zero JavaScript dependency** — components are CSS classes only
- Works with any HTML: Jinja2, HTMX, plain HTML, any templating engine
- Installation: `@plugin "daisyui"` in CSS file — one line
- Components use semantic class names: `btn`, `card`, `badge`, `modal`, `alert`

### Multi-Brand Theming: ✅ EXCELLENT
- Uses `data-theme` attribute (analogous to project's `data-brand`)
- Custom themes via `@plugin "daisyui/theme"` with CSS custom properties
- 35 built-in themes + unlimited custom themes
- Theme variables use oklch color space (modern, perceptually uniform)
- **Direct mapping to project's architecture**: your `css_generator.py` could generate DaisyUI-compatible theme variables
- Per-element theming supported: `<div data-theme="mytheme">` scopes theme to subtree

### Tailwind v4 Compatibility: ✅ NATIVE
- v5.x designed specifically for Tailwind v4
- Uses `@plugin "daisyui"` (Tailwind v4 plugin syntax)
- Custom themes use `@plugin "daisyui/theme" { ... }` directive
- No config file needed — everything in CSS

### Accessibility: ⚠️ PARTIAL (requires developer effort)
- **Modal**: Recommends HTML `<dialog>` element (native accessibility, Esc key support)
- **Buttons**: Provides semantic class structure but ARIA attributes are developer responsibility
- **No automatic ARIA roles** — DaisyUI styles elements, doesn't add behavior
- **Focus management**: Relies on browser defaults + Tailwind's `focus-visible`
- **Color contrast**: Built-in themes pass WCAG AA, but custom themes need manual validation
- **Assessment**: Your existing Jinja2 macros with explicit `role`, `aria-label`, `aria-disabled` attributes are MORE accessible than DaisyUI defaults

### Security: ✅ LOW RISK
- CSS-only — no executable JavaScript
- No runtime dependencies
- Open source (MIT), auditable
- Styles don't affect security posture

### Cost: ✅ FREE
- MIT license, fully open source
- No premium tier required for component access
- Optional paid templates/themes available but not needed

### Implementation Complexity: ✅ LOW
- Add one npm dependency + one CSS line
- Rename existing component classes to DaisyUI conventions
- Keep existing brand token system (css_generator.py, design_tokens.py)
- Gradual adoption possible — use DaisyUI classes alongside existing styles

### Stability: ✅ GOOD
- 40.6k GitHub stars, 1.6k forks
- 2,921 commits, 632 tags
- Active: last commit 2 days ago (March 25, 2026)
- Single maintainer (saadeghi) — slight bus factor risk
- MIT license — can fork if abandoned

### Integration Estimate
```
Effort:        2-3 days
Risk:          Low
Breaking:      None (additive change)
Reversibility: High (remove plugin, revert to custom CSS)
```

---

## 2. Flowbite 4.0.1

### Overview
Open-source Tailwind CSS component library with optional vanilla JavaScript for interactive elements. Uses data attributes for behavior (similar to HTMX pattern).

### Framework Compatibility: ✅ GOOD
- Core components are Tailwind CSS utility classes (HTML templates)
- Interactive components (modals, dropdowns, tooltips) use vanilla JavaScript
- **Data attributes API**: `data-modal-target`, `data-dropdown-toggle` — similar to HTMX's `hx-*`
- JavaScript is optional — static components work without it
- Has `initFlowbite()` function for data attribute initialization

### Multi-Brand Theming: ⚠️ LIMITED
- Relies on Tailwind's theme configuration for colors
- No built-in multi-theme system like DaisyUI's `data-theme`
- Custom theming requires overriding Tailwind theme values
- Flowbite v4 introduced "Design System with variable tokens" (announced but limited documentation)
- Would need significant customization to support 5-brand system

### Tailwind v4 Compatibility: ✅ SUPPORTED
- v4.0 released with Tailwind v4 support
- Migration guide from v3 to v4 available
- Uses `@plugin "flowbite/plugin"` for Tailwind v4

### Accessibility: ⚠️ PARTIAL
- Interactive components include basic keyboard navigation
- Data attribute components handle focus trapping in modals
- ARIA attributes included in documentation examples but not enforced
- No automated accessibility validation
- Less consistent than DaisyUI's approach to native HTML elements

### Security: ⚠️ MODERATE
- Includes JavaScript file (potential attack surface)
- Data attributes interface is safe (read-only attributes)
- JavaScript API has more surface area
- Open source, auditable

### Cost: ✅ FREE (with paid Pro option)
- MIT license for core library
- Flowbite Pro: paid templates and advanced components
- Pro pricing not required for basic components

### Implementation Complexity: ⚠️ MODERATE
- Need to include Flowbite JavaScript bundle (~20KB)
- Must call `initFlowbite()` or component-specific init functions
- **Potential conflict with HTMX**: Both use data attributes for behavior, could cause confusion
- Components use long utility class strings (less clean than DaisyUI's semantic classes)

### Stability: ⚠️ FAIR
- 9.2k GitHub stars, 851 forks
- Last release: November 17, 2025 (4 months ago)
- 215 open issues
- Active but slower update cadence than DaisyUI

### Integration Estimate
```
Effort:        3-5 days
Risk:          Moderate (JS conflicts with HTMX possible)
Breaking:      None (additive)
Reversibility: Moderate (JS integration harder to unwind)
```

---

## 3. Tailwind Plus (formerly Tailwind UI)

### Overview
Official component library from the Tailwind CSS team. Provides 500+ professionally designed, responsive component examples. Paid product with HTML, React, and Vue code.

### Framework Compatibility: ⚠️ PARTIAL
- **UI Blocks provide HTML code** — directly usable in Jinja2 templates
- Templates are React/Next.js only
- UI Kit is React-only
- HTML blocks are static — no interactive behavior included
- Must implement JS behavior yourself (or with HTMX)

### Multi-Brand Theming: ❌ NOT BUILT-IN
- Components use Tailwind utility classes with hardcoded colors
- No theming system — you'd need to manually replace color classes
- Not designed for multi-brand applications
- Would need significant adaptation to use CSS custom properties

### Tailwind v4 Compatibility: ✅ NATIVE
- Built by the Tailwind CSS team — always up to date
- Uses latest Tailwind v4 features and patterns

### Accessibility: ⚠️ PARTIAL
- HTML examples include basic ARIA attributes
- Interactive patterns (dropdowns, modals) show correct ARIA markup
- No runtime enforcement — it's just HTML patterns to copy
- Quality is high but you must maintain it yourself

### Security: ✅ LOW RISK
- It's just HTML/CSS code you copy — no runtime dependency
- No JavaScript included (in HTML blocks)
- Source code is yours to audit

### Cost: 💰 PAID
- Personal: **$299 one-time** (1 developer)
- Team: **$979 one-time** (up to 25 people)
- Lifetime access including future updates

### Implementation Complexity: ⚠️ MODERATE
- Copy HTML into Jinja2 macros
- Replace hardcoded colors with CSS variable references
- Add HTMX attributes for interactive behavior
- Good reference but requires adaptation work

### Stability: ✅ EXCELLENT
- Backed by Tailwind Labs (well-funded company)
- Continuous updates with new components
- Will always support latest Tailwind CSS version

### Integration Estimate
```
Effort:        1-2 weeks (adapting patterns to macros)
Risk:          Low (reference code, not dependency)
Breaking:      None
Reversibility: N/A (you own the code)
```

---

## 4. IBM Carbon Design System (Web Components)

### Overview
IBM's open-source design system for digital products. Available as React components and Web Components. The Web Components version (`@carbon/web-components` v11.104.0) is framework-agnostic.

### Framework Compatibility: ⚠️ POSSIBLE BUT HEAVY
- Web Components work in any HTML (including Jinja2 templates)
- Usage: `<cds-button>Click me</cds-button>` — custom HTML elements
- Requires JavaScript runtime for Web Components (~100KB+)
- Shadow DOM encapsulation may conflict with Tailwind utility classes
- Not designed for Tailwind CSS — has its own CSS system

### Multi-Brand Theming: ⚠️ LIMITED
- Uses CSS custom properties for theming (compatible concept)
- Has light/dark theme tokens
- Custom themes possible but follow Carbon's design language
- Not designed for arbitrary brand colors — assumes IBM's design grid
- Would require significant effort to map 5 franchise brands

### Tailwind v4 Compatibility: ❌ INCOMPATIBLE
- Carbon has its own CSS framework — doesn't use Tailwind
- Shadow DOM encapsulation blocks Tailwind utility classes
- Would need to maintain TWO CSS systems side by side

### Accessibility: ✅ EXCELLENT
- IBM's dedication to accessibility is industry-leading
- All components meet WCAG 2.1 AA minimum
- Many components target WCAG 2.1 AAA
- Screen reader tested across JAWS, NVDA, VoiceOver
- Keyboard navigation fully implemented
- Focus management in complex components (modals, date pickers)
- Regular accessibility audits

### Security: ✅ GOOD
- Enterprise-grade (IBM uses it in production)
- Regular security updates
- Apache 2.0 license
- Large contributor base (2.1k forks)

### Cost: ✅ FREE
- Apache 2.0 license — permissive open source
- No paid tiers

### Implementation Complexity: ❌ HIGH
- Requires adding Web Components polyfills
- Shadow DOM conflicts with existing Tailwind system
- Different styling paradigm than current architecture
- Learning curve for Carbon's design token system
- Would require maintaining two parallel CSS systems

### Stability: ✅ EXCELLENT
- IBM-backed, enterprise-grade
- 9k GitHub stars, 2.1k forks
- 976 open issues (actively tracked)
- Last commit: 3 days ago
- Regular release cadence (v11.104.0)

### Integration Estimate
```
Effort:        2-4 weeks (fundamental architecture change)
Risk:          High (dual CSS system, Shadow DOM conflicts)
Breaking:      Yes (template changes throughout)
Reversibility: Low
```

---

## 5. shadcn/ui

### Overview
The most popular React component library (111k GitHub stars). A code distribution system — you copy component code into your project and own it. Built on Radix Primitives.

### Framework Compatibility: ❌ REACT ONLY
- Requires React as a runtime dependency
- Dependencies: `shadcn`, `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`
- Needs TypeScript/JavaScript build pipeline (`tsconfig.json`)
- Supported frameworks: Next.js, Vite, Astro, React Router, TanStack Start, Laravel (with Inertia)
- **No HTML-only, no Jinja2, no vanilla JS option**

### Why It's Eliminated
Adding shadcn/ui would require:
1. Adding React (~40KB min) + ReactDOM (~120KB)
2. Setting up a JavaScript build pipeline
3. Converting Jinja2 templates to React components
4. Potentially re-architecting HTMX interactions
5. Estimated effort: **3-6 months of migration**

### What You CAN Learn From It
- CSS variable theming pattern (similar to your approach)
- Component composition patterns
- The `cn()` utility for conditional class merging
- ARIA patterns in component code

---

## 6. Radix Primitives

### Overview
Unstyled, accessible React primitives for building design systems. Made by WorkOS. The foundation under shadcn/ui.

### Framework Compatibility: ❌ REACT ONLY
- Explicitly: "Unstyled, accessible, open source **React** primitives"
- No Web Components, no vanilla JS, no Vue option
- Headless approach — provides behavior, you provide styles

### Why It's Eliminated
Same as shadcn/ui — requires React. The overhead of adding React just for accessible primitives is not justified when:
- Your Jinja2 macros already have ARIA attributes
- Native HTML elements (`<dialog>`, `<details>`) provide most accessible patterns
- DaisyUI recommends native HTML elements for accessibility

### What You CAN Learn From It
- Focus management patterns
- Keyboard navigation implementations
- ARIA attribute specifications per component type

---

## 7. Headless UI 2.1

### Overview
Completely unstyled, fully accessible UI components by the Tailwind CSS team. Designed for React and Vue.

### Framework Compatibility: ❌ REACT OR VUE ONLY
- Only two framework options: React and Vue
- No vanilla JS, no Web Components, no HTML-only option
- Provides accessible behavior without styles

### Why It's Eliminated
Despite being from the Tailwind CSS team, Headless UI requires React or Vue. The project uses HTMX + vanilla JS, making this incompatible.

### What You CAN Learn From It
- Reference implementation for accessible component behavior
- Transition and animation patterns
- Focus trap implementation details

---

## Cross-Cutting Analysis

### Accessibility Ranking (for this project's context)

1. **Your existing custom system** — Jinja2 macros already include `role`, `aria-label`, `aria-disabled`, `aria-current`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`. Combined with `color_utils.py` WCAG validation, this is enterprise-grade.
2. **Carbon Design System** — Best out-of-box accessibility, but incompatible with Tailwind
3. **DaisyUI** — Good foundation with native HTML elements (`<dialog>`), but requires developer ARIA additions
4. **Flowbite** — Adequate but inconsistent across components
5. **Tailwind Plus** — Good patterns to copy but no runtime enforcement

### Multi-Brand Theming Ranking

1. **Your existing custom system** — Purpose-built for 5-brand theming with validated CSS variables
2. **DaisyUI** — `data-theme` system is architecturally aligned, supports unlimited themes
3. **Carbon** — Token-based but not designed for arbitrary brands
4. **Flowbite** — Basic dark mode but no multi-brand support
5. **Tailwind Plus** — No theming system at all

### Total Cost of Ownership (3-year projection)

| Option | Year 1 | Year 2 | Year 3 | Total |
|--------|--------|--------|--------|-------|
| **Keep Custom + DaisyUI** | $0 + 3 days effort | Minimal maintenance | Minimal maintenance | ~$2,000 in dev time |
| **Keep Custom + Tailwind Plus** | $299-979 + 2 weeks | Adapt new patterns | Adapt new patterns | ~$5,000-10,000 |
| **Carbon Web Components** | 4 weeks migration | Learning curve, dual systems | Ongoing complexity | ~$30,000-50,000 |
| **React Migration (shadcn/ui)** | 3-6 months migration | React ecosystem maintenance | React version upgrades | ~$100,000-200,000 |

### HTMX Compatibility Assessment

| Library | HTMX Conflict Risk | Notes |
|---------|-------------------|-------|
| **DaisyUI** | ✅ None | CSS-only, no JS to conflict |
| **Flowbite** | ⚠️ Low-Medium | Both use data attributes; Flowbite's JS init may re-bind elements HTMX swaps |
| **Tailwind Plus** | ✅ None | HTML patterns, no JS |
| **Carbon WC** | ⚠️ Medium | Web Components may not re-render properly after HTMX DOM swaps |
