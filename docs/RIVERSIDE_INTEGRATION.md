# Riverside Compliance Integration Guide

This guide provides comprehensive documentation for integrating Riverside Company compliance tracking into the Azure Governance Platform.

## Table of Contents

1. [Overview](#overview)
2. [Compliance Requirements](#compliance-requirements)
3. [Platform Integration](#platform-integration)
4. [API Usage Examples](#api-usage-examples)
5. [Dashboard Walkthrough](#dashboard-walkthrough)
6. [Data Sync Configuration](#data-sync-configuration)
7. [Evidence Upload Process](#evidence-upload-process)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Background

Riverside Company is a compliance initiative requiring Azure governance maturity scoring to reach 3.0/5.0 by **July 8, 2026**. This represents a critical business requirement with significant financial implications:

- **Financial Risk**: $4M potential loss from a single breach
- **Current State**: 2.4/5.0 overall maturity
- **MFA Gap**: 70% of 1,992 users unprotected
- **Timeline**: ~160 days remaining

### Tenants in Scope

| Tenant Code | Name | Type | MFA Status |
|-------------|------|------|------------|
| HTT | HTT | Riverside | 30% |
| BCC | BCC | Riverside | 30% |
| FN | FN | Riverside | 30% |
| TLL | TLL | Riverside | 30% |
| DCE | DCE | Standalone | N/A |

---

## Compliance Requirements

### Maturity Domains

The compliance framework evaluates five maturity domains:

1. **Identity & Access Management (IAM)** - Current: 2.2/5.0
2. **Governance & Security (GS)** - Current: 2.5/5.0
3. **Data Security (DS)** - Current: 2.6/5.0
4. **Security Operations** - Current: 2.3/5.0
5. **Platform Security** - Current: 2.4/5.0

### Key Requirements Categories

| Category | Requirements | Priority |
|----------|-------------|----------|
| IAM | MFA, PAM, Conditional Access | P0 |
| GS | Security Team, Training, Policies | P0 |
| DS | Classification, Encryption | P1 |
| Device | MDM, EDR, Encryption | P0 |

### Critical Gaps

The following gaps require immediate attention:

1. **IAM-12: Universal MFA Enforcement** - 30% → 100%
2. **GS-10: Dedicated Security Team** - Not Started
3. **IAM-03: Privileged Access Management** - Not Started
4. **IAM-08: Conditional Access Policy** - 40% → 100%
5. **DS-02: Data Classification** - Not Started
6. **GS-05: Security Awareness Training** - 25% → 100%
7. **IAM-15: Service Account Management** - Not Started
8. **DS-05: Encryption at Rest** - Not Started

---

## Platform Integration

### Installation

1. Ensure the platform is installed per [README.md](../README.md)
2. Copy `.env.example` to `.env`
3. Enable Riverside compliance:

```bash
# Add to .env
RIVERSIDE_COMPLIANCE_ENABLED=true
RIVERSIDE_DEADLINE_DATE=2026-07-08
RIVERSIDE_MFA_TARGET=100
RIVERSIDE_MATURITY_TARGET=3.0
```

4. Run database migrations:

```bash
python -m app.models.riverside create_tables
```

### Verification

```bash
# Test that Riverside endpoints are accessible
curl http://localhost:8000/api/v1/riverside/summary

# Should return:
# {"overall_maturity": 2.4, "days_remaining": 160, ...}
```

---

## API Usage Examples

### Executive Summary

```bash
curl -X GET "http://localhost:8000/api/v1/riverside/summary" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "overall_maturity": 2.4,
  "target_maturity": 3.0,
  "days_remaining": 160,
  "deadline": "2026-07-08",
  "financial_risk": 4000000,
  "mfa_coverage_percent": 30,
  "mfa_unprotected_users": 1358,
  "critical_gaps_count": 8,
  "requirements_compliant": 45,
  "requirements_total": 72,
  "threat_beta_score": 1.04
}
```

### MFA Status

```bash
# All tenants
curl -X GET "http://localhost:8000/api/v1/riverside/mfa-status" \
  -H "Authorization: Bearer $TOKEN"

# Single tenant
curl -X GET "http://localhost:8000/api/v1/riverside/mfa-status/HTT" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "summary": {
    "total_users": 1992,
    "mfa_enabled": 634,
    "mfa_disabled": 1358,
    "coverage_percent": 30
  },
  "by_tenant": [
    {
      "tenant_id": "htt",
      "tenant_name": "HTT",
      "total_users": 498,
      "mfa_enabled": 149,
      "coverage_percent": 30
    },
    ...
  ]
}
```

### Requirements List

```bash
# All requirements
curl -X GET "http://localhost:8000/api/v1/riverside/requirements" \
  -H "Authorization: Bearer $TOKEN"

# Filter by status
curl -X GET "http://localhost:8000/api/v1/riverside/requirements?status=Not Started" \
  -H "Authorization: Bearer $TOKEN"

# Filter by category
curl -X GET "http://localhost:8000/api/v1/riverside/requirements?category=IAM" \
  -H "Authorization: Bearer $TOKEN"
```

### Critical Gaps

```bash
curl -X GET "http://localhost:8000/api/v1/riverside/gaps" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "critical_gaps": [
    {
      "requirement_id": "IAM-12",
      "requirement_name": "Universal MFA Enforcement",
      "status": "In Progress",
      "current_progress": 30,
      "target": 100,
      "deadline": "Immediate",
      "risk_level": "Critical",
      "financial_impact": 4000000,
      "owner": "Security Team"
    },
    ...
  ],
  "warning_gaps": [...],
  "total_financial_risk": 4000000
}
```

### Maturity Scores

```bash
# All domains
curl -X GET "http://localhost:8000/api/v1/riverside/maturity-scores" \
  -H "Authorization: Bearer $TOKEN"

# Per tenant
curl -X GET "http://localhost:8000/api/v1/riverside/maturity-scores/HTT" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "overall": {
    "current": 2.4,
    "target": 3.0,
    "gap": 0.6
  },
  "by_domain": [
    {
      "domain": "IAM",
      "current": 2.2,
      "target": 3.0,
      "gap": 0.8
    },
    {
      "domain": "GS",
      "current": 2.5,
      "target": 3.0,
      "gap": 0.5
    },
    ...
  ]
}
```

---

## Dashboard Walkthrough

### Access

Open the Riverside dashboard:

```
http://localhost:8000/riverside
```

### Components

#### 1. Executive Summary Card

Located at the top, shows:
- Overall maturity score (2.4/5.0)
- Days remaining (160)
- Financial risk ($4M)
- Requirements completion (45/72)

#### 2. MFA Compliance Gauge

Visual indicator showing:
- Current: 30%
- Target: 100%
- Protected: 634 users
- Unprotected: 1,358 users

#### 3. Domain Maturity Radar Chart

Interactive radar chart showing:
- IAM: 2.2
- GS: 2.5
- DS: 2.6
- Security Operations: 2.3
- Platform Security: 2.4

#### 4. Requirements Status Table

Filterable table with columns:
- Requirement ID
- Name
- Category
- Status
- Priority
- Owner
- Due Date

**Filters:**
- Status: All, Not Started, In Progress, Compliant
- Category: All, IAM, GS, DS, Device
- Priority: All, P0, P1, P2

#### 5. Timeline Widget

Countdown display showing:
- Days/hours/minutes to deadline
- Milestones achieved
- Upcoming critical dates

#### 6. Risk Summary Panel

Financial risk breakdown:
- Total risk: $4M
- Risk by category
- Risk mitigation progress

---

## Data Sync Configuration

### Automatic Sync

Riverside data syncs automatically based on configuration:

```env
RIVERSIDE_SYNC_INTERVAL_HOURS=4
```

### Manual Sync

Trigger a manual sync:

```bash
curl -X POST "http://localhost:8000/api/v1/sync/riverside" \
  -H "Authorization: Bearer $TOKEN"
```

### Data Sources

| Source | Integration | Frequency |
|--------|-------------|-----------|
| Microsoft Graph | MFA data | Every 4 hours |
| Intune | Device data | Every 4 hours |
| Azure AD | Admin roles | Every 4 hours |
| Manual entry | Requirements | On-demand |

### Syncing MFA Data

For Phase 1, MFA data can be entered manually:

```bash
# Update MFA status for a tenant
curl -X PUT "http://localhost:8000/api/v1/riverside/mfa-status/HTT" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "total_users": 498,
    "mfa_enabled": 149,
    "mfa_disabled": 349,
    "admin_accounts_total": 12,
    "admin_accounts_mfa_enabled": 8
  }'
```

---

## Evidence Upload Process

### Upload Evidence

```bash
# Upload evidence for a requirement
curl -X POST "http://localhost:8000/api/v1/riverside/requirements/IAM-12/evidence" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@mfa-policy-screenshot.png" \
  -F "evidence_type=Screenshot" \
  -F "notes=MFA policy enforcement screenshot"
```

### Link External Evidence

```bash
# Link to external evidence (e.g., SharePoint document)
curl -X POST "http://localhost:8000/api/v1/riverside/requirements/IAM-12/evidence" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_type": "External Link",
    "evidence_link": "https://company.sharepoint.com/sites/compliance/documents/mfa-policy.pdf",
    "notes": "Linked to SharePoint policy document"
  }'
```

### Evidence Types

| Type | Description |
|------|-------------|
| Screenshot | Visual evidence |
| Document | PDF/Word document |
| API Verification | Automated check result |
| External Link | URL to evidence |
| Email | Communication record |
| Certificate | Compliance certificate |

---

## Troubleshooting

### Dashboard Not Loading

1. Check that `RIVERSIDE_COMPLIANCE_ENABLED=true`
2. Verify database has Riverside tables:

```bash
sqlite3 data/governance.db ".tables" | grep riverside
```

3. Check logs for errors:

```bash
tail -f logs/app.log | grep -i riverside
```

### MFA Data Not Showing

1. Verify data exists in database:

```sql
SELECT * FROM mfa_compliance ORDER BY snapshot_date DESC LIMIT 1;
```

2. Trigger manual sync:

```bash
curl -X POST "http://localhost:8000/api/v1/sync/riverside/mfa"
```

3. Manually update via API:

```bash
# See Manual Data Entry section
```

### API Returns 404

1. Verify `RIVERSIDE_COMPLIANCE_ENABLED=true`
2. Check application startup logs for Riverside routes
3. Restart the application:

```bash
pkill -f uvicorn
uvicorn app.main:app --reload
```

### Database Migration Issues

If tables don't exist:

```bash
# Create tables manually
python -c "
from app.core.database import engine
from app.models.riverside import Base
Base.metadata.create_all(bind=engine)
print('Tables created')
"
```

---

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Technical architecture
- [RIVERSIDE_EXECUTIVE_SUMMARY.md](./RIVERSIDE_EXECUTIVE_SUMMARY.md) - Executive summary
- [RIVERSIDE_API_GUIDE.md](./RIVERSIDE_API_GUIDE.md) - API reference
- [README.md](../README.md) - Platform documentation
