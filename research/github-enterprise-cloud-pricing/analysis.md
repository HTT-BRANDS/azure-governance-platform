# Multi-Dimensional Analysis: GitHub Enterprise Cloud Pricing

## Cost Analysis (7 Seats)

### Direct Costs
| Item | Team | Enterprise Cloud |
|------|------|-----------------|
| Seat cost | $28/mo ($336/yr) | $147/mo ($1,764/yr) |
| Actions overage (est. 5K extra min Linux) | $30/mo | $0 (within 50K quota) |
| Storage overage | Likely needed | Unlikely (50GB) |
| GHCR | Free | Free |
| Pages | Free | Free |
| **Estimated total** | **~$58-70/mo** | **$147/mo** |

### Hidden Costs to Consider
- Enterprise may be cheaper if you'd regularly exceed Team's 3,000-minute quota
- Breakeven: ~19,500 additional Linux 2-core minutes/month on Team ≈ $117/mo in overage, making Enterprise cheaper
- Enterprise's "starting at" language implies negotiable pricing for committed contracts

## Security Analysis
- **Enterprise Cloud advantage:** SAML SSO, SCIM provisioning, Enterprise Managed Users, audit log API, SOC1/SOC2 reports, FedRAMP ATO
- **Team gap:** No SSO means password-based auth or personal PATs — significant security risk for an Azure governance platform
- **Recommendation:** For a governance/compliance platform, Enterprise's security features are likely **required**, not optional

## Implementation Complexity
- **Team:** Simple setup, no SSO configuration needed
- **Enterprise:** Requires SAML IdP configuration (Azure AD/Entra ID), SCIM setup, Enterprise Account management
- **Migration path:** Team → Enterprise is straightforward; GitHub provides migration tooling

## Stability & Maturity
- GitHub Enterprise Cloud is GitHub's most mature offering
- GHCR "currently free" is a **risk factor** — could change with 1 month notice
- Per-minute pricing has been stable; the runner pricing model is well-established

## Optimization Opportunities
1. **Self-hosted runners:** Free minutes on any plan — consider for heavy CI/CD workloads
2. **GHCR:** Take advantage while free, but budget for potential future charges
3. **Public repos:** Get unlimited free Actions minutes for open-source components
4. **Cache strategy:** 10 GB/repo included; optimize cache keys to stay within limit
5. **Artifact retention:** Reduce retention period to minimize storage consumption

## Compatibility
- Full Azure AD/Entra ID integration for SSO (Enterprise Cloud)
- GitHub Actions + Azure deployment is well-supported
- GHCR integrates directly with Azure Container Apps/AKS
- GitHub Pages can host project documentation alongside the codebase
