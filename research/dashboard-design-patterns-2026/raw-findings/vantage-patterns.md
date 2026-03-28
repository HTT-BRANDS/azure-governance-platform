# Vantage.sh — Raw UX Findings

**Source**: https://www.vantage.sh, https://www.vantage.sh/features, https://www.vantage.sh/features/cost-reports
**Date Accessed**: March 27, 2026
**Tier**: Tier 2 (vendor product marketing with live UI screenshots)

---

## Homepage Positioning
- "Cloud Cost Management for Modern Engineering Teams"
- New: "Introducing Vantage in ChatGPT" (AI integration)
- Trusted by: CircleCI, Vercel, Boom, Rippling, HelloFresh, Joybird, Starburst, Metronome, Square, PBS

## Feature Organization (Goal-Based IA)

### Find Immediate Savings
- Autopilot (Buying of Savings Plans)
- Cost Recommendations
- Kubernetes Rightsizing
- Cross-Provider Recommendations

### Eliminate Cost Overruns
- Anomaly Detection
- Custom Cost Alerts
- Budget Alerts

### Build a FinOps Culture
- Virtual Tagging
- Network Flow Reports
- Unit Costs
- Budgets
- Financial Commitment Reports
- Slack, Jira, Microsoft Teams Integrations

## Cost Reports UI

### Layout
- Left sidebar: Overview, Cost Reports (active), Issues
- Workspace selector: "Management" dropdown at top-left
- Tabs within report: "Overview" | "Anomalies"
- Filter bar: [Filter] [August 1 - August 31] [Settings]
- Save button with dropdown

### KPI Cards
- Accrued Costs: $34,567,883.65 with +12.78% badge
- Forecasted Costs: $25,324,463.12 with -15.89% badge
- Badges are colored (green for good, red for bad) and positioned right of the dollar amount

### Cost Breakdown Table
Columns: Service (with provider icon) | Accrued Costs | Previous Period Costs | Change %
- All columns sortable (sort icon visible)
- Service icons (AWS logo next to service names)
- Example rows:
  - Log Management: $4,516.86 vs $2,573.97 = +75.48%
  - Amazon Redshift: $1,577.40 vs $520.00 = +203.35%

## Kubernetes Visibility
- Stacked bar chart with color-coded clusters
- "Group By: Cluster" dropdown
- Hover tooltip: "Rightsizing Suggestion — Current vCPU: 16, Suggested vCPU: 2, Potential Savings: $143/mo"
- Legend with cluster identifiers (prod-alpha-ap-southeast-1, stg-ka...)

## Automated Waste Detection
- Multi-cloud scan visualization: AWS, Azure, GCP icons
- Progress bar: "Scanning Azure usage 76%" with spinner animation
- Checklist findings:
  - 🟡 No issues found in virtual machine usage
  - 🔵 Storage volumes optimized and healthy
  - 🟢 Network configuration within best practices

## Virtual Tagging (Rule Builder)
- Title: "Cost Based Values — Allocate percentages of a cost a tag"
- Step 1: Select Input Cost Filters
  - Query builder: "All Costs ... from [GCP icon] GCP where [Category icon] Category is [GCP Support (Business) ×] [+] [🗑]"
  - "+ New Rule" button
- Step 2: Select a Tag Key (dropdown: "Sports Event")
- Step 3: Select Output Cost Filters

## Features Page
- "Tools for the Whole Organization"
- "Vantage is a complete FinOps platform from visibility to optimization to enterprise-grade cost governance for the cloud"
- Sections: VISIBILITY (Kubernetes, Virtual Tagging), OPTIMIZATION (Automated Waste Detection)

## Customer Quote
PlanetScale CTO: "Doing all our cost reporting manually was taking too much time and wasn't sustainable. Every month felt like starting from scratch."
