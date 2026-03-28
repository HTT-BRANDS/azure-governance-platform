# Project-Specific Recommendations

**Research Date:** March 27, 2026  
**Project:** Azure Governance Platform  
**Stack:** Python/FastAPI + Jinja2 + HTMX + Tailwind CSS v4.2 + 5 brand themes

---

## Priority 1: Integrate DaisyUI 5.x (Recommended — 2-3 days)

### Why This Is the Best Fit

1. **Zero architecture change** — Your existing stack stays intact
2. **CSS-only** — No JavaScript conflicts with HTMX
3. **Semantic classes** — `btn` instead of `inline-block cursor-pointer rounded-md bg-gray-800 px-4 py-3...`
4. **`data-theme` ≈ `data-brand`** — Architecturally identical to your existing approach
5. **Free, MIT licensed, 40.6k stars** — Low adoption risk

### Implementation Steps

#### Step 1: Install DaisyUI (5 minutes)

```bash
npm i -D daisyui@latest
```

#### Step 2: Add plugin to theme.src.css

```css
@import "tailwindcss";
@plugin "daisyui";
```

#### Step 3: Create brand themes as DaisyUI custom themes

In `theme.src.css`, add one theme per brand:

```css
@plugin "daisyui/theme" {
  name: "httbrands";
  default: true;
  color-scheme: light;
  --color-primary: oklch(from #500711 l c h);
  --color-primary-content: oklch(from #FFFFFF l c h);
  --color-secondary: oklch(from #BB86FC l c h);
  --color-accent: oklch(from #FFC957 l c h);
  --color-base-100: oklch(from #FFFFFF l c h);
  --color-base-content: oklch(from #111827 l c h);
  --color-success: oklch(from #10B981 l c h);
  --color-warning: oklch(from #F59E0B l c h);
  --color-error: oklch(from #EF4444 l c h);
  --color-info: oklch(from #3B82F6 l c h);
  --rounded-btn: 8px;
}

@plugin "daisyui/theme" {
  name: "frenchies";
  color-scheme: light;
  --color-primary: oklch(from #2563eb l c h);
  --color-primary-content: oklch(from #FFFFFF l c h);
  --color-accent: oklch(from #FFC957 l c h);
  --color-base-100: oklch(from #FFFFFF l c h);
  --color-base-content: oklch(from #111827 l c h);
  --rounded-btn: 8px;
}

/* ... repeat for bishops, lashlounge, deltacrown */
```

#### Step 4: Map data-brand to data-theme

Option A — In `base.html`, add both attributes:
```html
<html data-brand="{{ brand_key }}" data-theme="{{ brand_key }}">
```

Option B — Generate DaisyUI-compatible CSS in `css_generator.py`:
```python
def generate_daisyui_theme_override(brand_key: str, brand: BrandConfig) -> str:
    """Generate [data-theme='brand'] CSS block with DaisyUI variable mappings."""
    # Map brand colors to DaisyUI's expected variable names
    ...
```

#### Step 5: Gradually replace custom component CSS

Before (custom):
```html
<button class="btn-brand px-4 py-2 text-sm font-medium">Save</button>
```

After (DaisyUI):
```html
<button class="btn btn-primary btn-sm">Save</button>
```

The existing `btn-brand` classes can coexist with DaisyUI's `btn` classes during migration.

#### Step 6: Update Jinja2 macros

```jinja2
{# Before #}
{% macro brand_button(text, variant="primary", size="md") %}
<button class="btn-brand {{ size_classes[size] }} inline-flex items-center gap-2">
  {{ text }}
</button>
{% endmacro %}

{# After — using DaisyUI classes #}
{% macro brand_button(text, variant="primary", size="md") %}
{% set size_map = {"sm": "btn-sm", "md": "", "lg": "btn-lg"} %}
{% set variant_map = {
  "primary": "btn-primary",
  "secondary": "btn-secondary",
  "accent": "btn-accent",
  "ghost": "btn-ghost",
  "danger": "btn-error"
} %}
<button class="btn {{ variant_map[variant] }} {{ size_map[size] }}">
  {{ text }}
</button>
{% endmacro %}
```

### What You Keep

- `config/brands.yaml` — Brand definitions (unchanged)
- `app/core/design_tokens.py` — Pydantic validation (unchanged)
- `app/core/color_utils.py` — WCAG color math (unchanged)
- `app/core/css_generator.py` — May need minor updates to generate DaisyUI-compatible variables
- `app/core/theme_middleware.py` — Unchanged (adds `data-theme` alongside `data-brand`)
- All ARIA attributes in Jinja2 macros — **Keep these, DaisyUI doesn't provide them**

### What You Can Remove (after migration)

- `app/static/css/theme.src.css` component section (~100 lines): `.btn-brand`, `.card-brand`, `.badge-brand`, `.progress-brand`, `.nav-brand`
- These are replaced by DaisyUI's `btn`, `card`, `badge`, `progress`, `navbar`

### DaisyUI Component Mapping

| Your Component | Your CSS Class | DaisyUI Class | Notes |
|---------------|---------------|---------------|-------|
| Button | `btn-brand` | `btn btn-primary` | Add `btn-sm`, `btn-lg` for sizes |
| Secondary Button | `btn-brand-secondary` | `btn btn-secondary` | Or `btn btn-outline` |
| Card | `card-brand` | `card bg-base-100 shadow` | Add `card-body` for content |
| Badge | `badge-brand` | `badge badge-primary` | Variants: `badge-success`, etc. |
| Progress | `progress-brand` | `progress progress-primary` | Set `value` and `max` attrs |
| Nav | `nav-brand` | `navbar bg-primary` | Extensive nav component |
| Modal | N/A | `modal` + `<dialog>` | Native HTML dialog |
| Alert | N/A | `alert alert-success` | New component available |
| Tooltip | N/A | `tooltip` | New component available |
| Accordion | N/A | `collapse` | New component available |
| Tabs | N/A | `tabs` | New component available |
| Skeleton | N/A | `skeleton` | New component available |

---

## Priority 2: Purchase Tailwind Plus for Reference ($299)

### Why
- Professional HTML component patterns for governance dashboards
- Data tables, stat cards, navigation patterns
- Copy into Jinja2 macros, replace colors with CSS variables
- One-time cost, permanent access

### How to Use
1. Purchase personal license ($299)
2. Browse UI Blocks → select "HTML" view
3. Copy patterns into Jinja2 macros
4. Replace hardcoded Tailwind color classes with brand variable classes
5. Add ARIA attributes and HTMX integration

### Best Value Components for This Project
- **Application UI → Stats / KPI Cards** — Dashboard metric cards
- **Application UI → Tables** — Data tables for compliance, resources
- **Application UI → Navigation** — Sidebar, breadcrumbs
- **Application UI → Alerts** — Status notifications
- **Application UI → Forms** — Input groups, select menus
- **Application UI → Page Headings** — Dashboard headers

---

## Priority 3: Enhance Existing Accessibility (Ongoing)

### Your Current Strengths
Your Jinja2 macros already include:
- `role="region"`, `role="progressbar"`, `role="status"`, `role="alert"`
- `aria-label`, `aria-disabled`, `aria-current="page"`
- `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- `aria-hidden="true"` on decorative icons
- WCAG AA color contrast validation in `color_utils.py`

### Gaps to Address (from WCAG 2.2)
1. **Focus Not Obscured (2.4.11)**: Ensure sticky headers/sidebars don't cover focused elements
2. **Target Size (2.5.8)**: Ensure all interactive elements are at least 24×24px
3. **Dragging Movements (2.5.7)**: If any drag interactions exist, provide click alternatives
4. **Consistent Help (3.2.6)**: Help links should be in consistent locations

### DaisyUI Accessibility Additions
After integrating DaisyUI, add these ARIA attributes to the macros (DaisyUI doesn't include them):

```jinja2
{# DaisyUI modal with full accessibility #}
{% macro accessible_modal(id, title) %}
<dialog id="{{ id }}" class="modal" aria-labelledby="{{ id }}-title" role="dialog">
  <div class="modal-box">
    <h3 id="{{ id }}-title" class="text-lg font-bold">{{ title }}</h3>
    {{ caller() }}
    <div class="modal-action">
      <form method="dialog">
        <button class="btn">Close</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
{% endmacro %}
```

---

## Anti-Recommendations (Do NOT Do These)

### ❌ Do NOT migrate to React/Next.js for component libraries
- **Cost**: 3-6 months of engineering time
- **Risk**: Fundamental architecture change
- **Impact**: Breaks HTMX integration, requires rewriting all templates
- **Gain**: Access to shadcn/ui, Radix, Headless UI — nice but not worth it

### ❌ Do NOT adopt Carbon Design System Web Components
- **Cost**: 2-4 weeks minimum
- **Risk**: Shadow DOM conflicts with Tailwind, dual CSS systems
- **Complexity**: Significant learning curve, different mental model
- **Gain**: Better accessibility — but your existing system is already good

### ❌ Do NOT replace your custom token system with a library's theming
- Your `css_generator.py` + `design_tokens.py` + `color_utils.py` system is:
  - Pydantic-validated (type-safe, injection-proof)
  - WCAG-validated (contrast ratios checked)
  - Server-generated (no client-side overhead)
  - Brand-scoped (per-tenant isolation)
- This is MORE robust than any library's theming system

### ❌ Do NOT over-consolidate CSS custom properties
- 47+ properties × 5 brands = 235 total is FINE
- They're generated, not hand-maintained
- They're cached (O(1) after first request)
- CSS custom properties are optimized by browsers
- The "47 is too many" instinct is wrong — it's a strength

---

## Decision Summary

| Question | Answer |
|----------|--------|
| Keep custom design system? | **Yes — it's a competitive advantage** |
| Add a component library? | **Yes — DaisyUI 5.x as a plugin** |
| Buy Tailwind Plus? | **Optional but valuable at $299** |
| Migrate to React? | **Absolutely not** |
| 47 CSS vars × 5 brands OK? | **Yes — it's fine and well-architected** |
| What about WCAG 2.2? | **Already mostly compliant, address the 4 gaps listed above** |
| Flowbite or DaisyUI? | **DaisyUI — better theming, no JS conflicts, 4x more popular** |
