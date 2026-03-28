# Microsoft Defender for Cloud — Cross-Tenant Compliance via Lighthouse

## Source
- **URL**: https://learn.microsoft.com/en-us/azure/defender-for-cloud/cross-tenant-management
- **URL**: https://learn.microsoft.com/en-us/azure/defender-for-cloud/concept-cloud-security-posture-management
- **URL**: https://azure.microsoft.com/en-us/pricing/details/defender-for-cloud/
- **URL**: https://learn.microsoft.com/en-us/azure/lighthouse/concepts/cross-tenant-management-experience
- **Tier**: 1 (Official Microsoft Documentation)
- **Last verified**: 2026-03-27

## Key Findings

### Cross-Tenant Capabilities (via Lighthouse)
- **Manage security policies**: From one view, manage security posture of many resources with policies, take actions with security recommendations, collect and manage security-related data
- **Improve Secure Score and compliance posture**: Cross-tenant visibility to view overall security posture of ALL tenants and where to improve secure score and compliance posture for each
- **Remediate recommendations**: Monitor and remediate recommendations for many resources from various tenants at one time — tackle highest risk vulnerabilities across all tenants
- **Manage Alerts**: Detect alerts throughout different tenants, take action on resources out of compliance with actionable remediation steps
- **Manage advanced cloud defense features**: JIT VM access, Adaptive Network Hardening, adaptive application controls, File Integrity Monitoring

### Foundational CSPM (FREE)
Included at no cost:
- Asset inventory
- Data exporting
- Data visualization with Azure Workbooks
- Microsoft Cloud Security Benchmark
- Secure Score
- Security recommendations
- Continuous assessments
- Works across Azure, AWS, GCP

### Defender CSPM (PAID: $5.11/billable resource/month)
Additional features:
- Agentless VM secrets scanning
- Agentless VM vulnerability scanning
- AI security posture management
- API security posture management
- Attack path analysis
- Azure Kubernetes Service security dashboard
- Code-to-cloud mapping for containers and IaC
- Critical assets protection
- Custom Recommendations
- Data security posture management (DSPM)
- External attack surface management
- Governance rules
- Billable resources: VMs, Storage Accounts, OSS DBs, SQL PaaS, Servers on Machines, Serverless functions, Web apps

### Cloud Workload Protection Pricing
- Defender for Servers Plan 1: $4.906/server/month
- Defender for Servers Plan 2: $14.60/server/month
- Defender for Containers: $6.8693/vCore/month
- Defender for SQL: $15/instance/month
- Defender for Storage: $10/storage account/month

### Regulatory Framework Support
- Microsoft Cloud Security Benchmark (built-in)
- Regulatory compliance dashboard maps to standards
- Limited to Azure infrastructure standards — NOT custom business compliance
- Cannot map to arbitrary regulatory frameworks (SOC2 Type II, NIST CSF 2.0 custom controls)

### Critical Limitations
1. **Entire subscription must be delegated** to the managing tenant — Defender for Cloud scenarios **aren't supported with delegated resource groups**
2. **Viewing compliance DETAILS for noncompliant resources in customer tenants is NOT currently supported** via Lighthouse (can see summary, not detail)
3. Cannot remediate `deployIfNotExists` policies without proper role assignments
4. No DMARC monitoring capability
5. No specialized regulatory deadline tracking
6. No custom compliance rule engine beyond Azure Policy

### Integrations
- ServiceNow integration available (preview)
- Azure Workbooks for visualization
- Logic Apps for automation
