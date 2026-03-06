# Solutions Architect Patterns for Automated/AI-Assisted Development

**Research Date:** January 2025  
**Scope:** Architecture Decision Records, Automated Architecture Review, Security-by-Design, API Governance, Technology Selection Frameworks  
**Target Context:** Azure Multi-Tenant Governance Platform (Python/FastAPI)

---

## Executive Summary

This research synthesizes current best practices (2024-2025) for implementing a "Solutions Architect" role in automated/AI-assisted development pipelines. The findings are contextualized for a Python/FastAPI-based Azure governance platform.

### Key Findings

1. **ADR Formats**: MADR 4.0 is now the leading format, emphasizing lightweight documentation with optional sections. Nygard remains popular for simpler contexts.

2. **Automated Architecture Compliance**: Tools like ArchUnit (Java), Spectral (API linting), and fitness functions provide measurable architecture governance. The "Decision Guardian" pattern integrates ADRs into PR workflows.

3. **Security-by-Design**: STRIDE and OWASP Threat Modeling remain industry standards. Automated threat modeling tools are emerging but require human oversight.

4. **API Governance**: Spectral is the dominant OpenAPI linting tool with extensive ruleset ecosystem. Azure, Adidas, and major tech companies publish their Spectral configurations.

5. **Technology Selection**: ATAM (Architecture Tradeoff Analysis Method) and fitness functions provide structured evaluation. Cost-benefit analysis remains essential for cloud-native decisions.

---

## Quick Reference: Recommended Stack for Azure Governance Platform

| Concern | Recommended Tool/Pattern | Integration Approach |
|---------|---------------------------|---------------------|
| ADR Documentation | MADR 4.0 + adr-tools | `/docs/decisions/` directory |
| Architecture Compliance | ArchUnit concepts + Python linters | CI pipeline gates |
| API Design Governance | Spectral | Pre-commit hooks + CI |
| Security Modeling | OWASP Threat Modeling + STRIDE | Design phase checkpoints |
| Technology Evaluation | Fitness functions + ATAM-lite | ADR decision drivers section |

---

## Research Structure

- [`sources.md`](./sources.md) - All sources with credibility assessments
- [`analysis/`](./analysis/) - Multi-dimensional analysis by topic
  - [`adr-formats.md`](./analysis/adr-formats.md) - ADR templates and tooling comparison
  - [`automated-compliance.md`](./analysis/automated-compliance.md) - Automated architecture review tools
  - [`security-frameworks.md`](./analysis/security-frameworks.md) - Security-by-design integration
  - [`api-governance.md`](./analysis/api-governance.md) - API design standards and linting
  - [`technology-selection.md`](./analysis/technology-selection.md) - Evaluation frameworks
- [`recommendations.md`](./recommendations.md) - Project-specific action items
- [`raw-findings/`](./raw-findings/) - Extracted content from sources

---

## Research Methodology

**Sources Evaluated:**
- Official project documentation (MADR, ArchUnit, Spectral)
- GitHub repositories with >1000 stars
- OWASP official resources
- ThoughtWorks Technology Radar
- AWS/Azure prescriptive guidance

**Source Reliability:**
- Tier 1 (Primary): GitHub official repos, OWASP, vendor documentation
- Tier 2 (High): Established tech publications, industry expert blogs
- Tier 3 (Medium): Community forums with validated answers

---

## Context: Target Project

**Project:** Azure Multi-Tenant Governance Platform  
**Stack:** Python 3.11+, FastAPI, HTMX, SQLite/Azure SQL, Azure SDK  
**Domain:** Cloud governance, cost optimization, compliance monitoring  
**Team Size:** Small team (<10 developers)  
**Deployment:** Azure App Service / Container Apps

This context informed the prioritization of recommendations—favoring lightweight, low-overhead solutions suitable for small teams while maintaining enterprise-grade quality.

---

*Last Updated: January 2025*  
*Research ID: web-puppy-122f44*
