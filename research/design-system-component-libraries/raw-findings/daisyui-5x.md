# DaisyUI 5.x — Raw Research Findings

**Version:** 5.5.19  
**GitHub:** https://github.com/saadeghi/daisyui (40.6k ⭐)  
**License:** MIT  
**Last Updated:** March 25, 2026 (2 days ago at time of research)

## Installation (Tailwind v4)
```css
@import "tailwindcss";
@plugin "daisyui";
```

```bash
npm i -D daisyui@latest
```

## Key Characteristics
- **CSS-only** — No JavaScript runtime required
- **Semantic classes** — `btn`, `card`, `badge` instead of utility strings
- **Tailwind v4 native** — Uses `@plugin` directive
- **35 built-in themes** + custom theme support
- **data-theme attribute** — Per-element theme scoping
- **CDN option** available for quick prototyping
- **Figma integration** available
- **MCP Server** integration available (for AI tools)

## Custom Theme System
```css
@plugin "daisyui/theme" {
  name: "mytheme";
  default: true;
  prefersdark: false;
  color-scheme: light;

  --color-base-100: oklch(98% 0.02 240);
  --color-base-200: oklch(95% 0.03 240);
  --color-base-300: oklch(92% 0.04 240);
  --color-base-content: oklch(20% 0.05 240);
  --color-primary: oklch(55% 0.3 240);
  --color-primary-content: oklch(98% 0.01 240);
  --color-secondary: oklch(70% 0.25 200);
  --color-accent: oklch(75% 0.15 60);
  --color-success: ...;
  --color-warning: ...;
  --color-error: ...;
  --color-info: ...;
}
```

## Theme Scoping
```html
<!-- Global theme -->
<html data-theme="dark">
  <!-- Override for specific section -->
  <div data-theme="light">This div will always use light theme</div>
  <span data-theme="retro">This span will always use retro theme!</span>
</html>
```

## CDN Theme Override
```css
:root:has(input.theme-controller[value=mytheme]:checked),
[data-theme="mytheme"] {
  color-scheme: light;
  --color-base-100: oklch(98% 0.02 240);
  /* ... */
}
```

## Component Count (from sidebar navigation)
### Actions
- Button, Dropdown, FAB/Speed Dial (new), Modal, Swap, Theme Controller

### Data Display
- Accordion, Avatar, Badge, Card, Carousel, Chat bubble, Collapse,
  Countdown (updated), Diff, Kbd, List, Loading, Radial progress,
  Skeleton, Stat, Table, Timeline, Toast, Tooltip, Tree

### Navigation
- Bottom navigation, Breadcrumbs, Dock, Link, Menu, Navbar, Pagination, Steps, Tab

### Feedback
- Alert, Progress, Rating

### Data Input
- Checkbox, Color picker, File input, Input, Radio, Range, Rating,
  Select, Textarea, Toggle

### Layout
- Artboard, Divider, Drawer, Footer, Hero, Indicator, Join, Mask, Stack

## Accessibility Approach
- **Modal**: Recommends HTML `<dialog>` element (Method 1, labeled "recommended")
  - "It is accessible and we can close the modal using Esc key"
  - Uses `ID.showModal()` and `ID.close()` methods
- **Buttons**: Semantic `<button>` elements with class styling
- **No automatic ARIA attributes** — developer responsibility
- **Focus indicators**: Inherits Tailwind's `:focus-visible` styles
- **Color contrast**: Built-in themes designed for contrast compliance

## Multi-Brand Mapping for This Project
| Brand | DaisyUI `data-theme` | Primary | Accent |
|-------|---------------------|---------|--------|
| httbrands | "httbrands" | #500711 | #FFC957 |
| frenchies | "frenchies" | #2563eb | #FFC957 |
| bishops | "bishops" | #c2410c | #FFC957 |
| lashlounge | "lashlounge" | #7c3aed | #FFC957 |
| deltacrown | "deltacrown" | #004538 | #FFC957 |
