# Source Credibility Assessment

**Research Date:** March 6, 2026

## Tier 1 Sources (Highest Credibility)

### W3C - Web Content Accessibility Guidelines 2.2
- **URL:** https://www.w3.org/TR/WCAG22/
- **Type:** Official Standard
- **Last Updated:** October 5, 2023 (W3C Recommendation)
- **Credibility Assessment:**
  - **Authority:** Official W3C standard - the authoritative source for web accessibility
  - **Currency:** Current as of October 2023, stable recommendation status
  - **Validation:** Primary source, referenced by all accessibility tools
  - **Bias:** None - neutral technical standard
  - **Primary/Secondary:** Primary source

### W3C - What's New in WCAG 2.2
- **URL:** https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- **Type:** Official Documentation
- **Last Updated:** October 5, 2023
- **Credibility Assessment:**
  - **Authority:** W3C WAI (Web Accessibility Initiative)
  - **Currency:** Current, last updated 2023
  - **Validation:** Cross-referenced with WCAG 2.2 spec
  - **Bias:** None - educational documentation
  - **Primary/Secondary:** Primary source

### Deque Systems - axe-core
- **URL:** https://www.deque.com/axe/axe-core/
- **Type:** Official Product Documentation
- **Version:** 4.11.1 (as of research date)
- **Credibility Assessment:**
  - **Authority:** Deque is the creator/maintainer of axe-core
  - **Currency:** Active development, latest release 4.11.1
  - **Validation:** Cross-referenced with GitHub repository
  - **Bias:** Commercial interest in accessibility tools, but data is factual
  - **Primary/Secondary:** Primary source for tool capabilities

### axe-core GitHub Repository
- **URL:** https://github.com/dequelabs/axe-core
- **Type:** Open Source Repository
- **License:** MPL 2.0
- **Credibility Assessment:**
  - **Authority:** Official source code repository
  - **Currency:** Active development (400+ contributors, 6.9k stars)
  - **Validation:** Can verify all claims through code
  - **Bias:** None - open source
  - **Primary/Secondary:** Primary source

### California Attorney General - CCPA Guidelines
- **URL:** https://oag.ca.gov/privacy/ccpa
- **Type:** Government Regulation
- **Last Updated:** March 13, 2024
- **Credibility Assessment:**
  - **Authority:** Official state regulation
  - **Currency:** Updated March 2024 with CPRA amendments
  - **Validation:** Legal document, legally binding
  - **Bias:** None - government regulation
  - **Primary/Secondary:** Primary source

## Tier 2 Sources (High Credibility)

### Google Material Design 3
- **URL:** https://m3.material.io/
- **Type:** Design System Documentation
- **Last Updated:** 2025 (M3 Expressive launched)
- **Credibility Assessment:**
  - **Authority:** Google's official design system
  - **Currency:** Active development, M3 Expressive recently added
  - **Validation:** Used by millions of applications
  - **Bias:** Promotes Google's design philosophy
  - **Primary/Secondary:** Primary source for Material Design

### IBM Carbon Design System
- **URL:** https://carbondesignsystem.com/
- **Type:** Open Source Design System
- **Version:** Last updated March 6, 2026 (as per site)
- **Credibility Assessment:**
  - **Authority:** IBM's official design system, widely adopted
  - **Currency:** Active development with accessibility focus
  - **Validation:** Open source, community contributions
  - **Bias:** IBM-centric but principles are universal
  - **Primary/Secondary:** Primary source

### Salesforce Lightning Design System 2
- **URL:** https://www.lightningdesignsystem.com/
- **Type:** Design System Documentation
- **Version:** Winter '26 v2.3.0
- **Credibility Assessment:**
  - **Authority:** Salesforce's official design system
  - **Currency:** Winter '26 release (21 days old at research time)
  - **Validation:** Used across Salesforce ecosystem
  - **Bias:** Salesforce-specific but patterns are transferable
  - **Primary/Secondary:** Primary source

### Pa11y
- **URL:** https://pa11y.org/
- **Type:** Open Source Tool Documentation
- **Credibility Assessment:**
  - **Authority:** Established open-source accessibility testing tool
  - **Currency:** Copyright 2025 on site
  - **Validation:** Widely used in CI/CD pipelines
  - **Bias:** None - open source
  - **Primary/Secondary:** Primary source

## Tier 3 Sources (Medium Credibility)

### Web.dev Accessibility Section
- **URL:** https://web.dev/accessibility
- **Type:** Educational Resource
- **Credibility Assessment:**
  - **Authority:** Google's web development resource
  - **Currency:** Regularly updated
  - **Validation:** Cross-references with W3C standards
  - **Bias:** Google ecosystem focus
  - **Primary/Secondary:** Secondary source (interprets standards)

## Source Reliability Summary

| Source | Tier | Authority | Currency | Validation | Bias | Type |
|--------|------|-----------|----------|------------|------|------|
| W3C WCAG 2.2 | 1 | Highest | Current | Self | None | Primary |
| axe-core (Deque) | 1 | High | Current | Verified | Low | Primary |
| CCPA Guidelines | 1 | Highest | Current | Legal | None | Primary |
| Material Design | 2 | High | Current | Widely used | Low | Primary |
| IBM Carbon | 2 | High | Current | Open source | Low | Primary |
| Salesforce SLDS | 2 | High | Current | Verified | Low | Primary |
| Pa11y | 2 | Medium | Current | Open source | None | Primary |
| web.dev | 3 | Medium | Current | Cross-ref | Medium | Secondary |

## Research Methodology

### Verification Process
1. **Cross-Reference:** All claims verified against multiple sources
2. **Version Check:** Confirmed current versions and dates
3. **Authority Validation:** Prioritized official documentation over third-party interpretations
4. **Currency Check:** Ensured information is from 2023-2026 timeframe
5. **Bias Assessment:** Evaluated commercial vs. neutral sources

### Gaps in Research
- **Lighthouse-specific coverage gaps:** Need deeper analysis
- **Privacy-by-Design UI patterns:** Limited authoritative sources on implementation
- **Frontend-backend accessibility contracts:** Emerging area with few established patterns
- **Design system governance metrics:** Limited quantitative data on adoption

### Recommendations for Further Research
1. Review axe-core GitHub issues for known coverage gaps
2. Analyze Lighthouse accessibility scoring algorithm
3. Research GPC (Global Privacy Control) implementation patterns
4. Investigate ARIA-live regions for error messaging patterns
5. Study design system versioning strategies from major organizations

---

*Sources assessed on March 6, 2026. Technology and regulations evolve - verify currency before implementation.*
