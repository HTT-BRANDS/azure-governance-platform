# React-Only Libraries — Eliminated Options

## shadcn/ui
- **Site:** https://ui.shadcn.com
- **GitHub Stars:** 111k
- **Framework:** React only
- **Dependencies:** shadcn, class-variance-authority, clsx, tailwind-merge, lucide-react
- **Requires:** tsconfig.json, path aliases, React build pipeline
- **Supported Frameworks:** Next.js, Vite, Astro, React Router, TanStack Start, Laravel (with Inertia.js)
- **Concept:** "Not a component library — it's how you build your component library"
- **Distribution:** CLI copies component code into your project
- **Styling:** Tailwind CSS with CSS custom properties for theming
- **Accessibility:** Built on Radix Primitives (good ARIA support)
- **Verdict:** Excellent library, but fundamentally requires React. Cannot be used with Jinja2+HTMX.

## Radix Primitives
- **Site:** https://www.radix-ui.com/primitives
- **Made By:** WorkOS
- **Framework:** React only ("open source React primitives")
- **Concept:** Unstyled, accessible building blocks
- **Components:** Dialog, Dropdown Menu, Popover, Tooltip, Navigation Menu, Select, Tabs, etc.
- **Accessibility:** Excellent — purpose-built for accessibility
  - Full keyboard navigation
  - Focus management
  - Screen reader support
  - ARIA attributes automatically applied
- **Verdict:** Best accessibility of any library, but React-only. The ARIA patterns are worth studying as reference.

## Headless UI 2.1
- **Site:** https://headlessui.com/
- **Made By:** Tailwind Labs
- **Framework:** React and Vue only (visible as tabs on homepage)
- **Concept:** Completely unstyled, fully accessible UI components
- **Designed For:** Tailwind CSS integration
- **Components:** Menu (dropdown), Listbox (select), Combobox, Switch, Disclosure, Dialog, Popover, Radio Group, Tab, Transition
- **Accessibility:** Excellent — fully accessible out of box
- **Verdict:** Despite being from Tailwind Labs, requires React or Vue runtime. No vanilla JS or HTML-only option.

## Lessons Learned From These Libraries

Even though these libraries can't be used directly, their patterns inform best practices:

### From shadcn/ui
- CSS variable-based theming is the right approach (validates our design token system)
- Component composition via consistent interfaces
- The `cn()` utility pattern for conditional class names

### From Radix
- Every interactive component should manage its own focus
- Keyboard shortcuts should follow WAI-ARIA patterns
- Roving tabindex for grouped controls (radio groups, tabs)

### From Headless UI
- Transition components for enter/leave animations
- Render props pattern for maximum flexibility
- Search functionality in listboxes/comboboxes

These accessibility patterns can be implemented in vanilla JS/HTMX without adopting the libraries.
