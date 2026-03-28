# Project-Specific Recommendations

**Research Date:** March 27, 2026
**Project:** Azure Multi-Tenant Governance Platform (4-5 tenants, PE portfolio, Riverside deadline)

---

## Primary Recommendation: Continue with Custom Platform

### Rationale
The custom platform has already been built and is operational (v1.2.0+). The research conclusively shows that **no commercial or open-source alternative can replace 80% of its functionality** because:

1. **Unique modules** (Riverside compliance, DMARC, multi-brand theming) have zero commercial equivalents
2. **Azure Lighthouse integration** is not supported by any evaluated platform
3. **Scale mismatch** — commercial platforms are priced for 50+ account enterprises, not 4-5 tenant portfolios
4. **Identity governance via Entra ID** is not addressed by any FinOps tool

### Cost Comparison

| Approach | Monthly Cost | Annual Cost | Coverage |
|----------|-------------|-------------|----------|
| **Custom Platform** (Azure App Service B2 + SQL S0) | ~$50-75 | ~$600-900 | 100% |
| **Vantage Business** (cost module only) | $200 | $2,400 | ~25% |
| **CoreStack** (closest match) | ~$1,250+ | ~$15,000+ | ~60% |
| **CloudHealth** (enterprise minimum) | ~$833+ | ~$10,000+ | ~35% |
| **Vantage + Azure native tools** (best combo) | ~$200 | ~$2,400 | ~55% |

The custom platform costs **less per year than one month of any commercial alternative**, while providing 100% coverage.

---

## Secondary Recommendations: Potential Complements

### 1. Infracost CI/CD (Free) — Add to IaC Workflow
**Priority: Low | Effort: 2 hours | Cost: $0**

Add Infracost to the GitHub Actions pipeline for Bicep deployments:
- Estimates cost impact of infrastructure changes in PRs
- Catches expensive mistakes before deployment
- Free tier is sufficient for this project's scale
- Complements (doesn't replace) runtime cost monitoring

```yaml
# Example GitHub Action addition
- name: Infracost Cost Estimate
  uses: infracost/actions/setup@v3
  with:
    api-key: ${{ secrets.INFRACOST_API_KEY }}
```

### 2. Vantage Starter (Free) — Validate Cost Data
**Priority: Low | Effort: 1 hour | Cost: $0**

Connect the free Vantage Starter tier as a cost data validation source:
- Cross-reference custom platform cost data with Vantage
- $2,500 cloud spend limit may be sufficient for one test tenant
- SAML SSO included even in free tier
- Useful as a "second opinion" on cost anomalies

### 3. Azure Native Tools — Already Integrated
**Priority: N/A | Already in use**

The custom platform already leverages Azure native capabilities:
- Azure Cost Management APIs (cost data source)
- Azure Policy (compliance data source)
- Microsoft Secure Score (security posture)
- Entra ID / Microsoft Graph (identity data)
- Azure Lighthouse (multi-tenant delegation)

No additional Azure native tool integration is needed.

---

## What NOT to Do

### ❌ Do Not Replace the Custom Platform with a Commercial Tool
- The build cost is sunk; the maintenance cost is minimal
- No commercial tool covers Riverside compliance, DMARC, or multi-brand theming
- Commercial pricing is optimized for large enterprises, not 4-5 tenants

### ❌ Do Not Adopt CoreStack as a "Better Platform"
- Despite being the closest feature match, CoreStack:
  - Costs 15-50x more annually than the custom platform
  - Still doesn't cover DMARC, Riverside, or multi-brand theming
  - Adds vendor lock-in risk
  - Is over-engineered for 4-5 tenants

### ❌ Do Not Invest Time in Komiser
- ELv2 license restricts usage
- Project appears to be declining (2-year-old code, many open issues)
- Feature set is too basic to be useful

### ❌ Do Not Consider OpenCost
- Kubernetes-only — the PE portfolio uses App Service, VMs, and SQL, not Kubernetes
- Wrong tool category entirely

---

## Feature Gap Analysis: What Could Be Borrowed

Even though replacement isn't recommended, some competitor features could inspire custom platform improvements:

### From Vantage
| Feature | Value | Implementation Effort |
|---------|-------|----------------------|
| Virtual Tagging | Retroactive cost allocation without Azure tags | Medium — would need tag inference engine |
| FinOps as Code | Terraform/Bicep provider for cost policies | Low — could add cost policy YAML files |
| Automated Waste Detection scan UI | Visual scanning progress for Azure waste | Low — UX enhancement |

### From CloudHealth
| Feature | Value | Implementation Effort |
|---------|-------|----------------------|
| Intelligent Assist (AI chat) | Natural language queries on governance data | High — would need LLM integration |
| Realized Savings tracking | Show actual savings from recommendations acted on | Medium — track recommendation → action → savings |

### From CoreStack
| Feature | Value | Implementation Effort |
|---------|-------|----------------------|
| AI-driven governance scoring | Automated maturity assessment | Medium — already partially exists in Riverside module |
| Ten-facet governance model | Structured governance framework | Low — documentation/conceptual alignment |

### From Infracost
| Feature | Value | Implementation Effort |
|---------|-------|----------------------|
| Governance best practice scores | Category-level FinOps maturity (Compute 39%, Storage 63%) | Medium — would need scoring rules |
| PR cost comments | Cost impact in deployment PRs | Low — CI/CD integration |

---

## Risk Assessment

### Risk of Staying with Custom Platform
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Maintenance burden grows | Medium | Platform is well-tested (700+ tests); FastAPI/Python are stable |
| Feature gap vs. commercial tools widens | Low | Custom features (Riverside, DMARC) are the differentiators |
| Single developer dependency | Medium | Good documentation, standard tech stack, agent-assisted development |
| Azure API changes break integrations | Low | Circuit breaker patterns already implemented |

### Risk of Switching to Commercial Platform
| Risk | Likelihood | Impact |
|------|-----------|--------|
| Lose Riverside compliance tracking | Certain | **Critical** — regulatory deadline July 8, 2026 |
| Lose DMARC monitoring | Certain | High — email security gap |
| Lose multi-brand theming | Certain | Medium — brand identity impact |
| Higher ongoing costs | Certain | 15-50x current hosting cost |
| Vendor lock-in | High | Difficult to migrate back |
| Azure Lighthouse integration loss | Certain | Would need per-tenant credentials |

---

## Action Items

1. **No action needed on platform replacement** — custom platform is the right choice
2. **Optional**: Add Infracost free tier to CI/CD for pre-deployment cost checks
3. **Optional**: Use Vantage free tier as cost data validation source
4. **Future consideration**: If the PE portfolio grows to 15+ tenants, re-evaluate CoreStack or CloudHealth
5. **Monitor**: Spot.io/Flexera merger for potential new competitive offerings
6. **Document**: This analysis as ADR evidence for "build vs. buy" decision justification
