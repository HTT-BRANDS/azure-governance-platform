# Recommendations: GitHub Plan Selection for azure-governance-platform

## Primary Recommendation: Enterprise Cloud

For a 7-seat Azure governance platform, **GitHub Enterprise Cloud at $147/month** is the recommended choice.

### Rationale
1. **Security requirements:** A governance platform handling Azure resources needs SSO, SCIM, and audit capabilities — only available on Enterprise
2. **CI/CD headroom:** 50,000 min/month vs 3,000 gives substantial room for CI/CD pipelines, testing, and deployment automation
3. **GHCR is free:** Container registry costs are $0, offsetting the plan premium
4. **Compliance:** SOC2 reports and FedRAMP ATO may be required for governance tooling

### Action Items (Prioritized)

1. **Immediate:** Verify GHCR free status applies to your account (check billing dashboard)
2. **Before purchase:** Contact GitHub Sales to negotiate pricing — "starting at" $21 may be negotiable for annual commitment
3. **Setup:** Configure Azure AD/Entra ID as SAML IdP for SSO
4. **Optimization:** Set up self-hosted runners for heavy workloads to preserve included minutes
5. **Monitoring:** Set up spending budgets and 90%/100% usage alerts in GitHub billing settings
6. **Risk mitigation:** Monitor GitHub announcements for GHCR pricing changes (1-month notice guaranteed)

## Alternative: Team Plan ($28/month)

Only viable if:
- No SSO/compliance requirements
- CI/CD usage stays under 3,000 min/month
- Willing to accept security trade-offs
