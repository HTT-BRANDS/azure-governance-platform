# Azure Monitor Workbooks — Cross-Tenant Dashboards

## Source
- **URL**: https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/workbooks-overview
- **URL**: https://learn.microsoft.com/en-us/azure/governance/resource-graph/concepts/query-language
- **Tier**: 1 (Official Microsoft Documentation)
- **Last verified**: 2026-03-27

## Key Findings

### What Azure Workbooks Provide
- Flexible canvas for data analysis and rich visual reports within the Azure portal
- Tap into multiple data sources from across Azure
- Combine multiple kinds of visualizations and analyses
- Combine text, log queries, metrics, and parameters into rich interactive reports
- Shareable and collaborative

### Data Sources
Workbooks can query:
- Azure Monitor Logs (Log Analytics)
- Azure Monitor Metrics
- Azure Resource Graph (**automatically includes Lighthouse-delegated resources**)
- Azure Resource Manager (ARM API calls)
- Azure Data Explorer
- Custom JSON endpoints
- Merge/union results from multiple sources

### Cross-Tenant Capabilities via Lighthouse
- **Azure Resource Graph queries in workbooks automatically span delegated tenants**
- Can build parameterized workbooks with tenant/subscription selectors
- Can create cross-tenant resource inventory dashboards
- Can visualize Azure Policy compliance across tenants (summary level)
- Can show cost data via ARM API integration
- Can display Defender for Cloud recommendations cross-tenant

### Visualization Types
- Charts (line, bar, area, scatter, pie)
- Grids/tables
- Tiles (summary cards)
- Text blocks (markdown)
- Maps
- Graphs (network diagrams)
- Honeycomb layouts
- Composite bars

### Access Control
- Workbook permissions based on Azure RBAC for the resources included
- Standard roles: Monitoring Reader (/read), Monitoring Contributor (/write)
- Custom roles need `microsoft.insights/workbooks/write`
- Via Lighthouse, delegated Monitoring Reader role enables workbook viewing

### What Workbooks Do Well
1. **Rich visualization layer** for cross-tenant Azure resource data
2. **Free** — no cost for workbooks themselves
3. **Parameterized** — can build dynamic tenant/subscription filters
4. **Multiple data sources** — combine different query types
5. **Built-in templates** — Defender for Cloud, Cost Management, etc.
6. **Shareable** — pin to dashboards, share with teams

### What Workbooks CANNOT Do
1. **Cannot query Entra ID data** — no Microsoft Graph integration in workbooks
   - No MFA compliance dashboards
   - No stale account detection
   - No privileged access reporting
   - No guest user management views
2. **Requires deep KQL/Kusto expertise** to build effective dashboards
3. **No DMARC monitoring** — completely outside Azure Monitor scope
4. **No regulatory deadline tracking** — no date-driven countdown capabilities
5. **No chargeback/showback calculations** — can show raw costs but no allocation logic
6. **Locked into Azure portal UX** — cannot customize branding
7. **No alerting from workbook data** — need separate Alert rules in Azure Monitor
8. **Not accessible to non-technical users** — requires Azure portal access and understanding
9. **No custom compliance rules** — limited to Azure Policy states
10. **Compliance detail gap**: Cannot drill into noncompliant resource details cross-tenant (Lighthouse limitation)

### Cost
- **Workbooks**: $0 (free)
- **Log Analytics data ingestion**: ~$2.76/GB/day (first 5GB/day free per workspace)
- **Log Analytics data retention**: 31 days free, then $0.10/GB/month
- For typical governance monitoring: ~$50-200/month in ingestion costs
- **Azure Resource Graph queries**: Free (no ingestion cost)

### Building Cross-Tenant Workbooks: Effort Estimate
- Basic resource inventory workbook: ~4-8 hours (KQL expertise required)
- Cost overview workbook: ~8-16 hours
- Compliance summary workbook: ~16-24 hours
- Full governance dashboard: ~40-80 hours of KQL development
- Ongoing maintenance: ~4-8 hours/month for query updates
- **Total initial effort**: ~70-130 hours of specialized KQL development
