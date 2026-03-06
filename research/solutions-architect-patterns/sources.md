# Research Sources

## Source Credibility Assessment

### Tier 1: Primary Sources (Official Documentation)

| Source | URL | Date | Credibility | Notes |
|--------|-----|------|-------------|-------|
| MADR Official | https://adr.github.io/madr/ | 2024-09 | Tier 1 | Official MADR 4.0 documentation |
| MADR GitHub | https://github.com/adr/madr | 2024 | Tier 1 | Source code and templates |
| ADR GitHub Org | https://github.com/adr | 2024 | Tier 1 | Central ADR tooling hub |
| Spectral GitHub | https://github.com/stoplightio/spectral | 2025-03 | Tier 1 | 3k+ stars, actively maintained |
| ArchUnit | https://github.com/TNG/ArchUnit | 2025 | Tier 1 | Java architecture testing standard |
| OWASP Threat Modeling | https://owasp.org/www-project-threat-modeling/ | 2025 | Tier 1 | Industry security standard |
| C4 Model | https://c4model.com/ | 2024 | Tier 1 | Architecture visualization standard |
| AWS ADR Guidance | https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html | 2024 | Tier 1 | Enterprise practice guidance |

### Tier 2: High Credibility Sources

| Source | URL | Date | Credibility | Notes |
|--------|-----|------|-------------|-------|
| Joel Parker Henderson ADR | https://github.com/joelparkerhenderson/architecture-decision-record | 2025-03 | Tier 2 | 15.2k stars, comprehensive collection |
| ThoughtWorks Radar | https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records | 2024 | Tier 2 | Industry trend analysis |
| Decision Guardian | https://github.com/DecispherHQ/decision-guardian | 2025-03 | Tier 2 | Emerging ADR automation tool |
| ArchUnitTS | https://github.com/LukasNiessen/ArchUnitTS | 2024 | Tier 2 | TypeScript port of ArchUnit |
| DRF (Decision Reasoning Format) | https://github.com/reasoning-formats/reasoning-formats | 2024 | Tier 2 | Machine-readable decision format |

### Tier 3: Medium Credibility Sources

| Source | URL | Date | Credibility | Notes |
|--------|-----|------|-------------|-------|
| ADR Tools | https://github.com/npryce/adr-tools | 2024 | Tier 3 | CLI tooling, stable but not actively developed |
| API Stylebook | https://apistylebook.stoplight.io/ | 2024 | Tier 3 | Community ruleset collection |

---

## Cross-Referenced Claims

### ADR Format Popularity
- **MADR 4.0** released September 2024 (verified via GitHub releases)
- **Nygard format** remains widely referenced (verified via ThoughtWorks Radar 2024)
- **MADR recommended** in AWS Prescriptive Guidance (2024)

### Tool Adoption
- **Spectral**: 3k+ GitHub stars, 7.4k dependent projects (verified 2025-03)
- **ArchUnit**: Java standard, active development (verified 2025)
- **Decision Guardian**: New entrant, MIT license (verified 2025-03)

### Framework Standards
- **STRIDE**: Microsoft methodology, adopted by OWASP (verified)
- **OWASP Threat Modeling**: Project actively maintained (verified 2025)
- **PASTA**: Risk-centric methodology, used in financial services

---

## Deprecated/Legacy References

| Item | Status | Replacement |
|------|--------|-------------|
| MADR 1.x-3.x | Superseded | MADR 4.0 (Sept 2024) |
| adr-tools (npryce) | Maintenance mode | Custom tooling / Decision Guardian |
| Old ADR numbering | Deprecated | Filename-based organization |

---

## Currency Notes

- **MADR 4.0**: Released September 17, 2024 - Latest stable version
- **Spectral v6.15.0**: Released April 2025 - Latest stable
- **ArchUnit**: Continuous development, latest release 2025
- **Decision Guardian**: Very recent (2025), emerging tool

---

## Bias Assessment

### Potential Commercial Bias
- **Stoplight/Spectral**: Commercial API design platform vendor
  - Mitigation: Open source, Apache 2.0, widely adopted
- **TNG/ArchUnit**: Consulting company
  - Mitigation: Open source, MIT license, industry standard

### Community Bias
- **MADR**: Developed by academic/research community
  - Neutral, dual-licensed (MIT + CC0)
- **ADR GitHub Org**: Community-driven
  - Neutral, collaborative governance

---

## Source Reliability Hierarchy Applied

### For ADR Formats
1. **MADR official docs** (Tier 1) - Authoritative format specification
2. **AWS guidance** (Tier 1) - Enterprise adoption validation
3. **GitHub ADR org** (Tier 1) - Tooling ecosystem

### For API Governance
1. **Spectral official** (Tier 1) - Authoritative documentation
2. **API Stylebook** (Tier 2) - Real-world ruleset examples
3. **Adidas/Azure rulesets** (Tier 2) - Production validation

### For Security Frameworks
1. **OWASP official** (Tier 1) - Industry standard body
2. **Microsoft STRIDE** (Tier 2) - Original methodology source
3. **Security community** (Tier 3) - Practical implementation

---

*Source verification completed: March 6, 2026*
