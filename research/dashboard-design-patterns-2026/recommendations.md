# Project-Specific Recommendations

**For:** Azure Multi-Tenant Governance Platform
**Stack:** Python/FastAPI, Jinja2/HTMX, Tailwind CSS, Chart.js
**Users:** 10-30 IT power users
**Date:** March 27, 2026

---

## Priority Matrix

### 🔴 P0 — Implement Immediately (High Impact, Addresses Core UX Gaps)

#### R1: Add Global Tenant Filter/Selector to Dashboard Header
**Source Pattern**: Azure Portal (subscription selector), Vantage (workspace selector), Cloudflare (account selector), Datadog (template variables)

**Current State**: No tenant filtering on dashboard. All tenants always shown.

**Implementation**:
```html
<!-- Add to base.html header, after the page title -->
<div class="flex items-center gap-2">
  <label class="text-sm text-secondary-theme">Tenant:</label>
  <select hx-get="/dashboard"
          hx-target="#main-content"
          hx-push-url="true"
          name="tenant"
          class="text-sm border rounded px-2 py-1">
    <option value="all">All Tenants</option>
    {% for tenant in tenants %}
    <option value="{{ tenant.id }}" {{ 'selected' if selected_tenant == tenant.id }}>
      {{ tenant.name }}
    </option>
    {% endfor %}
  </select>
</div>
```

**Effort**: Low (1-2 days)
**Requires**: Backend filter parameter on all dashboard API endpoints

---

#### R2: Redesign KPI Summary Bar (4 Cards with Change Indicators)
**Source Pattern**: Azure Defender for Cloud (5 KPIs), Vantage (2 KPIs with % change), Azure Cost Analysis (Total + Average with % change)

**Current State**: 4 cards exist but lack change indicators, sparklines, and proper hierarchy.

**Target Design**:
```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Total Cost (30d)  │  │ Compliance Score  │  │ Active Alerts     │  │ Managed Resources │
│ $12,450.00        │  │ 87%              │  │ 12               │  │ 342              │
│ ↑ +3.2% vs prev  │  │ ↑ +2pts vs prev  │  │ 3 critical       │  │ 4 tenants        │
│ ─── sparkline ─── │  │ ████████░░ 87%   │  │ ● ● ● ○ ○ ○     │  │ A:120 B:89 C:82  │
└──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

**Implementation Notes**:
- Store previous period values in cache/DB for comparison
- Use `text-wm-green-100` for positive change, `text-wm-red-100` for negative
- Sparklines via Chart.js `type: 'line'` with `{responsive: true, scales: {x: {display: false}, y: {display: false}}}`
- Make each card clickable → navigates to the module page

**Effort**: Medium (3-5 days)
**Requires**: Previous period calculation in each summary service, Chart.js sparkline component

---

#### R3: Add Filter Chips to All List/Table Views
**Source Pattern**: Azure Defender for Cloud (filter chips with × dismiss + Add filter), Vantage (filter bar)

**Current State**: No filtering on compliance, identity, or resource tables.

**Implementation**:
```html
<!-- Filter chip bar component (reusable Jinja macro) -->
{% macro filter_chips(active_filters, base_url) %}
<div class="flex flex-wrap gap-2 items-center py-2">
  {% for filter in active_filters %}
  <span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm
               bg-brand-primary-5 text-brand-primary-100">
    {{ filter.label }} = {{ filter.value }}
    <button hx-get="{{ base_url }}?remove_filter={{ filter.key }}"
            hx-target="#content-area"
            class="hover:text-wm-red-100">×</button>
  </span>
  {% endfor %}
  <button class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm
                 border border-dashed text-secondary-theme hover:text-primary-theme"
          onclick="document.getElementById('filter-dropdown').classList.toggle('hidden')">
    + Add filter
  </button>
</div>
{% endmacro %}
```

**Effort**: Medium (3-4 days)
**Requires**: Backend query parameter support for each filter dimension, macro in Jinja

---

### 🟡 P1 — Implement Next Sprint (High Impact, Moderate Effort)

#### R4: Replace Compliance Percentage with Scorecard + Progress Bars
**Source Pattern**: Azure Policy (progress bars per initiative), GCP SCC (benchmark % per standard), NNg research (bars > gauges)

**Current State**: Simple percentage display.

**Target Design**:
```
Overall: [████████████████████░░░░░] 78%  ↑ +2pts

By Framework:
CIS Azure    [████████████████░░░░░░░░] 65%    Fail: 10/31
SOC 2        [██████████████████████░░] 89%    Fail: 4/36
HIPAA        [██████████████████████░░] 91%    Fail: 2/22

By Tenant:
Tenant A     [████████████████████░░░░░] 82%
Tenant B     [██████████████████░░░░░░░] 73%   ⚠ Below threshold
```

**Why bars over gauges**: NNg preattentive processing research (Laubheimer, 2017) confirms length comparison is processed more accurately than angle/area. Multiple progress bars in a vertical list enable instant cross-item comparison.

**Effort**: Medium (3-5 days)

---

#### R5: Implement Collapsible Sections with Lazy Loading
**Source Pattern**: Grafana (collapsible rows), Datadog (grouped widgets), Vantage (expandable details)

**Current State**: All dashboard sections always visible, always loaded.

**Implementation**:
```html
<!-- Lazy-loaded collapsible section -->
<details class="group" open>
  <summary class="flex items-center justify-between p-4 cursor-pointer
                   bg-surface-secondary rounded-lg hover:bg-surface-hover">
    <div class="flex items-center gap-2">
      <svg class="w-4 h-4 transition-transform group-open:rotate-90">...</svg>
      <h2 class="text-lg font-semibold text-primary-theme">Cost Overview</h2>
    </div>
    <span class="text-sm text-secondary-theme">Last synced: 5 min ago</span>
  </summary>
  <div class="mt-2"
       hx-get="/api/v1/dashboard/cost-section"
       hx-trigger="revealed"
       hx-swap="innerHTML">
    <div class="htmx-indicator p-4 text-center text-secondary-theme">Loading...</div>
  </div>
</details>
```

**Benefits**:
- Reduces initial page load (only visible sections load)
- Lets users control information density
- `hx-trigger="revealed"` loads content only when section is scrolled into view

**Effort**: Low-Medium (2-3 days)

---

#### R6: Implement Side Panel Detail View
**Source Pattern**: Azure Defender (alert detail side panel), Azure Portal (blade navigation)

**Current State**: Clicking items navigates to a full new page, losing list context.

**Implementation**:
```html
<!-- Side panel container (add to base.html) -->
<div id="detail-panel"
     class="fixed right-0 top-0 h-full w-[480px] bg-surface-primary shadow-2xl
            transform translate-x-full transition-transform duration-300 z-50
            overflow-y-auto"
     data-panel>
  <div class="sticky top-0 bg-surface-primary border-b p-4 flex justify-between">
    <h3 id="panel-title" class="font-semibold text-primary-theme"></h3>
    <button onclick="closePanel()" class="text-secondary-theme hover:text-primary-theme">×</button>
  </div>
  <div id="panel-content" class="p-4"></div>
</div>
<div id="panel-backdrop"
     class="fixed inset-0 bg-black/20 hidden z-40"
     onclick="closePanel()">
</div>

<!-- Table row that opens side panel -->
<tr hx-get="/api/v1/compliance/resource/{{ resource.id }}/panel"
    hx-target="#panel-content"
    hx-swap="innerHTML"
    hx-on::after-request="openPanel()"
    class="cursor-pointer hover:bg-surface-hover">
```

**Effort**: Medium (4-5 days)
**Requires**: Partial templates for panel content (separate from full page templates)

---

#### R7: Add Period-over-Period Change Badges to Cost Metrics
**Source Pattern**: Vantage (+12.78% badge), Azure Cost Analysis (% change next to total)

**Implementation**:
```html
{% macro change_badge(current, previous) %}
{% set change = ((current - previous) / previous * 100) if previous > 0 else 0 %}
{% if change > 0 %}
  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
               bg-wm-red-5 text-wm-red-100">↑ +{{ "%.1f"|format(change) }}%</span>
{% elif change < 0 %}
  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
               bg-wm-green-5 text-wm-green-100">↓ {{ "%.1f"|format(change) }}%</span>
{% else %}
  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
               bg-surface-secondary text-secondary-theme">— 0%</span>
{% endif %}
{% endmacro %}
```

**Note**: For costs, DOWN is green (good), UP is red (bad). For compliance, the reverse.

**Effort**: Low (1-2 days)
**Requires**: Previous period data stored in summary tables

---

### 🟢 P2 — Implement When Capacity Allows (Lower Urgency, Quality-of-Life)

#### R8: Sparklines in KPI Summary Cards
**Source Pattern**: Datadog (inline sparklines in Query Value widgets), Cloudflare (zone analytics)

**Implementation**: Chart.js line chart with all chrome stripped:
```javascript
new Chart(ctx, {
  type: 'line',
  data: { labels: last30days, datasets: [{ data: dailyCosts, borderColor: '#3B82F6', borderWidth: 1.5, fill: false, pointRadius: 0 }] },
  options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
    scales: { x: { display: false }, y: { display: false } } }
});
```

**Effort**: Medium (2-3 days per module)

---

#### R9: Last Synced Timestamps
**Source Pattern**: All platforms show data freshness indicators.

**Implementation**: Add to each dashboard section header:
```html
<span class="text-xs text-secondary-theme">
  Last synced: {{ sync_status.last_success | timeago }}
  {% if sync_status.is_stale %}
    <span class="text-wm-spark-100" title="Data may be outdated">⚠ stale</span>
  {% endif %}
</span>
```

**Effort**: Low (1 day)

---

#### R10: Bulk Operations on Governance Tables
**Source Pattern**: Azure Defender (checkbox → Change status of multiple alerts at once)

**Implementation**: HTMX-powered bulk selection:
```html
<!-- Select all checkbox -->
<input type="checkbox"
       onclick="document.querySelectorAll('.row-checkbox').forEach(cb => cb.checked = this.checked)">

<!-- Bulk action bar (appears when items selected) -->
<div id="bulk-actions" class="hidden sticky bottom-0 bg-surface-primary border-t p-3">
  <span class="text-sm font-medium" id="selected-count">0 selected</span>
  <button hx-post="/api/v1/compliance/bulk-acknowledge"
          hx-include=".row-checkbox:checked"
          class="btn-brand-secondary ml-4">Acknowledge</button>
  <button hx-post="/api/v1/compliance/bulk-suppress"
          hx-include=".row-checkbox:checked"
          class="btn-brand-secondary">Suppress</button>
</div>
```

**Effort**: Medium (3-4 days)

---

#### R11: Density Toggle (Comfortable / Compact / Dense)
**Source Pattern**: Datadog and Grafana panel density options, Microsoft Fluent UI DetailsList compact mode

**Implementation**: CSS custom property toggle + user preference cookie:
```css
[data-density="comfortable"] { --row-height: 48px; --cell-padding: 16px; --font-size: 14px; }
[data-density="compact"]     { --row-height: 36px; --cell-padding: 10px; --font-size: 13px; }
[data-density="dense"]       { --row-height: 28px; --cell-padding: 6px;  --font-size: 12px; }
```

Default to **compact** for our power user audience.

**Effort**: Low (1-2 days)

---

## Implementation Sequence

```
Sprint 1 (Week 1-2):
  R1: Tenant filter selector          [Low effort, High impact]
  R7: Change badges on cost metrics   [Low effort, Medium impact]
  R9: Last synced timestamps           [Low effort, Low-Med impact]

Sprint 2 (Week 3-4):
  R2: KPI summary bar redesign        [Medium effort, High impact]
  R3: Filter chips                     [Medium effort, High impact]
  R5: Collapsible sections + lazy load [Low-Med effort, Medium impact]

Sprint 3 (Week 5-6):
  R4: Compliance scorecard + bars      [Medium effort, Medium impact]
  R6: Side panel detail view           [Medium effort, High impact]

Sprint 4 (Week 7-8):
  R8: Sparklines                       [Medium effort, Low impact]
  R10: Bulk operations                 [Medium effort, Medium impact]
  R11: Density toggle                  [Low effort, Low impact]
```

---

## Mapping to Project Requirements

| Recommendation | Requirements Addressed |
|---------------|----------------------|
| R1: Tenant filter | RM-005 (Subscription/RG organization view), all cross-tenant requirements |
| R2: KPI summary bar | NF-P01 (Dashboard load < 3s), CO-002 (Cost trending), CM-006 (Secure Score) |
| R3: Filter chips | CM-007 (Non-compliant resource inventory), IG-002 (Privileged access) |
| R4: Compliance scorecard | CM-001 (Policy compliance), CM-006 (Secure Score), CM-008 (Trend reporting) |
| R5: Collapsible sections | NF-P01 (Dashboard load < 3s via lazy loading) |
| R6: Side panel | All detail-view requirements across modules |
| R7: Change badges | CO-002 (Cost trending), CO-003 (Cost anomaly detection) |
| R8: Sparklines | CO-002 (Cost trending), CM-008 (Compliance trend reporting) |
| R9: Last synced | NF-P04 (Data refresh intervals) |
| R10: Bulk operations | CM-005 (Automated remediation), IG-010 (Access review) |
| R11: Density toggle | NF-P01 (Performance), user preference support |
