# GitHub Enterprise Cloud Pricing Research

**Research Date:** April 15, 2026
**Researcher:** web-puppy-e2d609
**Sources:** All Tier 1 (Official GitHub documentation and pricing pages)

---

## Executive Summary

GitHub Enterprise Cloud costs **$21 USD/user/month** (starting at). For a 7-seat organization, the monthly cost would be **$147/month** before any overage charges. The plan includes **50,000 GitHub Actions minutes/month** and **50 GB of shared storage**. A critical finding: **GitHub Container Registry (GHCR) storage is currently free** and does not count against the shared storage quota.

---

## 1. Monthly Cost Per Seat

| Plan | Price |
|------|-------|
| **GitHub Enterprise Cloud** | **$21 USD per user/month** (starting at) |
| GitHub Team (for comparison) | $4 USD per user/month |
| GitHub Free | $0 |

> **Source:** [github.com/pricing](https://github.com/pricing) — Tier 1 (official pricing page)
> **Verified:** April 15, 2026

---

## 2. GitHub Actions Minutes Included (Linux Runners)

| Plan | Minutes/Month | Artifact Storage | Cache Storage |
|------|--------------|-----------------|---------------|
| GitHub Free (org) | 2,000 | 500 MB | 10 GB/repo |
| GitHub Team | 3,000 | 2 GB | 10 GB/repo |
| **GitHub Enterprise Cloud** | **50,000** | **50 GB** | **10 GB/repo** |

- Minutes are for **standard GitHub-hosted runners** on **private repositories**
- Public repositories: **unlimited free minutes** on standard runners
- Minutes reset monthly; storage resets to zero accrual each billing cycle
- Cache storage limit is **per repository** (10 GB included per repo, all plans)

> **Source:** [GitHub Actions billing docs](https://docs.github.com/en/billing/concepts/product-billing/github-actions) — Tier 1

---

## 3. Additional Minute Costs (Overage)

Per-minute rates for standard GitHub-hosted runners beyond included quota:

| Runner Type | Billing SKU | Per-Minute Rate |
|-------------|------------|----------------|
| **Linux 1-core (x64)** | `actions_linux_slim` | **$0.002** |
| **Linux 2-core (x64)** | `actions_linux` | **$0.006** |
| Linux 2-core (arm64) | `actions_linux_arm` | $0.005 |
| Windows 2-core (x64) | `actions_windows` | $0.010 |
| Windows 2-core (arm64) | `actions_windows_arm` | $0.010 |
| macOS 3/4-core (M1/Intel) | `actions_macos` | $0.062 |

### Larger Linux Runners (x64) — Always Billed, Even With Quota

| Cores | Per-Minute Rate |
|-------|----------------|
| 4-core | $0.012 |
| 8-core | $0.022 |
| 16-core | $0.042 |
| 32-core | $0.082 |
| 64-core | $0.162 |
| 96-core | $0.252 |

**Important:** Larger runners are **always charged**, even for public repos or when you have quota remaining.

> **Source:** [GitHub Actions billing docs](https://docs.github.com/en/billing/concepts/product-billing/github-actions) + [Pricing Calculator](https://github.com/pricing/calculator?feature=actions) — Tier 1

---

## 4. GHCR (GitHub Container Registry) Storage

### ⚡ CRITICAL FINDING: GHCR IS CURRENTLY FREE

> **"Billing for container image storage: Container image storage and bandwidth for the Container registry is currently free. If you use Container registry, you'll be informed at least one month in advance of any change to this policy."**

— [GitHub Packages billing docs](https://docs.github.com/en/billing/concepts/product-billing/github-packages)

### What this means:
- GHCR storage: **$0 (free)**
- GHCR bandwidth: **$0 (free)**
- GHCR does **NOT** count against the shared 50 GB storage quota
- GitHub will provide **at least 1 month notice** before this changes

### Non-Container Packages Storage (npm, Maven, NuGet, etc.)

These DO count against the shared storage pool:

| Plan | Shared Storage | Data Transfer/Month |
|------|---------------|-------------------|
| GitHub Free (org) | 500 MB | 1 GB |
| GitHub Team | 2 GB | 10 GB |
| **GitHub Enterprise Cloud** | **50 GB** | **100 GB** |

**⚠️ Storage is shared** across: GitHub Packages + Actions artifacts + Actions caches

> **Source:** [GitHub Packages billing docs](https://docs.github.com/en/billing/concepts/product-billing/github-packages) — Tier 1

---

## 5. Additional Storage Costs (Overage)

### Cache Storage Overage
- **$0.07 per GiB per month** (explicitly stated in docs)
- Applies when a repository exceeds 10 GB cache limit

### Artifact & Packages Storage Overage
- Billed based on **hourly usage** calculated as **GB-Hours**, converted to **GB-Months**
- The docs do **not** state an explicit $/GB/month rate — they refer to the [pricing calculator](https://github.com/pricing/calculator)
- Storage is calculated as: `(GB used × hours stored) / (hours in month)` = GB-Months billed
- ⚠️ **Note:** The exact per-GB-Month dollar rate for artifact/Packages storage was not explicitly listed in the documentation reviewed. Use the official [GitHub pricing calculator](https://github.com/pricing/calculator) for exact overage costs, or contact GitHub Sales.

> **Source:** [GitHub Actions billing docs](https://docs.github.com/en/billing/concepts/product-billing/github-actions) — Tier 1

---

## 6. GitHub Pages Hosting

### Included? YES — with limits

**Availability by plan:**
- Free / Free for orgs: **Public repositories only**
- Team / Enterprise Cloud: **Public AND private repositories** ✅

### Usage Limits

| Limit | Value |
|-------|-------|
| Published site size | **≤ 1 GB** |
| Source repo recommended size | ≤ 1 GB |
| Bandwidth | **100 GB/month** (soft limit) |
| Builds per hour | 10 (soft limit; does NOT apply with Actions workflows) |
| Deployment timeout | 10 minutes |
| Sites per account | 1 user/org site + unlimited project sites |

### Important Notes:
- The bandwidth limit is a **soft limit** — GitHub contacts you if exceeded rather than hard-blocking
- Standard GitHub-hosted runner usage for Pages builds is **free** (does not consume Actions minutes)
- **Not allowed** for: commercial SaaS, e-commerce, or sensitive transactions
- Rate limiting (HTTP 429) may apply under heavy load

> **Source:** [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) — Tier 1

---

## 7. Enterprise Cloud vs Team — 7-Seat Comparison

### Monthly Cost

| | Team (7 seats) | Enterprise Cloud (7 seats) | Difference |
|---|---|---|---|
| **Per-seat cost** | $4/user/mo | $21/user/mo | +$17/user |
| **Monthly total** | **$28/month** | **$147/month** | **+$119/month** |
| **Annual total** | $336/year | $1,764/year | +$1,428/year |

### Included Resources

| Resource | Team | Enterprise Cloud | Enterprise Advantage |
|----------|------|-----------------|---------------------|
| Actions minutes/mo | 3,000 | **50,000** | **16.7× more** |
| Shared storage | 2 GB | **50 GB** | **25× more** |
| Packages data transfer | 10 GB/mo | **100 GB/mo** | **10× more** |
| Cache storage | 10 GB/repo | 10 GB/repo | Same |

### Feature Differences (Enterprise Cloud extras)

| Feature | Team | Enterprise Cloud |
|---------|:----:|:----------------:|
| SAML SSO | ❌ | ✅ |
| Enterprise Managed Users | ❌ | ✅ |
| SCIM provisioning | ❌ | ✅ |
| Data residency | ❌ | ✅ |
| Audit Log API | ❌ | ✅ |
| Advanced auditing | ❌ | ✅ |
| GitHub Connect | ❌ | ✅ |
| Environment protection rules | ❌ | ✅ |
| SOC1/SOC2 type 2 reports | ❌ | ✅ |
| FedRAMP Tailored ATO | ❌ | ✅ |
| Multi-org Enterprise Account | ❌ | ✅ |
| Premium support (add-on) | ❌ | ✅ (exclusive) |
| Repository rules | ✅ | ✅ |
| Code owners | ✅ | ✅ |
| Required reviewers | ✅ | ✅ |
| Pages & Wikis | ✅ | ✅ |
| Draft PRs | ✅ | ✅ |
| GitHub Codespaces | ✅ | ✅ |

### Recommendation for 7 Seats

**Choose Team ($28/mo) if:**
- You don't need SAML SSO or SCIM provisioning
- 3,000 Actions minutes/month is sufficient
- 2 GB shared storage meets your needs
- No compliance requirements (SOC2, FedRAMP)

**Choose Enterprise Cloud ($147/mo) if:**
- You need SSO/SCIM for identity management
- You need >3,000 Actions minutes (Enterprise gets 50,000)
- You need compliance certifications
- You want centralized policy management across orgs
- The 50 GB storage pool is needed for heavy CI/CD

---

## Project Context: azure-governance-platform

This project uses:
- Docker/GHCR for container images → **GHCR is currently free** ✅
- GitHub Actions for CI/CD → Enterprise gives **50,000 min/mo** (vs Team's 3,000)
- GitHub Pages for documentation → **Included with both plans**
- Python/FastAPI backend with Azure deployment

For this specific project, the **GHCR being free** is a major cost benefit, and the **50,000 Actions minutes** on Enterprise Cloud provides substantial CI/CD headroom.
