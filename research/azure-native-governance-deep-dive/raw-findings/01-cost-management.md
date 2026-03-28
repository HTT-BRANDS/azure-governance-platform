# Azure Cost Management — Cross-Tenant via Lighthouse

## Source
- **URL**: https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/overview-cost-management
- **URL**: https://learn.microsoft.com/en-us/azure/lighthouse/concepts/cross-tenant-management-experience
- **URL**: https://learn.microsoft.com/en-us/azure/cost-management-billing/understand/analyze-unexpected-charges
- **Tier**: 1 (Official Microsoft Documentation)
- **Last verified**: 2026-03-27

## Key Findings

### Cross-Tenant Cost Access via Lighthouse
- CSP partners can view, manage, and analyze **pre-tax consumption costs** (not inclusive of purchases) for customers under the Azure plan
- Cost is based on **retail rates** and the Azure RBAC access the partner has for the customer's subscription
- Currently, you can view consumption costs at retail rates for **each individual customer subscription** based on Azure RBAC access
- **No native cross-tenant cost aggregation** — costs are viewed per-subscription

### Anomaly Detection
- Available in Cost Analysis **smart views** at **subscription scope** only
- Uses a **univariate time series, unsupervised prediction model**
- Anomalies evaluated for subscriptions **daily**, comparing day's total usage to a forecasted total based on the **last 60 days**
- Accounts for common patterns (e.g., Monday spikes)
- Anomaly detection runs **36 hours after end of day (UTC)** to ensure complete data
- Can create anomaly alerts to get notified automatically
- **Cost anomaly alerts are NOT available for Azure Government customers**
- No cross-tenant anomaly aggregation — must set up per-subscription

### Forecasting
- Cost forecasting is available within Cost Analysis views
- Based on historical usage patterns
- Forecast scope: per subscription, per resource group, or per management group
- **No cross-tenant unified forecast**

### Idle Resource Detection
- **Not a Cost Management feature** — requires Azure Advisor separately
- Azure Advisor provides right-sizing and shutdown recommendations
- Advisor works via Lighthouse for delegated subscriptions
- No unified idle resource dashboard across tenants

### Budget & Alerting
- Budget alerts can be created per subscription
- Budget alerts fire when threshold is reached
- Can be configured for delegated subscriptions via Lighthouse
- **No cross-tenant budget roll-up**

### Chargeback Capabilities
- **No native chargeback/showback reporting**
- Cost allocation rules exist but are limited to EA/MCA billing scopes
- No ability to categorize costs into custom billing categories (compute, storage, network, etc.)
- No per-tenant cost allocation with custom markup/overhead

### Data Latency
- Billing data finalized 72 hours after billing period ends
- Real-time cost data available with some delay per service

### Cost
- **$0** — Azure Cost Management is free for Azure subscriptions
- Cost exports to storage incur storage costs (~negligible)
