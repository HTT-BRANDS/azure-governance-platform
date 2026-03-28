# Source Credibility Assessment

**Research Date:** March 27, 2026

---

## Tier 1 Sources (Highest Credibility)

### DaisyUI Official Documentation
- **URL**: https://daisyui.com/docs/
- **Type**: Official project documentation
- **Version Verified**: 5.5.19
- **Currency**: Documentation matches latest release
- **Authority**: Primary source, maintained by project creator (saadeghi)
- **Validation**: Cross-referenced with GitHub repo (2 days since last commit)
- **Bias**: None detected — open source project
- **Key Findings**: Tailwind v4 plugin syntax, `data-theme` theming, CSS-only components

### DaisyUI GitHub Repository
- **URL**: https://github.com/saadeghi/daisyui
- **Type**: Primary source code
- **Stats**: 40.6k stars, 1.6k forks, 37 issues, 19 PRs
- **Currency**: Last commit 2 days ago (March 25, 2026)
- **Release**: v5.5.19 (CHANGELOG.md updated last month)
- **License**: MIT (verified)
- **Assessment**: ⭐⭐⭐⭐⭐ Excellent — active, popular, well-maintained

### Flowbite Official Documentation
- **URL**: https://flowbite.com/docs/getting-started/quickstart/
- **Type**: Official project documentation
- **Version Verified**: 4.0
- **Currency**: Documentation current, matched to v4.x
- **Authority**: Maintained by Themesberg
- **Bias**: Commercial entity (has Pro tier), but core is open source
- **Key Findings**: Data attributes API, vanilla JS, Tailwind v4 support

### Flowbite GitHub Repository
- **URL**: https://github.com/themesberg/flowbite
- **Type**: Primary source code
- **Stats**: 9.2k stars, 851 forks, 215 issues
- **Currency**: Last release v4.0.1 (November 17, 2025 — 4 months ago)
- **License**: MIT (verified)
- **Assessment**: ⭐⭐⭐⭐ Good — active but slower cadence, commercial backing

### shadcn/ui Official Documentation
- **URL**: https://ui.shadcn.com/docs
- **Type**: Official project documentation
- **GitHub Stars**: 111k
- **Currency**: Active development, recent updates
- **Authority**: Created by shadcn (Vercel employee)
- **Key Findings**: React-only, code distribution model, TypeScript required
- **Assessment**: ⭐⭐⭐⭐⭐ Excellent source — but library is React-only

### Radix Primitives Official Site
- **URL**: https://www.radix-ui.com/primitives
- **Type**: Official project documentation
- **Authority**: Made by WorkOS
- **Currency**: Active development
- **Key Findings**: "Open source React primitives" — explicitly React-only
- **Assessment**: ⭐⭐⭐⭐⭐ Excellent source — confirmed React dependency

### Headless UI Official Site
- **URL**: https://headlessui.com/
- **Type**: Official project documentation
- **Version Verified**: 2.1
- **Authority**: Made by Tailwind Labs
- **Currency**: Active
- **Key Findings**: React and Vue only (visible in UI tabs)
- **Assessment**: ⭐⭐⭐⭐⭐ Excellent source — confirmed framework requirement

### Carbon Design System Official Documentation
- **URL**: https://carbondesignsystem.com/developing/frameworks/
- **Type**: Official IBM documentation
- **Authority**: IBM (enterprise backing)
- **Currency**: Active (Web Components v11.104.0)
- **Key Findings**: React and Web Components frameworks supported
- **Assessment**: ⭐⭐⭐⭐⭐ Excellent — enterprise-grade, IBM-maintained

### Carbon Design System GitHub Repository
- **URL**: https://github.com/carbon-design-system/carbon
- **Type**: Primary source code
- **Stats**: 9k stars, 2.1k forks, 976 issues, 85 PRs
- **Currency**: Last commit 3 days ago
- **Package**: `packages/web-components` at v11.104.0
- **License**: Apache 2.0 (verified)
- **Assessment**: ⭐⭐⭐⭐⭐ Excellent — enterprise-grade, actively maintained

### Tailwind Plus (formerly Tailwind UI) Official Site
- **URL**: https://tailwindcss.com/plus
- **Type**: Official product page
- **Authority**: Tailwind Labs (the Tailwind CSS creators)
- **Currency**: Active, recently rebranded from "Tailwind UI"
- **Pricing Verified**: $299 personal, $979 team (one-time)
- **Key Findings**: HTML + React + Vue blocks, 500+ components
- **Assessment**: ⭐⭐⭐⭐⭐ Excellent — authoritative source

---

## Tier 2 Sources (High Credibility)

### GitHub Release Pages
- Flowbite releases: Verified v4.0.1 date (Nov 17, 2025) and changelog
- DaisyUI releases: Verified v5.5.19 via CHANGELOG.md
- Carbon releases: Verified v11.104.0 via commit history

### Carbon Web Components Storybook
- **URL**: https://web-components.carbondesignsystem.com/
- **Type**: Interactive component demos
- **Assessment**: ⭐⭐⭐⭐ Good — official demo instance

---

## Tier 3 Sources (Not Used but Noted)

The following sources were NOT relied upon for this analysis:
- Blog posts comparing component libraries (often outdated or biased)
- Stack Overflow answers about library compatibility (may be outdated)
- YouTube tutorials (may not reflect latest versions)
- Medium/Dev.to articles (varying quality, often promotional)

---

## Cross-Reference Validation

| Claim | Source 1 | Source 2 | Validated? |
|-------|----------|----------|------------|
| DaisyUI is CSS-only | daisyui.com docs | GitHub source code | ✅ Yes |
| DaisyUI supports Tailwind v4 | daisyui.com/docs/install | package.json (v5.x) | ✅ Yes |
| Flowbite uses vanilla JS | flowbite.com quickstart | GitHub source | ✅ Yes |
| shadcn/ui requires React | ui.shadcn.com installation | dependency list (lucide-react) | ✅ Yes |
| Headless UI is React/Vue only | headlessui.com | GitHub README | ✅ Yes |
| Radix is React-only | radix-ui.com | npm package description | ✅ Yes |
| Carbon has Web Components | carbondesignsystem.com | GitHub packages/web-components | ✅ Yes |
| Tailwind Plus costs $299/$979 | tailwindcss.com/plus pricing | Pricing page screenshot | ✅ Yes |
| Tailwind Plus has HTML blocks | tailwindcss.com/plus/ui-blocks | Product page (HTML/React/Vue tabs) | ✅ Yes |
