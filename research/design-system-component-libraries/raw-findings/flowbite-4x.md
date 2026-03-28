# Flowbite 4.x — Raw Research Findings

**Version:** 4.0.1  
**GitHub:** https://github.com/themesberg/flowbite (9.2k ⭐, 851 forks)  
**License:** MIT  
**Last Release:** November 17, 2025

## Installation
```bash
npm i flowbite
```

## Key Characteristics
- Tailwind CSS utility-class components + vanilla JavaScript for interactive elements
- **Data attributes API** — `data-modal-target`, `data-dropdown-toggle`, etc.
- **JavaScript API** — Programmatic access to component behavior
- **No framework required** — works with vanilla HTML
- v4.0 added Tailwind CSS v4 support
- v4.0.1 added datepicker styles via themes and variables
- Flowbite Design System with variable tokens (announced as "New")

## Interactive Components Require JS
- Flowbite includes a JavaScript bundle for interactive components
- `initFlowbite()` initializes all data attribute listeners
- Alternative: Initialize individually with `initDropdowns()`, `initModals()`, etc.
- Supports ESM and CJS imports
- Can use bundled JavaScript via CDN

## Data Attributes Pattern
```html
<!-- Modal trigger -->
<button data-modal-target="default-modal" data-modal-toggle="default-modal">
  Toggle modal
</button>

<!-- Modal -->
<div id="default-modal" tabindex="-1" aria-hidden="true" class="hidden ...">
  <div class="...">
    <div class="...">
      <!-- Modal content -->
    </div>
  </div>
</div>
```

## HTMX Compatibility Concern
Both Flowbite and HTMX use data attributes for behavior:
- Flowbite: `data-modal-target`, `data-dropdown-toggle`
- HTMX: `hx-get`, `hx-post`, `hx-swap`

Potential issue: After HTMX swaps DOM content, Flowbite's event listeners
may not re-bind to new elements. Would need to call `initFlowbite()` after
HTMX swaps using `htmx.on('htmx:afterSwap', ...)`.

## Theming
- Limited built-in theming compared to DaisyUI
- Dark mode support via Tailwind's dark mode classes
- v4.0 introduced "Design System with variable tokens" but documentation is sparse
- No `data-theme` equivalent for multi-brand support
- Colors configured through Tailwind theme configuration

## Component Count
From documentation sidebar:
- Accordion, Alert, Avatar, Badge, Banner, Bottom Navigation
- Breadcrumb, Button, Button Group, Card, Carousel
- Charts (via ApexCharts integration)
- Clipboard, Datepicker, Device Mockups
- Drawer, Dropdown, Footer, Forms, Gallery
- Heading, HR, Images, Indicators, Input Field
- Jumbotron, KBD, Link, List, List Group
- Mega Menu, Modal, Navbar, Number Input
- Pagination, Paragraph, Popover, Progress
- Rating, Select, Sidebar, Skeleton, Speed Dial
- Spinner, Stepper, Table, Tabs, Textarea
- Timeline, Toast, Tooltip, Typography, Video

## Release History
- v4.0.1 — Nov 17, 2025: datepicker themes, component fixes
- v4.0.0 — Unknown date: Tailwind v4 support
- v3.1.2 — Feb 7, 2025: CSS variables refactoring
- v3.1.1 — Jan 31, 2025: CSS variables fix

## Integration Guides
Has official integration guides for:
- React, Next.js, Vue, Nuxt, Svelte
- Generic JavaScript / TypeScript
- (No Jinja2 or HTMX guide, but vanilla JS guide applies)
