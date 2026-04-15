# Source Credibility Assessment

## All Sources — Tier 1 (Highest Reliability)

Every source used in this research is an official GitHub primary source.

---

### Source 1: GitHub Pricing Page
- **URL:** https://github.com/pricing
- **Type:** Official vendor pricing page
- **Authority:** ⭐⭐⭐⭐⭐ — Primary source, official GitHub
- **Currency:** Live page, verified April 15, 2026
- **Bias:** Vendor page (marketing), but pricing numbers are contractual
- **Data extracted:** Plan prices ($0/$4/$21), feature comparison, included resources
- **Cross-validated with:** GitHub docs billing pages ✅

### Source 2: GitHub Actions Billing Documentation
- **URL:** https://docs.github.com/en/billing/concepts/product-billing/github-actions
- **Type:** Official documentation
- **Authority:** ⭐⭐⭐⭐⭐ — Primary source, official GitHub docs
- **Currency:** Version: "Free, Pro, & Team" — current as of April 2026
- **Bias:** None (technical documentation)
- **Data extracted:** Included minutes/storage per plan, per-minute overage rates, cache storage overage ($0.07/GiB/mo), storage billing methodology
- **Cross-validated with:** Pricing page and calculator ✅

### Source 3: GitHub Packages Billing Documentation
- **URL:** https://docs.github.com/en/billing/concepts/product-billing/github-packages
- **Type:** Official documentation
- **Authority:** ⭐⭐⭐⭐⭐ — Primary source, official GitHub docs
- **Currency:** Current as of April 2026
- **Bias:** None (technical documentation)
- **Data extracted:** Storage/transfer quotas per plan, GHCR free status, shared storage policy
- **Cross-validated with:** Actions billing page confirms shared storage ✅

### Source 4: GitHub Pages Limits Documentation
- **URL:** https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- **Type:** Official documentation
- **Authority:** ⭐⭐⭐⭐⭐ — Primary source, official GitHub docs
- **Currency:** Current as of April 2026
- **Bias:** None (technical documentation)
- **Data extracted:** Site size limit (1 GB), bandwidth soft limit (100 GB/mo), build limits
- **Cross-validated with:** Pricing page feature comparison ✅

### Source 5: GitHub Pricing Calculator
- **URL:** https://github.com/pricing/calculator?feature=actions
- **Type:** Official pricing tool
- **Authority:** ⭐⭐⭐⭐⭐ — Primary source, official GitHub
- **Currency:** Live tool, April 2026
- **Bias:** None (interactive calculator)
- **Data extracted:** Full runner pricing table (all core sizes), confirmation of per-minute rates
- **Cross-validated with:** Actions billing docs ✅

### Source 6: GitHub Pricing Feature Comparison
- **URL:** https://github.com/pricing#compare-features
- **Type:** Official feature comparison
- **Authority:** ⭐⭐⭐⭐⭐ — Primary source, official GitHub
- **Currency:** Live page, April 2026
- **Bias:** Marketing-oriented presentation but factual feature data
- **Data extracted:** Side-by-side plan comparison confirming Actions minutes, Packages storage, feature availability
- **Cross-validated with:** All other sources ✅

---

## Sources NOT Used (and why)

- **Third-party blogs/articles:** Not needed; all data available from primary sources
- **Stack Overflow:** Not consulted; pricing data is best from vendor directly
- **Search engines:** Google, DuckDuckGo, and Bing all returned CAPTCHA challenges during automated research

## Known Data Gaps

1. **Artifact/Packages storage overage rate ($/GB/month):** Not explicitly stated in current documentation. Only cache storage overage is documented ($0.07/GiB/month). The docs reference the pricing calculator for exact costs.
2. **Data transfer overage rate:** Not explicitly stated per-GB in current documentation.
3. **Volume discounts:** Enterprise Cloud pricing says "starting at" $21, suggesting potential negotiated pricing for larger organizations.
