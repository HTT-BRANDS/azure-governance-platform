# Riverside API Guide

API reference documentation for Riverside compliance endpoints.

## Base URL

```
http://localhost:8000/api/v1/riverside
```

## Authentication

All endpoints require Azure AD authentication. Include the Bearer token in the Authorization header:

```bash
curl -H "Authorization: Bearer $TOKEN" ...
```

---

## Endpoints

### Executive Summary

#### GET /summary

Returns executive-level compliance summary.

**Response:**

```json
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

**Example:**

```bash
curl -X GET "http://localhost:8000/api/v1/riverside/summary"
```

---

### Requirements

#### GET /requirements

Returns all compliance requirements with optional filters.

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| status | string | Filter by status | All |
| category | string | Filter by category | All |
| priority | string | Filter by priority | All |
| page | int | Page number | 1 |
| page_size | int | Items per page | 50 |

**Status Values:** `Not Started`, `In Progress`, `Compliant`, `Exempt`

**Category Values:** `IAM`, `GS`, `DS`, `Device`, `SecOps`, `PlatSec`

**Priority Values:** `P0`, `P1`, `P2`

**Response:**

```json
{
  "items": [
    {
      "id": "IAM-12",
      "name": "Universal MFA Enforcement",
      "category": "IAM",
      "status": "In Progress",
      "priority": "P0",
      "owner": "Security Team",
      "due_date": "2026-02-08",
      "completed_date": null,
      "current_progress": 30,
      "target_progress": 100,
      "notes": "Enrolling users"
    }
  ],
  "total": 72,
  "page": 1,
  "page_size": 50
}
```

**Example:**

```bash
# All requirements
curl -X GET "http://localhost:8000/api/v1/riverside/requirements"

# Filter by status
curl -X GET "http://localhost:8000/api/v1/riverside/requirements?status=Not%20Started"

# Filter by category
curl -X GET "http://localhost:8000/api/v1/riverside/requirements?category=IAM"
```

#### GET /requirements/{id}

Returns a single requirement by ID.

**Response:**

```json
{
  "id": "IAM-12",
  "name": "Universal MFA Enforcement",
  "category": "IAM",
  "description": "All users must have MFA enabled",
  "status": "In Progress",
  "priority": "P0",
  "owner": "Security Team",
  "due_date": "2026-02-08",
  "completed_date": null,
  "current_progress": 30,
  "target_progress": 100,
  "evidence": [
    {
      "id": 1,
      "type": "Screenshot",
      "link": null,
      "notes": "MFA policy screenshot",
      "uploaded_at": "2026-01-08T10:00:00Z"
    }
  ],
  "notes": "Enrolling users"
}
```

#### POST /requirements

Creates a new requirement.

**Request Body:**

```json
{
  "id": "IAM-16",
  "name": "Password Policy Enforcement",
  "category": "IAM",
  "description": "Enforce password complexity",
  "priority": "P1",
  "owner": "IT Team",
  "due_date": "2026-05-01"
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/riverside/requirements" \
  -H "Content-Type: application/json" \
  -d '{"id":"IAM-16","name":"Password Policy","category":"IAM","priority":"P1"}'
```

#### PUT /requirements/{id}

Updates an existing requirement.

**Request Body:**

```json
{
  "status": "In Progress",
  "current_progress": 50,
  "notes": "Implemented for 3 tenants"
}
```

#### POST /requirements/{id}/evidence

Uploads evidence for a requirement.

**Request (multipart/form-data):**

| Field | Type | Description |
|-------|------|-------------|
| file | file | Evidence file (optional) |
| evidence_type | string | Type of evidence |
| evidence_link | string | External link (optional) |
| notes | string | Notes about evidence |

**Evidence Types:**

- `Screenshot`
- `Document`
- `API Verification`
- `External Link`
- `Email`
- `Certificate`

**Example:**

```bash
# Upload file
curl -X POST "http://localhost:8000/api/v1/riverside/requirements/IAM-12/evidence" \
  -F "file=@screenshot.png" \
  -F "evidence_type=Screenshot" \
  -F "notes=MFA settings"

# Link external evidence
curl -X POST "http://localhost:8000/api/v1/riverside/requirements/IAM-12/evidence" \
  -H "Content-Type: application/json" \
  -d '{"evidence_type":"External Link","evidence_link":"https://sharepoint.com/doc","notes":"Policy doc"}'
```

---

### MFA Status

#### GET /mfa-status

Returns MFA enrollment status across all tenants.

**Response:**

```json
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
      "mfa_disabled": 349,
      "coverage_percent": 30,
      "admin_accounts_total": 12,
      "admin_accounts_mfa_enabled": 8
    }
  ]
}
```

#### GET /mfa-status/{tenant_id}

Returns MFA status for a specific tenant.

**Response:**

```json
{
  "tenant_id": "htt",
  "tenant_name": "HTT",
  "total_users": 498,
  "mfa_enabled": 149,
  "mfa_disabled": 349,
  "coverage_percent": 30,
  "admin_accounts_total": 12,
  "admin_accounts_mfa_enabled": 8,
  "snapshot_date": "2026-01-08"
}
```

#### PUT /mfa-status/{tenant_id}

Updates MFA status for a tenant (manual entry).

**Request Body:**

```json
{
  "total_users": 498,
  "mfa_enabled": 149,
  "mfa_disabled": 349,
  "admin_accounts_total": 12,
  "admin_accounts_mfa_enabled": 8
}
```

---

### Device Compliance

#### GET /device-compliance

Returns device compliance overview.

**Response:**

```json
{
  "summary": {
    "total_devices": 2450,
    "compliant_devices": 1715,
    "non_compliant_devices": 490,
    "pending_devices": 245,
    "compliance_rate": 70
  },
  "by_tenant": [
    {
      "tenant_id": "htt",
      "tenant_name": "HTT",
      "total_devices": 612,
      "compliant_devices": 428,
      "non_compliant_devices": 122,
      "pending_devices": 62,
      "compliance_rate": 70,
      "mdm_enrolled": 550,
      "edr_installed": 480
    }
  ]
}
```

#### GET /device-compliance/{tenant_id}

Returns device compliance for specific tenant.

---

### Maturity Scores

#### GET /maturity-scores

Returns domain maturity scores.

**Response:**

```json
{
  "overall": {
    "current": 2.4,
    "target": 3.0,
    "gap": 0.6,
    "trend": "stable"
  },
  "by_domain": [
    {
      "domain": "IAM",
      "current": 2.2,
      "target": 3.0,
      "gap": 0.8,
      "trend": "up"
    },
    {
      "domain": "GS",
      "current": 2.5,
      "target": 3.0,
      "gap": 0.5,
      "trend": "stable"
    },
    {
      "domain": "DS",
      "current": 2.6,
      "target": 3.0,
      "gap": 0.4,
      "trend": "stable"
    }
  ],
  "by_tenant": [...]
}
```

#### GET /maturity-scores/{tenant_id}

Returns maturity scores for specific tenant.

#### PUT /maturity-scores

Updates maturity scores (manual entry).

**Request Body:**

```json
{
  "tenant_id": "htt",
  "domain": "IAM",
  "score": 2.3,
  "assessor": "Security Team",
  "notes": "Updated after MFA push"
}
```

---

### Timeline

#### GET /timeline

Returns deadline timeline and milestones.

**Response:**

```json
{
  "deadline": "2026-07-08",
  "days_remaining": 160,
  "milestones": [
    {
      "milestone": "MFA >80%",
      "target_date": "2026-03-08",
      "status": "not_started",
      "days_until": 59
    },
    {
      "milestone": "All P0 Compliant",
      "target_date": "2026-05-08",
      "status": "not_started",
      "days_until": 120
    }
  ],
  "completed_milestones": []
}
```

---

### Critical Gaps

#### GET /gaps

Returns critical gap analysis.

**Response:**

```json
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
    }
  ],
  "warning_gaps": [
    {
      "requirement_id": "DS-02",
      "requirement_name": "Data Classification",
      "status": "Not Started",
      "current_progress": 0,
      "target": 100,
      "deadline": "2026-04-08",
      "risk_level": "Medium",
      "financial_impact": 500000,
      "owner": "Data Team"
    }
  ],
  "total_financial_risk": 4000000
}
```

---

### External Threats

#### GET /threats

Returns external threat data.

**Response:**

```json
{
  "latest": {
    "threat_beta_score": 1.04,
    "baseline": 1.0,
    "comparison": "15% higher than peers",
    "vulnerability_count": 12,
    "malicious_domains": 3,
    "last_updated": "2026-01-08"
  },
  "history": [...]
}
```

---

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "status"],
      "msg": "invalid status",
      "type": "value_error"
    }
  ]
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| GET requests | 100/minute |
| POST/PUT requests | 50/minute |
| File uploads | 10/minute |

---

## Related Documentation

- [RIVERSIDE_INTEGRATION.md](./RIVERSIDE_INTEGRATION.md) - Full integration guide
- [RIVERSIDE_EXECUTIVE_SUMMARY.md](./RIVERSIDE_EXECUTIVE_SUMMARY.md) - Executive overview
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Technical architecture
