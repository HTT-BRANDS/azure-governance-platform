# Cost Optimization Research — Azure Governance Platform

**Date:** 2026-03-27
**Researcher:** web-puppy-d7a84d
**Current Cost:** ~$73/mo ($35 prod + $38 staging) | ~$880/year
**Workload Profile:** 10-30 non-concurrent users, 6.25MB database, FastAPI + HTMX + Docker

---

## Executive Summary

**The platform can be reduced from $73/mo to as low as $0-5/mo (93-100% savings)** by leveraging Azure free tiers aggressively, or to **$15-18/mo (75% savings)** with minimal architectural changes.

### Key Findings

| Rank | Architecture | Monthly Cost | Savings | Risk | Effort |
|------|-------------|-------------|---------|------|--------|
| 🥇 | **Container Apps (scale-to-zero) + SQL Free Tier + GHCR** | **$0-5** | 93-100% | Medium | Medium |
| 🥈 | **Optimized Current (SQL Free + GHCR + kill staging)** | **$15-18** | 75% | **Low** | **Low** |
| 🥉 | **VPS (Hetzner/DigitalOcean)** | **$4-6** | 92% | Medium-High | Medium |
| 4 | GCP Cloud Run + Firestore | $0-10 | 86-100% | High | High |
| 5 | Azure Functions Consumption | $1-3 | 96% | High | **Very High** |
| 6 | AWS App Runner + DynamoDB | $7-15 | 79-90% | High | High |

### 🏆 Recommended Path: Two-Phase Approach

**Phase 1 (This week, saves ~$58/mo):** Eliminate staging, switch SQL to free tier, migrate ACR → GHCR
- $73 → $15/mo with minimal risk and effort

**Phase 2 (Next month, saves additional ~$10-15/mo):** Migrate App Service → Container Apps consumption
- $15 → $0-5/mo with moderate effort

---

## Detailed Findings

See:
- [analysis.md](./analysis.md) — Multi-dimensional analysis of each option
- [sources.md](./sources.md) — Source credibility assessments
- [recommendations.md](./recommendations.md) — Prioritized action plan with implementation steps
