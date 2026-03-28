# Multi-Platform Dashboard Design Analysis

**Last Updated:** March 27, 2026

---

## 1. Azure Portal Governance UX

### Information Architecture
Azure Portal uses a **blade-based navigation** pattern where each governance feature opens as a blade (sliding panel) from right to left. The hierarchy is:

```
Management Groups → Subscriptions → Resource Groups → Resources
         ↓                ↓                ↓              ↓
    Policy view      Cost view      Compliance view    Detail view
```

### Compliance Dashboard Patterns
- **Azure Policy Compliance**: Aggregated view → drill down to per-resource, per-policy granularity
- **Policy definitions** group into **policy initiatives (policySets)** → assigned at any scope
- Evaluation states: Compliant, Non-Compliant, Exempt, Unknown
- Resources are auto-evaluated on creation/update, policy assignment changes, and on a 24-hour cycle

### Secure Score Model (Defender for Cloud)
Azure's governance score uses a **3-step weighted model**:
1. **Calculate asset score** — Based on number and risk level of open recommendations, factoring in issue severity and asset risk factors
2. **Multiply by asset criticality** — Measure of resource importance within the organization
3. **Aggregate** — Final Secure Score = aggregation of asset scores × criticality weights

**Key UX Pattern**: The score is presented as a single percentage at the top, with a breakdown into security control categories below, each with their own sub-score and list of recommendations.

Two Secure Score models exist (as of 2026):
- **Cloud Secure Score (risk-based)** — New model, recommended
- **Classic Secure Score** — Legacy model

### Cost Management UX
- **Cost Analysis blade**: Area chart with daily/weekly/monthly granularity
- **Forecast line**: Dotted line showing projected spend
- **Comparison**: Side-by-side with previous period (not overlaid)
- **Grouping**: By subscription, resource group, resource type, tag
- **Budget alerts**: Visual threshold lines on charts

### Dashboard Widget System
Azure Portal dashboards use a **tile-based grid** system:
- Tiles can be resized (1×1 to 6×4 grid units)
- **Tile Gallery** provides pre-built tile types: Metrics chart, Resource groups, All resources, Markdown, Clock, etc.
- Custom tiles from pinned views (pin any blade element to dashboard)
- Shared dashboards via Azure RBAC

### Key Takeaway for Our Project
Azure's blade navigation is proprietary UI, but the **information hierarchy pattern** (aggregated score → category breakdown → per-item detail) and **weighted score model** are directly applicable.

---

## 2. AWS Console — Organizations + Control Tower

### Dashboard Pattern
AWS Control Tower dashboard offers **continuous oversight** of the landing zone, displaying:
- **Provisioned accounts** across the enterprise
- **Controls enabled** for policy enforcement
- **Controls for continuous detection** of policy non-conformance
- **Noncompliant resources** organized by accounts and OUs (Organizational Units)

### Governance Model
- **Guardrails** (controls): Mandatory, Strongly Recommended, or Elective
- **Drift detection**: Automatic identification of configuration divergence from best practices
- **Landing zone**: Pre-configured multi-account environment with guardrails applied
- **Account Factory**: Configurable template for standardized account provisioning

### Information Hierarchy
```
Organization
  └── Organizational Units (OUs)
       └── Accounts
            └── Regions
                 └── Resources → Controls → Compliance Status
```

### Dashboard Metrics
The Control Tower dashboard shows:
1. **Account summary**: Total accounts, enrolled vs. unenrolled
2. **Control compliance**: Enabled controls, compliant vs. non-compliant
3. **Drift status**: Resources that have drifted from governance baselines
4. **OU compliance**: Per-OU compliance breakdown

### Key Takeaway for Our Project
AWS's **OU-based grouping** maps well to our multi-tenant model. Their distinction between "drift" (configuration changed) and "non-compliance" (never met) is a useful UX pattern for our compliance page.

---

## 3. GCP Console — Organization Policy + Security Command Center

### Organization Policy Dashboard
GCP's Organization Policy service provides:
- **Centralized constraint management** across the entire resource hierarchy
- **Constraints → Policies → Inheritance** down the hierarchy
- **Dry-run mode** for testing policy impact before enforcement
- **Conditional policies** scoped with tags

Key dashboard elements:
- Policy compliance by project/folder
- Constraint violations list with severity
- Inheritance visualization showing which level set the policy

### Resource Hierarchy
```
Organization
  └── Folders (nestable)
       └── Projects
            └── Resources
```

### Security Command Center (SCC) — Compliance Visualization
GCP's SCC dashboard organizes security into three domains:
1. **Vulnerability detection**: Misconfigurations, exposed resources, leaked credentials, compliance benchmarks (NIST, HIPAA, PCI-DSS, CIS)
2. **Threat detection and mitigation**: Active threats, malware, DDoS
3. **Postures and policies**: Security posture deployment and monitoring

Service tiers: Standard, Premium, Enterprise
Activation levels: Project-level or Organization-level

### Compliance Benchmark Visualization
- **Benchmark compliance percentage** per standard (e.g., "CIS 1.2 — 87%")
- **Finding severity distribution**: Critical → High → Medium → Low
- **Resource-level findings**: Sortable table with resource, finding, severity, remediation

### Key Takeaway for Our Project
GCP's **dry-run mode for policies** is an interesting pattern we could adapt for our compliance rules (show what WOULD be non-compliant). Their three-domain split (Vulnerability/Threat/Posture) is a clean information architecture.

---

## 4. Datadog — Infrastructure Dashboard Patterns

### Layout System
Datadog offers **three dashboard layout types**:

| Type | Layout | Use Case | Grid |
|------|--------|----------|------|
| **Dashboard** | Grid-based (snap to grid) | Status boards, storytelling views | 12 columns max |
| **Timeboard** | Automatic flow layout | Troubleshooting, time-correlated analysis | Auto-arranged |
| **Screenboard** | Pixel-level precision | Custom executive displays | Free-form |

### Widget Organization
- **Tabs**: Group widgets into named sections. Tabs appear as navigation bar at dashboard top.
- **Groups**: Visual containers for related widgets
- **Template Variables**: Dynamic filters that apply across all widgets (e.g., tenant, environment, region)

### Widget Types Relevant to Governance
| Widget | Governance Use |
|--------|---------------|
| **Query Value** | Single metric display (compliance score, total cost) |
| **Timeseries** | Cost trends, compliance over time |
| **Table** | Resource lists, user lists |
| **Top List** | Top cost contributors, worst compliance scores |
| **Heat Map** | Density of non-compliant resources by type |
| **Change** | Period-over-period comparison |
| **SLO** | Service Level Objective tracking (analogous to compliance targets) |

### Data Density Patterns
- **Conditional formatting**: Color-code cells based on value thresholds (green/yellow/red)
- **Custom links**: Click any widget to drill down to detail view
- **Grouping**: Aggregate by tag dimensions (equivalent to tenant, resource type)
- **Overlays**: Event markers on time-series charts

### Refresh Rate Strategy
| Time Frame | Refresh Rate |
|-----------|-------------|
| 1-10 minutes | 10 seconds |
| 30 minutes - 1 hour | 20 seconds |
| 3-4 hours | 1 minute |
| 1 day | 3 minutes |
| 2 days | 10 minutes |
| 1 week - 3 months | 1 hour |

### Key Takeaway for Our Project
Datadog's **tab-based widget grouping** is directly implementable with HTMX and would solve our dashboard organization problem. Their **template variables** pattern maps to our tenant filter. Conditional formatting on tables is a must-have for compliance data.

---

## 5. Grafana — Dashboard Patterns for Governance Monitoring

### Core Architecture
- Dashboards = panels organized into rows
- Panels are created from data source queries → visualizations
- Data sources: SQL databases, APIs, time-series databases, CSV files

### Best Practices (Official Documentation)

#### Observability Strategies
1. **USE Method** (Utilization, Saturation, Errors) — How "happy" machines are
2. **RED Method** (Rate, Errors, Duration) — How "happy" users are; good for SLAs
3. **Four Golden Signals** (from Google SRE handbook):
   - **Latency**: Time taken to serve a request
   - **Traffic**: How much demand on the system
   - **Errors**: Rate of failures
   - **Saturation**: How "full" the system is

#### Dashboard Maturity Model
Grafana defines three maturity levels:

**Low (ad-hoc)**:
- One-off dashboards that persist forever
- No version control
- Lots of browsing to find the right dashboard
- No alerts directing to dashboards

**Medium (methodical)**:
- Template variables to prevent sprawl (single dashboard for multiple entities)
- Dashboards organized by observability strategy
- **Hierarchical dashboards with drill-downs** to next level

**High (strategic)**:
- Dashboards as code (JSON/YAML)
- Library panels (reusable across dashboards)
- Dashboard-specific alerts
- Consistent naming and tagging

#### Hierarchical Layout Pattern
Grafana demonstrates a **service hierarchy** dashboard pattern:
```
[Load Balancer Row]  — Collapsible
  ├── QPS panel    ├── Latency panel

[App Row]            — Collapsible
  ├── QPS panel    ├── Latency panel

[DB Row]             — Collapsible
  ├── QPS panel    ├── Latency panel
```
Each row has consistent panel layout (QPS left, Latency right), time-correlated across all panels.

### Key Takeaway for Our Project
Grafana's **hierarchical collapsible row pattern** is perfect for our multi-tenant dashboard (one row per tenant). Their **template variables** concept maps to our tenant context. We should aim for "Medium" maturity with hierarchical drill-downs.

---

## 6. Cloudflare Dashboard — Multi-Account/Zone Management

### Information Hierarchy
```
Accounts
  └── Organizations
       └── Members and permissions
       └── User profiles
       └── Domains (Zones)
```

### Analytics Architecture
- **Account-level analytics**: Aggregate across all zones
- **Zone-level analytics**: Per-domain detail
- **Network analytics**: Traffic patterns
- **Workers Analytics Engine**: Custom metrics via SQL queries

### Dashboard UX Patterns
- **Account selector** at top of navigation — switches all content
- **Zone list** as primary navigation within an account
- **Summary cards** at zone level: traffic, security events, performance
- **Time-range selector** applies globally to all analytics

### Key Takeaway for Our Project
Cloudflare's **account → zone** pattern maps directly to our **brand → tenant** hierarchy. Their account-level aggregation with zone drill-down is the exact pattern we need.

---

## 7. Cloud Cost Governance Tools

### 7a. Vantage.sh — Cloud Cost Management

**Platform Overview**: Multi-cloud FinOps platform (AWS, Azure, GCP, Kubernetes, Datadog, Snowflake). Used by CircleCI, Vercel, PlanetScale, Rippling, HelloFresh, Square, PBS.

**Information Architecture**: Organized by user intent/goal:
- **Find immediate savings**: Autopilot (auto-buy savings plans), Cost Recommendations, K8s Rightsizing, Cross-Provider Recommendations
- **Eliminate cost overruns**: Anomaly Detection, Custom Cost Alerts, Budget Alerts
- **Build a FinOps culture**: Virtual Tagging, Network Flow Reports, Unit Costs, Budgets, Financial Commitment Reports

**Dashboard UX Patterns**:
- **Left sidebar navigation**: Overview, Cost Reports (selected), Issues — persistent nav
- **Workspace selector**: Dropdown at top-left for multi-org management
- **Tab system within reports**: Overview | Anomalies tabs within a cost report
- **Filter bar**: Filter button + Date range picker + Settings gear
- **2 KPI cards** side by side: Accrued Costs ($34.5M, +12.78%) and Forecasted Costs ($25.3M, -15.89%)
- **Percentage change badges**: Green for favorable, red for unfavorable, inline next to dollar amount
- **Cost breakdown table**: Service | Accrued Costs | Previous Period Costs | Change % (sortable columns)
- **Stacked bar charts**: Color-coded by cluster/category with Group By dropdown
- **Inline recommendations in chart tooltips**: Hover over bar shows rightsizing suggestion with current vs suggested vCPU and potential savings

**Automated Waste Detection Pattern**:
- Multi-cloud scan visualization showing AWS/Azure/GCP icons
- Progress indicator: Scanning Azure usage 76% with spinner
- Checklist-style findings with color-coded dots (pass/fail/warning)
- Categories: VM usage, storage optimization, network configuration

**Virtual Tagging (Rule Builder Pattern)**:
- Step-by-step wizard: (1) Select Input Cost Filters (2) Select Tag Key (3) Select Output Filters
- Query builder UI: All Costs from GCP where Category is GCP Support (Business) with + New Rule
- Cost-based allocation with percentage rules

**Key Takeaway for Our Project**:
- The **percentage change badge** pattern is directly applicable to our cost KPI cards
- **Inline recommendations in chart tooltips** is an excellent pattern for our savings opportunities
- **Goal-based feature grouping** (Find savings / Eliminate overruns / Build culture) is superior IA to feature-based grouping
- The **report save with dropdown** pattern supports user workflow customization

### 7b. CloudHealth by Broadcom (formerly VMware)

**Platform Overview**: Enterprise-grade multi-cloud cost management and governance. Now under Broadcom after VMware acquisition. Targets enterprises and Managed Service Providers (MSPs).

**Key Features (2026)**:
- **Intelligent Assist**: Gen-AI co-pilot for FinOps queries
- **Smart Summary**: AI-powered cost recommendation summaries
- **Assets Explorer**: Dependency-aware resource elimination (safely identify and remove unused resources)
- **Savings dashboard**: Consolidated savings view in one dashboard
- **Custom Datasets**: General availability (Feb 2026) for bespoke cost dimensions
- **GCP anomaly detection**: New support (Feb 2026)

**Dashboard Patterns** (from product screenshots):
- Dark-themed executive dashboard with multiple widget cards
- **Cost History Report**: Stacked bar charts showing cost over time by category
- **New Dashboard creation**: Widget gallery for adding tiles (similar to Azure Portal)
- **Multi-layout support**: Grid-based dashboards with resizable/movable widgets
- **Role-based dashboards**: Different views for executives vs. FinOps practitioners vs. engineers

**Key Takeaway for Our Project**:
- CloudHealth's **AI-powered summaries** pattern could inspire our cost anomaly descriptions
- **Dependency-aware resource analysis** is relevant for our orphaned resource detection (RM-003)
- The **dark theme executive dashboard** confirms demand for dark mode in governance tools (our dark-mode.css is well-positioned)

### 7c. Spot.io to Flexera (Acquired)

**Status**: Spot.io (previously NetApp Spot) now redirects to **Flexera**, a broader hybrid IT spend and risk management platform. Flexera covers ITAM, SaaS management, FinOps, and vulnerability management.

**Flexera Positioning**: Manage hybrid IT spend and risk — balancing cost, minimizing risk, maximizing business value. Covers complex contracts, licensing, resource monitoring across entire tech stack.

**Key Takeaway**: The cloud cost governance market is consolidating. Standalone tools (Spot.io, CloudHealth) are being absorbed into larger platforms (Flexera, Broadcom). This validates our approach of building governance into a single unified platform rather than point solutions.

---

## 8. Azure Cost Management and Defender for Cloud — Deep Dive

### Azure Cost Analysis Smart Views Pattern

Azure Cost Analysis offers two view types:
1. **Smart views**: AI-curated views with intelligent insights, open in tabs (up to 5)
2. **Customizable views**: User-editable with save/share capability

**Smart View Components**:
- **KPI summary**: Total cost at top with % change from previous period
- **Average cost KPI**: Trend direction indicator
- **Intelligent insights**: Auto-detected anomalies inline
- **Expandable details**: Top contributors drill-down
- **Hierarchical breakdown**: Next logical level in resource/product hierarchy
- **Date pill navigation**: Arrows for previous/next period, click for calendar

### Defender for Cloud Alert Triage UX

**Alert Management Actions**:
- Refresh, Change status, Open query, Suppression rules, Security alerts map, Create sample alerts

**Alert List Components**:
- Summary: Active alerts count + Affected resources count
- Severity distribution bar (stacked horizontal bar)
- Filter chips: Severity, Status, Time, Resource type (removable, addable)
- Sortable table: Checkbox | Severity | Alert title | Affected resource | Activity time
- Grouping dropdown: None, Severity, Resource, Alert type

**Alert Detail Side Panel** (two tabs):
- **Alert Details tab**: Title, severity, status, time, description, affected resources, MITRE ATT&CK tactics
- **Take Action tab** (collapsible accordion):
  - Inspect resource context (to activity logs)
  - Mitigate the threat (to remediation steps)
  - Prevent future attacks (to related recommendations)
  - Trigger automated response (to Logic App)
  - Suppress similar alerts (to suppression rule creation)

**Bulk Operations**: Select multiple alerts via checkboxes and change status at once

**Key Takeaway for Our Project**:
- The **Smart Views** pattern with KPIs + insights + expandable details is the ideal model for our dashboard modules
- The **4-step Take Action accordion** (Inspect, Mitigate, Prevent, Suppress) should be adapted for our compliance remediation workflow
- **Filter chips** (removable badges) are an excellent pattern for our HTMX implementation using hx-get with query parameters

---

## 9. General UX Best Practices

### NN/g: 8 Design Guidelines for Complex Applications

From Kate Kaplan, Nielsen Norman Group (2020), applicable to governance dashboards:

1. **Promote Learning By Doing** — Real-time preview during configuration (e.g., show dashboard update as filters change)
2. **Help Users Adopt More Efficient Methods** — Surface keyboard shortcuts and advanced features for power users
3. **Provide Flexible and Fluid Ways to Navigate** — Multiple paths to the same data (sidebar nav, breadcrumbs, search, drill-down)
4. **Help Users Track Actions and Thought Processes** — Offload working memory with history, annotations, and state persistence
5. **Coordinate Transition Among Multiple Tools and Workspaces** — Integration with Azure Portal, email, Teams
6. **Reduce Visual Clutter Without Reducing Capability** — **Staged disclosure**: show options only when relevant to reduce clutter
7. **Support Personalization and Customization** — Saved views, custom date ranges, pinned tenants
8. **Mitigate Risk of Errors** — Confirmation dialogs for destructive actions, undo capability

### Microsoft Fluent UI: Data Table Patterns

The **DetailsList** component (used throughout Azure Portal):
- "Use a details list when **information density is critical**"
- Sort, group, and filter capabilities built-in
- Variants: Basic, **Compact** (for power users), Variable Row Heights, Custom Item Columns
- **Selection modes**: Single, Multi, None
- **Row headers**: Primary label column gets `isRowHeader: true` for accessibility
- **Keyboard navigation**: Arrow keys, Ctrl+arrows, Space for selection
- Content: Sentence-case column headers
- Accessible: screen reader labels on all interactive elements

### Material Design: Data Visualization Principles

Three core principles:
1. **Accurate** — Prioritize data accuracy, clarity, and integrity; don't distort information
2. **Helpful** — Navigate data with context; emphasize exploration and comparison
3. **Scalable** — Adapt for different device sizes; anticipate needs on data depth, complexity, and modality

Chart type selection depends on:
- The **data** you want to communicate
- What you want to **convey about** that data

---

## 8. Cross-Platform Pattern Synthesis

### Universal Patterns (Used by 4+ Platforms)

| Pattern | Azure | AWS | GCP | Datadog | Grafana | CF |
|---------|-------|-----|-----|---------|---------|-----|
| Summary → Drill-down hierarchy | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tenant/account selector (global filter) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Grid-based layout (12-column) | ✅ | — | — | ✅ | ✅ | — |
| Collapsible sections/rows | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Time range selector (global) | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| Conditional formatting (RAG) | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Score/percentage as primary metric | ✅ | — | ✅ | ✅ | — | — |

### Compliance Visualization Patterns

| Pattern | Where Used | When to Use |
|---------|-----------|-------------|
| **Scorecard (large number + subtitle)** | Azure Secure Score, GCP SCC | Single aggregate metric |
| **Stacked bar chart** | Azure Policy, AWS Control Tower | Distribution of compliant vs. non-compliant |
| **Progress bar** | Azure Policy initiatives | Progress toward a goal (e.g., 85/100 resources compliant) |
| **Heat map** | Datadog, Grafana | Density of issues across dimensions |
| **Badge/pill** | All platforms | Inline status indicator (Compliant/Non-Compliant) |
| **Semi-circle gauge** | Limited use | Single metric, NOT for lists/tables |

**Consensus**: Scorecards + stacked bars are preferred. Gauges are falling out of favor for governance (too much visual weight, poor comparison capability).

### Cost Visualization Patterns

| Pattern | Where Used | When to Use |
|---------|-----------|-------------|
| **Area chart (filled)** | Azure Cost Management | Show spend volume over time |
| **Line chart with forecast** | Azure Cost Management | Trend with projection |
| **Sparkline (in card)** | Datadog, Cloudflare | Inline mini-trend in summary card |
| **Bar chart (grouped)** | AWS Cost Explorer | Compare categories side-by-side |
| **Top-N list** | All platforms | Highest cost contributors |
| **Change indicator (↑↓)** | All platforms | Period-over-period delta |

**Consensus**: Area charts for cost trends (filled area shows volume better than lines). Sparklines in summary cards for at-a-glance trends.

### Identity/Security Risk Patterns

| Pattern | Where Used | When to Use |
|---------|-----------|-------------|
| **Risk-sorted list** | Azure Defender, GCP SCC | Prioritized action items |
| **Severity badges** | All platforms | Critical/High/Medium/Low |
| **MFA coverage bar** | Azure AD, our platform | Binary coverage metric |
| **Privileged user count** | Azure PIM, our platform | High-risk user highlight |
| **Activity timeline** | Azure AD, Datadog | Suspicious activity detection |

### Alert Management Patterns

| Pattern | Where Used | When to Use |
|---------|-----------|-------------|
| **Count badge in nav** | Datadog, Cloudflare | Total active alerts |
| **Severity-grouped list** | All platforms | Triage workflow |
| **Acknowledge/Snooze/Resolve** | Datadog, Grafana | Alert lifecycle |
| **Alert → Dashboard link** | Grafana best practice | Direct investigation path |
| **Threshold lines on charts** | Azure, Datadog | Visual budget/SLA limits |

### Data Table Patterns

| Pattern | Where Used | When to Use |
|---------|-----------|-------------|
| **Compact mode** | Fluent UI, Datadog | High row count (50+ items) |
| **Column sort + filter** | All platforms | Any tabular data |
| **Inline status badges** | All platforms | Quick status scan |
| **Row-click drill-down** | Azure, Datadog | Navigate to detail |
| **Bulk selection** | Azure, AWS | Multi-item actions |
| **Sticky header** | Fluent UI | Long scrolling tables |
| **Pagination vs. virtual scroll** | Varies | <1000 rows: paginate; 1000+: virtual scroll |

---

## 9. Data Density vs. Clarity — Guidance for Power Users

### The Expert User Sweet Spot

For 10-30 power users (our target audience), the research is clear:

> **Favor density over simplicity, but use progressive disclosure to manage complexity.**

Specific guidance:
1. **Show more data, fewer clicks** — Power users prefer seeing 4 KPI cards + 2 charts + 1 table on a single screen over stepping through wizard-like pages
2. **Use compact table mode by default** — Reduce row height, smaller font, tighter spacing
3. **Provide keyboard shortcuts** — Power users learn them quickly and expect them
4. **Allow saved views** — Let users save filter combinations they use daily
5. **Don't hide the numbers** — Show exact values alongside visualizations, not just tooltips
6. **Use conditional formatting aggressively** — Red/yellow/green on table cells, bold anomalies
7. **Default to the most useful time range** — Not "all time" but "last 30 days" or "current month"

### Information Architecture for 10-30 Users

```
┌─────────────────────────────────────────────────────────┐
│ Dashboard (Level 0 — Executive Summary)                  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │
│  │ Cost │ │Compl.│ │Resrc.│ │Ident.│  ← 4 KPI Cards    │
│  │ $12k │ │ 87% │ │ 342  │ │ 156  │     with delta     │
│  └──────┘ └──────┘ └──────┘ └──────┘                   │
│                                                          │
│  [▼ Cost Trends]           [▼ Compliance by Tenant]     │
│  ████████████████           ████████████████             │
│  ████████████████           ████████████████  ← Charts  │
│                                                          │
│  [▼ Recent Alerts / Action Items]                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Table: severity | tenant | item | age | action  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
         │ click tenant
         ▼
┌─────────────────────────────────────────────────────────┐
│ Tenant Detail (Level 1 — Per-Tenant)                     │
│  KPI cards for THIS tenant                               │
│  Compliance breakdown by category                        │
│  Cost breakdown by resource type                         │
│  Identity status (MFA, privileged users)                 │
│  Resource inventory summary                              │
└─────────────────────────────────────────────────────────┘
         │ click resource/policy
         ▼
┌─────────────────────────────────────────────────────────┐
│ Resource/Policy Detail (Level 2 — Per-Item)              │
│  Full compliance history                                  │
│  Cost history                                             │
│  Related recommendations                                  │
│  Audit trail                                              │
└─────────────────────────────────────────────────────────┘
```

### Dashboard Layout Grid

Based on Datadog and Grafana patterns, recommended grid:

```
┌────────────────────────────────────────────────┐
│ Header: Title | Tenant Selector | Time Range   │  ← Fixed
├────────────────────────────────────────────────┤
│ [3col] [3col] [3col] [3col]                    │  ← KPI Cards
├────────────────────────────────────────────────┤
│ [6col]              │ [6col]                   │  ← Charts
│ Cost Trend          │ Compliance by Tenant     │
├────────────────────────────────────────────────┤
│ [12col]                                        │  ← Full-width
│ Action Items / Alerts Table                    │  ← Collapsible
├────────────────────────────────────────────────┤
│ [6col]              │ [6col]                   │  ← Secondary
│ Resource Overview   │ Identity Overview        │  ← Collapsible
└────────────────────────────────────────────────┘
```

Uses Tailwind's `grid-cols-12` for flexible responsive layout.
