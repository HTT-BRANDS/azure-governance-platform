# Sources & Credibility Assessment

**Research Date:** March 27, 2026

---

## Primary Sources (Tier 1 — Official Vendor Websites)

### 1. CloudHealth by Broadcom
- **URL**: https://www.broadcom.com/products/software/finops/cloudhealth
- **Type**: Official product page
- **Credibility**: ✅ High — Official vendor website
- **Currency**: Active, February 2026 product enhancements blog post visible
- **Key Data Extracted**: Feature list (Perspectives, FlexOrgs, Reports, Optimization Dashboard, Intelligent Assist, Smart Summary, Asset Explorer, Realized Savings), MSP positioning
- **Bias**: Marketing material — features may be overstated
- **Note**: MSP-specific page (cloudhealthtech.com/solutions/managed-service-providers) now redirects to main Broadcom page. Suggests possible de-emphasis of MSP tier.

### 2. Spot.io / NetApp
- **URL**: https://spot.io → redirects to https://www.flexera.com
- **URL**: https://www.netapp.com/cloud-services/spot/ → "Access Denied"
- **Type**: Redirect/unavailable
- **Credibility**: ✅ High — Direct evidence of product discontinuation
- **Currency**: As of March 2026
- **Key Finding**: Product appears discontinued or divested to Flexera
- **Validation**: Both the spot.io domain redirect and NetApp access denial confirm discontinuation

### 3. IBM Cloudability (Apptio)
- **URL**: https://www.apptio.com/products/cloudability/
- **Type**: Official product page
- **Credibility**: ✅ High — Official vendor website
- **Currency**: Active, showing Winter 2026 TrustRadius badge
- **Key Data Extracted**: Feature overview, analyst badges (Forrester Wave Leader 2024, Gartner MQ, FinOps Certified, TrustRadius Buyer's Choice 2026), multi-cloud dashboard, team-based views, chargeback capabilities
- **Bias**: Marketing material; claims "reduce cloud unit costs by 30%+" should be treated as best-case
- **Note**: Free trial available for hands-on evaluation

### 4. Vantage
- **URL**: https://www.vantage.sh
- **Pricing URL**: https://www.vantage.sh/pricing
- **Features URL**: https://www.vantage.sh/features
- **Type**: Official product page
- **Credibility**: ✅ High — Official vendor website with transparent pricing
- **Currency**: Active, "New: Introducing Vantage in ChatGPT" banner visible
- **Key Data Extracted**: Complete pricing tiers (Free/$30/$200/Custom), feature matrix by tier, integration list (27+ providers including Azure), feature details (Virtual Tagging, Automated Waste Detection, Kubernetes, FinOps as Code)
- **Bias**: Low — pricing transparency is a positive credibility signal
- **Strength**: Only vendor with fully transparent pricing

### 5. Nerdio
- **URL**: https://getnerdio.com
- **Products URL**: https://getnerdio.com/nerdio-manager/
- **MSP URL**: https://getnerdio.com/nerdio-manager/msp/
- **Type**: Official product page
- **Credibility**: ✅ High — Official vendor website
- **Currency**: Active, NerdioCon 2026 conference promoted
- **Key Data Extracted**: Two products (Enterprise + MSP), AVD/Windows 365/Intune/M365 focus, MSP multi-customer management, device compliance filtering
- **Bias**: Marketing material; product is narrower than the "All-in-one Microsoft Cloud management" tagline suggests
- **Note**: Pricing not publicly available; requires demo/sales engagement

### 6. CoreStack
- **URL**: https://www.corestack.io
- **Governance URL**: https://www.corestack.io/solutions/corestack-governance/
- **Type**: Official product page
- **Credibility**: ✅ High — Official vendor website
- **Currency**: Active, FinOps white papers promoted
- **Key Data Extracted**: Three modules (FinOps+, SecOps, CloudOps), AI-powered governance, enterprise clients (Capgemini, De Beers, Deloitte, EMAAR, GE Health), multi-cloud support, ten governance facets
- **Bias**: Enterprise marketing; "Agentic AI-Powered" branding may overstate AI capabilities
- **Note**: Partner program available for MSPs

### 7. Komiser (GitHub)
- **URL**: https://github.com/mlabouardy/komiser (redirected from tailwarden/komiser)
- **Type**: Source code repository
- **Credibility**: ✅ High — Primary source (actual code and community metrics)
- **Currency**: Last code update ~2 years ago for most directories; README updated 6 months ago
- **Key Data Extracted**: 4.1K stars, 454 forks, 2,986 commits, 63+ contributors, Go/TypeScript stack, ELv2 license (changed from MIT), 220 open issues, 41 open PRs, supports AWS/Azure/GCP/DigitalOcean/Linode/OCI/Tencent/Civo
- **Bias**: None — direct repository data
- **Concern**: Declining development activity suggests possible project abandonment

### 8. OpenCost
- **URL**: https://opencost.io
- **Type**: Official project website
- **Credibility**: ✅ High — CNCF Sandbox project
- **Currency**: Active, Live Demo available
- **Key Data Extracted**: 6.4K GitHub stars, Kubernetes-focused, container-level cost allocation, Azure/AWS/GCP billing API integration, vendor-neutral, Apache 2.0 license
- **Bias**: Low — open source project with CNCF backing
- **Limitation**: Exclusively Kubernetes-focused, not general cloud governance

### 9. Infracost
- **URL**: https://www.infracost.io
- **Pricing URL**: https://www.infracost.io/pricing/
- **Type**: Official product page
- **Credibility**: ✅ High — Official vendor website with transparent pricing
- **Currency**: Active, new whitepaper promoted
- **Key Data Extracted**: CI/CD integration focus, GitHub/Azure Repos support, pricing (Free/$1K/Custom), governance scores, FinOps best practice scanning
- **Bias**: Low — transparent pricing and clear scope definition

---

## Source Gaps & Limitations

### Information Not Available from Primary Sources
1. **Exact pricing for CloudHealth, Cloudability, CoreStack, Nerdio** — all require sales engagement
2. **Azure Lighthouse compatibility details** — no vendor discusses Lighthouse support specifically
3. **Real-world MSP user reviews at 4-5 tenant scale** — most reviews are from 50+ account enterprises
4. **Spot.io disposition details** — unclear if product was acquired by Flexera or simply discontinued

### Search Engine Limitations
- Google and DuckDuckGo both triggered CAPTCHA challenges, preventing search-based cross-referencing
- All data sourced directly from vendor websites, which introduces marketing bias
- Independent analyst reports (Gartner, Forrester) are paywalled

### Recommended Follow-Up Research
1. **G2/TrustRadius reviews** — for real user pricing data and MSP experience reports
2. **Gartner Magic Quadrant for Cloud Financial Management Tools** — for analyst pricing benchmarks
3. **Reddit r/msp and r/azure** — for community experience with small-scale MSP tools
4. **Azure Marketplace** — for any governance tools with Lighthouse integration
5. **Direct vendor demos** — for actual pricing quotes at 4-5 tenant scale
