# Azure Defender for Cloud — Alert Triage UX (Raw Findings)

**Source**: https://learn.microsoft.com/en-us/azure/defender-for-cloud/manage-respond-alerts
**Date Accessed**: March 27, 2026
**Tier**: Tier 1 (Official Microsoft documentation)

---

## Overview

"Defender for Cloud collects, analyzes, and integrates log data from your Azure, hybrid, and multicloud resources, the network, and connected partner solutions, such as firewalls and endpoint agents. Defender for Cloud uses the log data to detect real threats and reduce false positives. A list of prioritized security alerts is shown in Defender for Cloud along with the information you need to quickly investigate the problem and the steps to take to remediate an attack."

## Dashboard KPI Bar (Screenshot Analysis)

Top bar shows 5 KPI summary cards:
1. 🟡 59 Azure subscriptions
2. 🟡 1 AWS accounts
3. 🟢 4 GCP projects
4. ≡ 161 Active recommendations
5. 🔴 121 Security alerts (selected/highlighted)

## Dashboard 2x2 Grid Sections

### Secure Score (top-left)
- Donut chart: 60% (3025 POINTS)
- COMPLETED: 1/16
- COMPLETED Recommendations: 29/190
- Link: "Improve your secure score >"

### Regulatory Compliance (top-right)
- "Current compliance by passed controls"
- Horizontal progress bars per framework:
  - UKO and U...: 0/7
  - SOC TSP: 1/13
  - NIST SP 80...: 2/23
  - HIPAA HITR...: 2/22
  - NIST SP 80...: 3/29
- Link: "Improve your compliance >"

### Workload Protections (bottom-left)
- Resource coverage: 95% — "For full protection, enable 10 resource plans"
- "Alerts by severity" — stacked bar chart
  - Bar values visible: 13, 29, 66, 22 Sun, 26
- Link: "Enhance your threat protection capabilities >"

### Inventory (bottom-right)
- Unmonitored VMs: 🔴 60 — "To better protect your organization, we recommend installing agents"
- Total Resources: 3900
- Status badges: Unhealthy (2936) | Healthy (679) | Not applicable (285)
- Link: "Explore your resources >"

## Alert List UI

### Toolbar Actions
- Refresh
- Change status (dropdown)
- Open query
- Suppression rules
- Security alerts map (Preview)
- Create sample alerts

### Summary Bar
- 🔴 3 Active alerts
- 🔵 1 Affected resources
- Active alerts by severity [horizontal stacked bar]: High (3)

### Filter Controls
- Filter chips (removable): "Status == Active ×", "Severity == High ×"
- Time filter: "Time == Last month ×"
- "+ Add filter" button
- "No grouping" dropdown

### Table Structure
| Column | Sortable? | Content |
|--------|-----------|---------|
| Checkbox | — | Multi-select for bulk operations |
| Severity | ↕ | Icon + text (High) |
| Alert title | ↕ | Truncated with "..." |
| Affected resource | ↕ | Resource identifier with icon |
| Activity start time | ↕ | Date/time |

### Example Rows
1. ☐ High | Exposed Kubernetes dashboard detec... | 🖥 | 11/05/18 1:58 PM (selected/highlighted)
2. ☐ High | Microsoft Defender for Cloud test aler... | 🖥 | 11/04/18 11:50 AM
3. ☐ High | Exposed Kubernetes dashboard detec... | 🖥 | 10/26/18 10:44 PM

## Alert Detail Side Panel

### Alert Header
- Alert title: "Exposed Kubernetes dashboard detected"
- Severity: High
- Status: Active (with dropdown to change)
- Time: 11/05/20, 13:58
- Activity time

### Alert Description
"Kubernetes audit log analysis detected exposure of the Kubernetes Dashboard by a LoadBalancer service. Exposed dashboard allows an unauthenticated access to the cluster management and poses a security threat."

### Affected Resource
- 🔒 Kubernetes service
- 🟡 Subscription

### MITRE ATT&CK Tactics
- Initial Access

### Navigation Dots
- Carousel dots at bottom for paging through multiple alerts

### Action Buttons
- "View full details" (blue/primary button)
- "Take action" (secondary)

## Alert Investigation Steps

Review high-level information:
1. Alert severity, status, and activity time
2. Description that explains the precise activity that was detected
3. Affected resources
4. Kill chain intent of the activity on the MITRE ATT&CK matrix

## Take Action Tab (Detail View)

### Full Page Alert View Structure
- Breadcrumb: Dashboard > Security alert
- Alert title with edit icon
- Alert: "Potential SQL Injection"
- Metadata: High Severity | Active Status | 06/11/20, 1... Activity time

### Alert Description
"Potential SQL injection was detected on your database Demo on server R-DEV\SQLEXPRESS"

### Affected Resource
- Azure Arc machine | Env: Development
- Subscription

### Intent
- Pre-attack

### Take Action Tab Sections (Collapsible Accordion)

#### 1. Inspect Resource Context (expanded)
- "Start with examining the resource logs around the time of the alert."
- [Open logs] button

#### 2. Mitigate the Threat (expanded)
- "Read more about SQL Injection threats and best practices for safe application code."
- "You have 34 more alerts on the affected resource. View all >>"

#### 3. Prevent Future Attacks (expanded)
- "Your top 2 active security recommendations on [RONMAT-DEV]:"
  - Medium 🟡 Windows Defender Exploit Guard should be enabled on your machines
  - High 🔴 Vulnerabilities on your SQL servers on machine should be remediated
- "Saving security recommendations can prevent future attacks by reducing attack surface."

#### 4. Trigger Automated Response (collapsed)
- Option to trigger a Logic App

#### 5. Suppress Similar Alerts (collapsed)
- Create suppression rule for similar characteristics

## Bulk Operations

"Change the status of multiple security alerts at once" section:
- Select multiple alerts using checkboxes
- Change status in bulk (e.g., dismiss multiple false positives)
- Available through the "Change status" toolbar button when items are selected
