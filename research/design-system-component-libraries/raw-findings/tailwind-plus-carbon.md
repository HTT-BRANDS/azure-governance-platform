# Tailwind Plus & Carbon Design System — Raw Findings

## Tailwind Plus (formerly Tailwind UI)

### Product Details
- **URL:** https://tailwindcss.com/plus (redirects from tailwindui.com)
- **Rebrand:** "Tailwind UI" → "Tailwind Plus"
- **Maker:** Tailwind Labs
- **Banner:** "Introducing Oatmeal — Our new multi-theme marketing site kit"

### Pricing (Verified March 27, 2026)
- **Personal License:** $299 one-time payment (plus local taxes)
  - For individuals working on their next big idea
  - Lifetime access to everything + future additions
- **Team License:** $979 one-time payment (plus local taxes)
  - For product teams and agencies
  - Up to 25 people
  - Get access for your entire team

### Product Tiers
1. **UI Blocks** — 500+ professionally designed, fully responsive component examples
   - Available in **HTML**, **React**, and **Vue** ← HTML is key for Jinja2
   - Categories: Application UI, Marketing, E-commerce
2. **Templates** — Visually-stunning site templates built with React and Next.js
   - React/Next.js only — NOT usable with Jinja2
3. **UI Kit** — A React starter kit built with Tailwind CSS
   - React only — NOT usable with Jinja2

### Key Takeaway
Only UI Blocks (HTML view) are useful for this project. The $299 buys access
to 500+ HTML patterns that can be adapted into Jinja2 macros. Templates and
UI Kit are React-only.

### Framework Support for UI Blocks
- HTML ✅ (plain Tailwind classes — perfect for Jinja2)
- React ✅
- Vue ✅

---

## IBM Carbon Design System

### Repository
- **GitHub:** https://github.com/carbon-design-system/carbon
- **Stars:** 9k
- **Forks:** 2.1k
- **Issues:** 976 open
- **PRs:** 85 open
- **License:** Apache 2.0
- **Last Commit:** 3 days ago (March 24, 2026)

### Framework Support
- **React** — Primary implementation (`@carbon/react`)
- **Web Components** — Framework-agnostic (`@carbon/web-components` v11.104.0)
- **Community Frameworks** — Angular, Vue, Svelte (community-maintained)
- **No vanilla HTML/CSS** option (unlike DaisyUI)

### Web Components Package
- Path: `packages/web-components` in monorepo
- Latest: v11.104.0 (release commit: March 24, 2026)
- Storybook: https://web-components.carbondesignsystem.com/
- Active development: commits 3 days ago

### Web Components Usage
```html
<!-- Import the component -->
<script type="module" src="@carbon/web-components/es/components/button/index.js"></script>

<!-- Use the custom element -->
<cds-button>Primary Button</cds-button>
<cds-button kind="secondary">Secondary</cds-button>
```

### Shadow DOM Concern
Carbon Web Components use Shadow DOM encapsulation:
- Styles are scoped inside the component
- **Tailwind utility classes CANNOT penetrate Shadow DOM**
- This means: you'd need to use Carbon's own styling system
- Result: Two parallel CSS systems (Tailwind + Carbon)

### Accessibility
- IBM-grade accessibility compliance
- All components tested against WCAG 2.1 AA
- Screen reader tested (JAWS, NVDA, VoiceOver)
- Keyboard navigation fully implemented
- Regular accessibility audits by IBM's accessibility team
- Best-in-class for enterprise applications

### Theming
- Token-based design system
- Light and dark themes
- Custom themes via CSS custom properties
- BUT: designed around IBM's design language
- Not intended for arbitrary brand colors (e.g., franchise brands)
- Multi-brand would require significant token mapping work

### Why It's Not Recommended for This Project
1. Shadow DOM blocks Tailwind utility classes
2. Requires maintaining two CSS systems
3. Web Components may have issues with HTMX DOM swapping
4. Heavy JavaScript footprint for Web Components runtime
5. Theme system doesn't naturally support 5 arbitrary brand colors
6. Overkill for an internal governance tool
