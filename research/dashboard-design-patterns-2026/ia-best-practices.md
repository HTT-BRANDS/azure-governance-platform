# Dashboard Information Architecture Best Practices

**Research Date:** March 27, 2026
**Context:** Azure Multi-Tenant Governance Platform (HTMX/Tailwind, 10-30 power users)

---

## 1. KPI Cards / Summary Cards

### How Many is Optimal?

**Recommendation: 4 KPI cards for the main dashboard, 2-3 per module page.**

| Platform | KPI Count (Main Dashboard) | Above the Fold? |
|----------|--------------------------|-----------------|
| Azure Defender for Cloud | 5 (Subscriptions, AWS accounts, GCP projects, Recommendations, Alerts) | Yes |
| Azure Cost Analysis | 2 (Total cost, Average cost) | Yes |
| Vantage.sh | 2 (Accrued Costs, Forecasted Costs) | Yes |
| Datadog | Variable (Query Value widgets) | Configurable |
| Grafana | Variable (Stat panels) | Configurable |
| CloudHealth | 4 (Cost, Savings, Compliance, Resources) | Yes |

**Evidence-Based Guidelines:**
- **Miller's Law** (7±2 items in working memory): 4-5 KPI cards sit well within cognitive limits
- **Azure's pattern**: 4-5 across the top for cross-domain overview, 2 for domain-specific pages
- **Vantage's pattern**: 2 KPIs per report (Accrued + Forecasted) with % change badges
- **NNg principle**: "Make important information visually salient" — KPI cards serve as the primary attention anchor

**Recommended KPI Card Anatomy (based on Azure + Vantage patterns):**
```
┌─────────────────────────────┐
│ Label (secondary text)      │
│ $12,450.00   ↑ +3.2%       │  ← Big number + change badge
│ vs. previous period         │  ← Context line
│ ───────── (sparkline)       │  ← Optional inline trend
└─────────────────────────────┘
```

**Our Dashboard — Recommended 4 KPIs:**
1. **Total Cost (30d)** — with % change from previous 30d period
2. **Compliance Score** — aggregated across tenants, with change indicator
3. **Active Alerts** — count with severity breakdown (e.g., "12 alerts · 3 critical")
4. **Managed Resources** — total count with tenant breakdown on hover

### What Metrics Should Be Above the Fold?

Based on cross-platform analysis, **above the fold** means:
- KPI summary cards (always)
- Tenant/time range filter controls (always)
- The FIRST section of the most critical module (usually compliance or alerts)

**Below the fold** (scrollable):
- Detailed charts and breakdowns
- Data tables
- Secondary modules

---

## 2. Compliance Gauge Visualization

### Radial Gauges vs. Progress Bars vs. Scorecards

**Recommendation: Use progress bars for multi-framework comparison. Use a single radial gauge ONLY for the hero compliance score.**

#### NNg Research Evidence (Preattentive Processing)

From "Dashboards: Making Charts and Graphs Easier to Understand" (Laubheimer, 2017):
- **Length** is the most accurate preattentive attribute for quantitative comparison
- **Angle** (used in radial gauges/pie charts) is harder to judge accurately
- **Area** comparison is even less accurate
- **Color** should indicate categories, not magnitude

#### Platform Patterns

| Platform | Compliance Visualization | Type |
|----------|------------------------|------|
| Azure Defender | Single donut for Secure Score (60%) + horizontal bars per control | Hybrid |
| Azure Policy | Compliance % per initiative + stacked bar (compliant/non-compliant/exempt) | Progress bars |
| GCP SCC | Benchmark % per standard + severity distribution bars | Progress bars |
| AWS Control Tower | Count-based (compliant/non-compliant controls per OU) | Scorecard |

#### Recommendation for Our Platform

```
COMPLIANCE OVERVIEW
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Overall Score: [████████████████████░░░░░] 78%  ↑ +2%     │  ← Hero metric (progress bar, not gauge)
│                                                             │
│  By Framework:                                              │
│  CIS Azure    [████████████████░░░░░░░░] 65%    2/31 fail  │  ← Per-framework bars
│  SOC 2        [██████████████████████░░] 89%    4/36 fail  │
│  NIST 800-53  [█████████████████░░░░░░░] 72%    8/29 fail  │
│  HIPAA        [██████████████████████░░] 91%    2/22 fail  │
│                                                             │
│  By Tenant:                                                 │
│  Tenant A     [████████████████████░░░░░] 82%              │  ← Per-tenant bars
│  Tenant B     [██████████████████░░░░░░░] 73%              │
│  Tenant C     [████████████████████████░] 95%              │
│  Tenant D     [████████████░░░░░░░░░░░░] 58%   ⚠ ALERT   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Why NOT radial gauges for multi-item comparison:**
- Radial gauges consume more horizontal space per item
- Length comparison (bars) is processed more accurately than angle (gauges)
- Progress bars align naturally in a vertical list, enabling instant comparison
- Radial gauges work for ONE hero metric only (and even then, a large number + bar is equally effective)

---

## 3. Data Table Design for Governance

### NNg Four Major User Tasks (Laubheimer, 2022)

Tables must support these four tasks:

1. **Find records that fit specific criteria**
   - Sorting by column
   - Filtering by value (filter chips, search)
   - Column-specific filters (dropdown in column header)

2. **Compare data across records**
   - Consistent column alignment
   - Zebra striping or row hover highlight
   - Sticky headers for scrolling
   - Conditional formatting (red/yellow/green cells)

3. **View/edit/add a single row's data**
   - Expandable rows for detail
   - Side panel for full record view
   - Inline editing for status changes

4. **Take actions on records**
   - Checkbox selection for bulk operations
   - Row-level action buttons (visible on hover or always visible)
   - Bulk action bar that appears when items are selected

### Governance Table Pattern (synthesized from Azure, Vantage, Defender)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [Filter] [Severity ▾] [Tenant ▾] [Status ▾]  ⌕ Search    [Export]  │  ← Filter bar
├──────────────────────────────────────────────────────────────────────┤
│ ☐ │ Severity │ Resource          │ Policy        │ Tenant │ Status  │  ← Sortable headers
├───┼──────────┼───────────────────┼───────────────┼────────┼─────────┤
│ ☐ │ 🔴 High  │ vm-prod-01        │ Disk encrypt  │ A      │ Open    │  ← Rows with severity icons
│ ☐ │ 🟡 Med   │ storage-backup-02 │ HTTPS only    │ B      │ Open    │
│ ☐ │ 🟢 Low   │ vnet-dev-03       │ NSG rules     │ A      │ Ack'd   │
├──────────────────────────────────────────────────────────────────────┤
│ ■ 2 selected  [Change Status ▾] [Assign ▾] [Suppress] [Export]     │  ← Bulk action bar
└──────────────────────────────────────────────────────────────────────┘
```

### Key Implementation Details

**Inline Actions (hover-revealed):**
- Azure pattern: Actions appear as icon buttons on row hover
- Vantage pattern: "..." overflow menu per row
- **Recommendation**: Show primary action (View Details) always as a link; secondary actions on hover or in overflow

**Expandable Rows:**
- Azure Resource Graph: Click row → side panel with full details
- Grafana: Click row → drill-down to new dashboard
- **Recommendation**: Use HTMX `hx-get` to load detail panel inline or as side drawer

**Bulk Operations:**
- Azure Defender: Checkbox selection → "Change status of multiple alerts at once"
- **Recommendation**: Essential for compliance remediation workflows (acknowledge, dismiss, assign multiple items)

**Conditional Formatting:**
- Vantage: % change in green (decrease) or red (increase) for costs
- Azure: Severity badges (Critical=red, High=orange, Medium=yellow, Low=blue)
- **Recommendation**: Use semantic color tokens from design system (wm-red, wm-green, wm-spark)

---

## 4. Alert Triage Patterns

### Microsoft Defender for Cloud — Gold Standard Pattern

**Alert List View:**
1. **Summary bar**: Total active alerts count + affected resources count
2. **Severity distribution**: Horizontal stacked bar showing High/Medium/Low proportions
3. **Filter chips**: Removable filter badges (Severity, Status, Time, Resource type) with `+ Add filter`
4. **Sortable table**: Checkbox, Severity icon, Alert title, Affected resource, Time
5. **Grouping**: Optional "Group by" dropdown (None, Severity, Resource, Alert type)

**Alert Detail (Side Panel):**
1. **Header**: Alert title, Severity badge, Status dropdown, Time
2. **Tabs**: "Alert details" | "Take action"
3. **Alert details tab**: Description, Affected resources, MITRE ATT&CK tactics, Evidence
4. **Take action tab** (accordion sections):
   - **Inspect resource context** → Link to activity logs
   - **Mitigate the threat** → Step-by-step remediation
   - **Prevent future attacks** → Related recommendations
   - **Trigger automated response** → Logic App integration
   - **Suppress similar alerts** → Create suppression rule

### Alert Severity Model

| Level | Color | Badge | Use Case |
|-------|-------|-------|----------|
| Critical | Red (wm-red-100) | 🔴 | Immediate action required (security breach, budget exceeded 200%) |
| High | Orange (wm-spark-100) | 🟠 | Action within 24h (compliance drift, budget exceeded 100%) |
| Medium | Yellow | 🟡 | Action within 1 week (idle resources, stale accounts) |
| Low | Blue (wm-blue-100) | 🔵 | Informational (optimization suggestions, upcoming renewals) |

### Alert Lifecycle States

```
New → Acknowledged → In Progress → Resolved
  ↓                                    ↓
  └→ Suppressed                        └→ Auto-closed (after TTL)
```

### Auto-Dismiss/Acknowledgment Patterns

- **Auto-resolve**: Alert auto-closes when the underlying condition is remediated (e.g., disk encrypted)
- **Acknowledgment**: User marks alert as "seen" without resolving (reduces noise but preserves record)
- **Suppression rules**: "Don't alert me again for [resource type] + [policy] + [tenant]" (with expiration)
- **Snooze**: Temporarily hide alert for N hours/days (re-appears if still active)

### Recommendation for Our Platform

```
ALERT TRIAGE FLOW

1. Dashboard KPI shows: "12 alerts · 3 critical"  [Click to view]
                              ↓
2. Alert list page with:
   - Filter chips: [Critical ×] [Last 7d ×] [Tenant A ×] [+ Add filter]
   - Grouped by severity (Critical section expanded, others collapsed)
   - Bulk select checkboxes
                              ↓
3. Click alert → Side panel with:
   - Tab 1: Details (resource, policy, evidence, timestamp)
   - Tab 2: Actions (remediate, suppress, assign)
   - "View Full Details" link to dedicated page
                              ↓
4. Bulk actions: Select multiple → Change Status / Assign / Suppress
```

---

## 5. Drill-Down Navigation Patterns

### Pattern Comparison

| Pattern | Description | Pros | Cons | Used By |
|---------|-------------|------|------|---------|
| **Hub-and-spoke** | Central dashboard links to detail pages, back button returns | Simple mental model, clean URLs | Loses dashboard context, extra page loads | AWS Control Tower |
| **Progressive disclosure** | Content reveals in-place (expandable rows, collapsible sections) | No page navigation, fast, maintains context | Can get cluttered, limited space | Grafana rows, Vantage tables |
| **Side panel (master-detail)** | Click item → detail panel slides in from right | Maintains list context, fast preview | Limited panel width, complex layout | Azure Defender, Azure Portal blades |
| **Breadcrumb drill-down** | Navigate deeper into hierarchy, breadcrumb shows path | Clear hierarchy, deep nesting | Long breadcrumbs, context loss | Azure Portal (management groups → subscriptions → resources) |
| **Tab-based sections** | Organize views into tabs within same page | Quick switching, flat hierarchy | Limited to 5-7 tabs, no nesting | Datadog, Vantage (Overview/Anomalies) |

### Recommendation: Hybrid Approach

For our governance platform, use a **3-layer hybrid approach**:

```
Layer 1: HTMX Tab Sections (Progressive Disclosure)
├── Dashboard page with collapsible module sections
├── Each section loads via hx-get on first view (lazy loading)
└── Sections: Cost | Compliance | Identity | Resources

Layer 2: Side Panel Detail (Master-Detail)
├── Click any item in a table → side panel slides in from right
├── Panel shows key details + actions
├── "View Full Details" link for complete page
└── Implementable with HTMX hx-get + CSS transition

Layer 3: Dedicated Detail Pages (Hub-and-Spoke)
├── Full resource/policy/user detail page
├── Breadcrumb: Dashboard > Compliance > Policy Name > Resource
├── All context and actions available
└── Back button returns to list position
```

**HTMX Implementation Pattern:**
```html
<!-- Collapsible section with lazy load -->
<details hx-trigger="toggle once" hx-get="/api/v1/compliance/summary" hx-target="#compliance-content">
  <summary>Compliance Overview</summary>
  <div id="compliance-content">
    <div class="htmx-indicator">Loading...</div>
  </div>
</details>

<!-- Side panel trigger -->
<tr hx-get="/api/v1/alerts/{{ alert.id }}/detail"
    hx-target="#detail-panel"
    hx-swap="innerHTML"
    class="cursor-pointer hover:bg-surface-hover">
  ...
</tr>

<!-- Side panel container -->
<div id="detail-panel"
     class="fixed right-0 top-0 h-full w-96 bg-surface-primary shadow-lg transform translate-x-full transition-transform"
     :class="{ 'translate-x-0': open }">
</div>
```

---

## 6. Data Density for Power Users

### NNg Research: Complex Application Design (Kaplan, 2020)

**8 Design Guidelines for Complex Applications**, applied to our context:

| # | Guideline | Application to Our Platform |
|---|-----------|----------------------------|
| 1 | Support users' preference to learn by doing | Provide data immediately, not behind onboarding wizards |
| 2 | Help users adopt more efficient methods | Show keyboard shortcuts, offer saved views |
| 3 | Provide flexible and fluid pathways | Multiple routes to same data (dashboard card → detail page, or sidebar nav → detail page) |
| 4 | Help users track actions and thought processes | Show "last viewed" alerts, recent searches, activity log |
| 5 | Coordinate transitions among tools | Maintain context when switching between modules (cost → compliance → identity) |
| 6 | **Reduce clutter without reducing capability** | Use progressive disclosure, collapsible sections, density toggles |
| 7 | **Ease transition between primary and secondary info** | Hover tooltips on charts, expandable table rows, side panels |
| 8 | **Make important information visually salient** | Severity color coding, anomaly badges, alert count in nav |

### Optimal Data Density Balance

**Key Principle**: Internal tools for 10-30 power users should NOT follow consumer app minimalism. Power users:
- Check the dashboard multiple times per day
- Know the domain vocabulary (no need to explain "compliance score")
- Want to see trends and anomalies at a glance
- Prefer fewer clicks over cleaner aesthetics

**Evidence-based density guidelines:**

1. **Summary Cards**: Show the number + change + sparkline (3 data points per card, not just 1)
2. **Tables**: Default to 15-25 rows visible (not 5-10 like consumer apps)
3. **Charts**: Include gridlines and axis labels (power users need exact values, not just shapes)
4. **Navigation**: Persistent sidebar with counts/badges (e.g., "Alerts (12)", "Non-compliant (47)")
5. **Whitespace**: Reduce padding compared to consumer apps, but maintain clear section separation

**Density Toggle Pattern** (from Datadog/Grafana):
```
┌─────────────────────────────────────────┐
│  View: [Comfortable] [Compact] [Dense]  │  ← User preference saved
└─────────────────────────────────────────┘

Comfortable: 16px row height, 24px padding, larger text
Compact:     12px row height, 16px padding, standard text  ← DEFAULT for our app
Dense:       10px row height, 8px padding, smaller text
```

### NNg on Operational vs Analytical Dashboards (Laubheimer, 2017)

Our platform is a **hybrid operational-analytical dashboard**:

| Aspect | Operational | Analytical | Our Platform |
|--------|------------|-----------|-------------|
| Update frequency | Real-time | Daily/weekly | 15min-24h (scheduled sync) |
| Primary task | Monitor + act | Analyze + decide | Both |
| Data density | High (status board) | Medium (charts) | High (power users) |
| Time sensitivity | Immediate | Days/weeks | Mixed (alerts = immediate, costs = weekly) |

**Implication**: Default to high density for monitoring panels (alerts, compliance), medium density for analytical panels (cost trends, resource inventory).

### Preattentive Processing for Governance Data

From NNg (Laubheimer, 2017), the preattentive attributes ranked by accuracy for quantitative comparison:

1. **2D position** (most accurate) → Use for chart data points
2. **Length** → Use for progress bars, bar charts
3. **Angle** (less accurate) → Avoid for multi-item comparison (pie charts, radial gauges)
4. **Area** (least accurate) → Avoid for quantitative comparison

**Color guidelines:**
- Use for **categorical distinction** (compliant=green, non-compliant=red, exempt=gray)
- Do NOT use color gradients for quantitative ranges (use bar length instead)
- Always pair color with a secondary indicator (icon, text label) for colorblind accessibility
- 4.5% of general population has color blindness (8% of men)
