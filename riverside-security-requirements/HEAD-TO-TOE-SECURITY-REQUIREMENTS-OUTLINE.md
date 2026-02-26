# Head to Toe Brands Security Requirements Outline
## Riverside Company Cyber Health Check - Implementation Guide

**Document Version:** 1.0  
**Date:** February 26, 2026  
**Prepared By:** Web-Puppy Research Agent  
**Source:** Riverside Company Readout (January 8, 2026)  
**Deadline:** July 8, 2026 (6 months from issuance)

---

## Executive Summary

This document consolidates the security requirements and findings from The Riverside Company's Cyber Health Check conducted on Head to Toe Brands in January 2026. The purpose is to provide a single-source-of-truth for security compliance tracking and to outline how these requirements can be monitored through the Azure Multi-Tenant Governance Platform.

### Critical Timeline
- **Assessment Date:** January 8, 2026
- **Compliance Deadline:** July 8, 2026 (6 months)
- **Current Status:** Multiple gaps requiring immediate attention

### Overall Maturity Scores
| Domain | Score | Target | Gap |
|--------|-------|--------|-----|
| Governance & Strategy | 2.4/5 | 3.0/5 | 0.6 |
| Network & Infrastructure | 2.5/5 | 3.0/5 | 0.5 |
| Identity & Access Management | 2.3/5 | 3.0/5 | 0.7 |
| Application Security | 2.2/5 | 3.0/5 | 0.8 |
| Data Protection | TBD | 3.0/5 | - |
| Monitoring | TBD | 3.0/5 | - |
| Resilience | TBD | 3.0/5 | - |

### Threat Landscape
- **Threat Beta Score:** 1.04 (moderate breach likelihood)
- **Risk vs Peers:** 15% higher than identified peers
- **Potential Financial Impact:** ~$4.0 million from single major event
  - Hard costs: $2.4 million (business interruption, fines, legal, IR, hardware)
  - Soft costs: $1.6 million (brand/reputational damage)
- **External Vulnerabilities:** 12 identified (4 priority, remotely exploitable)
- **Malicious Domains:** 7 potentially malicious registrations detected

---

## Part 1: Critical Requirements Summary

### 🔴 DO NOW (Immediate - First 30 Days)

| ID | Requirement | Domain | Priority | Owner | Current Status |
|----|-------------|--------|----------|-------|----------------|
| **GS-10** | Establish dedicated security team; name director-level security lead with authority | Governance | Critical | Tyler/Kristin | Not started |
| **GS-20/21** | Document formal information security policy covering 6-10 security areas | Governance | Critical | Legal/IT | Partial (acceptable use in new hire manual only) |
| **GS-30** | Institute KnowBe4 security awareness training for all employees | Governance | Critical | HR/IT | Partial (phishing training pushed out, general awareness pending) |
| **NI-41** | Implement endpoint protection (EDR) on all physical assets and virtual servers | Infrastructure | Critical | IT | Not started |
| **NI-42** | Accelerate email filtering and scanning; review quarterly | Infrastructure | Critical | IT | Partial (basic settings enabled) |
| **NI-43-48** | Complete MDM rollout covering: removable media, device firewall, encryption, local admin, remote wipe, asset access, software updates | Infrastructure | Critical | IT | In progress |
| **IAM-12** | Enable and enforce MFA universally across all tenants and user types without exception | IAM | Critical | IT | Major gaps (see breakdown below) |
| **D-4** | Confirm ecommerce data tokenization, encryption in transit, and formal data storage policy | Data | Critical | IT/Compliance | Under review |

### 🟡 DO NEXT (30-90 Days)

| ID | Requirement | Domain | Priority | Owner | Current Status |
|----|-------------|--------|----------|-------|----------------|
| **GS-1** | Establish and communicate formal security initiatives list with MSP role clarity | Governance | High | Leadership | Partial (items defined, not timelined) |
| **GS-18** | Document succession plan for key roles (Tyler/Kristin) | Governance | High | HR/Leadership | Informal |
| **IAM-1,2,8** | Fully integrate all tenants under consistent Azure AD security policies; standardize onboarding/offboarding | IAM | High | IT | Fragmented across 4 brands |
| **IAM-4,5** | Deploy enterprise password manager; eliminate shared passwords | IAM | High | IT | Shared passwords exist |
| **AP-2** | Leverage Intune Enterprise App Management for timely updates | Application | Medium | IT | Partial |
| **M-1** | Establish policies/procedures to monitor key system resources | Monitoring | High | IT | Not formalized |
| **M-3,8** | Ingest all logs into SIEM for complete coverage | Monitoring | High | IT | Partial |
| **M-11,12,16** | Create incident response team; define incidents and response procedures; classify data requiring higher safeguarding | Resilience | High | IT/Security | Not formalized |
| **E-3,4** | Review and optimize malware settings | Office 365 | Medium | IT | Partial |

---

## Part 2: Multi-Tenant Environment Breakdown

### Brand Structure Overview

Head to Toe Brands operates across **4 separate Azure/Office 365 tenants** representing acquired entities:

| Brand | Users | MFA Enabled | Admin Users | Devices | Status |
|-------|-------|-------------|-------------|---------|--------|
| **HTT** (Head to Toe) | 352 | 0% (0/342) | 7 total, 3 global | 558 | ⚠️ Critical - No MFA |
| **BCC** | 153 | 89% (131/147) | 4 total, 4 global | 39 | ✅ Good MFA coverage |
| **FN** (Footwear etc.) | 305 | 0% (0/287) | 11 total, 9 global | 174 | ⚠️ Critical - No MFA, high admin count |
| **TLL** | 1,181 | 39% (428/1,096) | 17 total, 4 global | 907 | ⚠️ Partial MFA coverage |
| **TOTAL** | **1,928** | **559/1,872 (30%)** | **39 total admins** | **1,678** | **70% lack MFA** |

### Critical MFA Gap Analysis
- **Total Enabled Users:** 1,872
- **Total with MFA Registered:** 559
- **Total WITHOUT MFA:** 1,313 (70%)
- **Brands with 0% MFA:** HTT, FN (completely unprotected)

**This represents the #1 security risk.**

### Admin Account Risk Analysis
- **Total Admin Accounts:** 39 across all brands
- **Global Admins:** 20
- **Risk Assessment:** FN brand has highest ratio (9 global admins for 305 users)

### Device Management Status
- **Total Devices:** 1,678
- **Enabled Devices:** 1,660 (98.9% - good maintenance)
- **Windows Devices:** 1,566
- **Mobile Devices:** 94
- **Device Enrollment:** Inconsistent across brands - requires standardization

---

## Part 3: Detailed Gap Analysis

### Governance & Strategy (2.4/5)

| Capability | Status | Gap | Evidence |
|------------|--------|-----|----------|
| **Cyber Strategy & Roadmap** | Partial | No documented timelines | Some initiatives defined, rely on Logically for ownership |
| **Risk Tolerance Definition** | Informal | Not documented | Known but not formalized; Tyler working with exec team |
| **Management Cyber Discussions** | Reactive | No formal agenda | Managed by Logically; informal discussions only |
| **Business Unit Accountability** | Reactive | Only when incidents occur | Currently in audit state; MSP interviews ongoing |
| **Security Budgeting** | Partial | Part of IT budget only | Confirmation provided but not dedicated |
| **Security Team Structure** | Missing | Delegated to MSP | **CRITICAL GAP** - No dedicated security team |
| **Security Authority** | Partial | Needs business executive involvement | Backed by IT but lacks business alignment |
| **Hardware/Software Assessment** | Partial | Annual review only | IT-led, needs quarterly reviews |
| **Succession Planning** | Informal | No documented plan | Tyler and Kristin share responsibility informally |
| **Security Policy Documentation** | Missing | Acceptable use only | Part of new hire manual, not comprehensive |
| **Security Training Program** | Partial | KnowBe4 not fully configured | Reviewing with Logically, not company-wide |
| **Phishing Training** | Active | Needs quarterly reviews | Being pushed out by Logically |
| **Cyber Insurance** | Partial | Basic Riverside policy | Amount needs confirmation |
| **Vendor Screening** | Under Review | Process exists but reviewing | To be followed up |
| **Contract Security Requirements** | Partial | Not reviewed formally | Stipulations exist in contracts |
| **External Provider Assessment** | N/A | N/A | N/A |
| **Data Destruction on Termination** | Partial | Basic equipment return only | No vendor data destruction agreements |

### Network & Infrastructure (2.5/5)

| Capability | Status | Gap | Evidence |
|------------|--------|-----|----------|
| **Asset Inventory** | Incomplete | In process | Not complete but in progress |
| **Asset Prioritization** | Informal | Not formalized | Consideration by role but not documented |
| **Change Management** | Partial | Ticketing system not covering all aspects | Defined but not fully formed |
| **Configuration Standards** | Informal | In progress with IT audit | Informal configuration standard |
| **Authorized Reseller Policy** | Partial | Amazon/Best Buy purchases | Formalized list updated annually |
| **Firewall Protection** | Strong but undocumented | Rulebase unorganized | Configuration considered strong |
| **Default "Deny All" Posture** | Not Compliant | Currently not "Deny All" | Needs firewall policy review |
| **DMZ Setup** | Unknown | - | Not specified in assessment |
| **Wireless Security** | Partial | Needs expansion | Segmented guest access, needs more controls |
| **IDS/IPS** | Partial | "Half-baked" per review | Limited automated alerts only |
| **Remote Access** | Under Review | - | To be followed up |
| **Network Segmentation** | Under Review | - | To be followed up |
| **Cloud Security Posture** | Unknown | - | Not fully assessed |

### Identity & Access Management (2.3/5)

| Capability | Status | Gap | Evidence |
|------------|--------|-----|----------|
| **Identity Store Integration** | Fragmented | 4 separate tenants | Not fully integrated under consistent policies |
| **Privileged Access Management** | Partial | Inconsistent processes | Onboarding/offboarding without standardized processes |
| **Service Account Governance** | Partial | Lack of documentation | Not fully documented |
| **Password Manager** | Missing | No enterprise solution | Shared passwords exist |
| **Shared Password Policy** | Missing | Not enforced | Shared passwords across systems |
| **Password Policy Enforcement** | Partial | Not consistently enforced | Gaps remain |
| **MFA Implementation** | **CRITICAL GAP** | 70% lack MFA | Only 30% coverage across brands |
| **Conditional Access Policies** | Partial | Inconsistent | Needs standardization |
| **Regular Access Reviews** | Missing | Not formalized | Not documented |
| **Service Principal Management** | Unknown | - | Not assessed |
| **Guest User Management** | Partial | Needs review | Not standardized across tenants |
| **Identity Monitoring** | Missing | Not implemented | No ongoing monitoring |

### Application Security (2.2/5)

| Capability | Status | Gap | Evidence |
|------------|--------|-----|----------|
| **Custom Software Security** | N/A | No custom software | Focus on managing software assets |
| **Patch Management** | Partial | Timing needs improvement | Updates not always timely |
| **Application Risk Assessment** | Missing | Not formalized | No understanding of relative risk per application |
| **Software Asset Management** | Partial | Needs improvement | Basic tracking exists |
| **Intune/App Management** | Partial | Not fully utilized | Enterprise App Catalog features available but not leveraged |

### Data Protection (Score TBD)

| Capability | Status | Gap | Evidence |
|------------|--------|-----|----------|
| **Data Classification** | Missing | Not formalized | Need to classify data requiring higher safeguarding |
| **E-commerce Data Handling** | Under Review | Tokenization/encryption needs confirmation | D-4 - confirm proper tokenization and encryption |
| **Data Storage Policy** | Missing | No formal policy | Need formal policy defining how data is stored/managed |
| **PII/PCI Handling** | Under Review | Compliance needs assessment | Regulations understood but implementation unclear |

### Monitoring & Detection (Score TBD)

| Capability | Status | Gap | Evidence |
|------------|--------|-----|----------|
| **System Resource Monitoring** | Missing | No formal policies/procedures | M-1 - need defined policies |
| **Log Aggregation** | Partial | Incomplete coverage | M-3,8 - need SIEM for all logs |
| **Alerting** | Partial | Limited automated alerts | Needs improvement |
| **Vulnerability Scanning** | Missing | Not formalized | Monthly scanning needed |
| **Penetration Testing** | Missing | Not conducted annually | Annual testing required |

### Resilience & Incident Response (Score TBD)

| Capability | Status | Gap | Evidence |
|------------|--------|-----|----------|
| **Incident Response Team** | Missing | Not created | M-11,12 - create IR team |
| **Incident Classification** | Missing | Not defined | Need to define what warrants what type of response |
| **Incident Documentation** | Missing | No formal process | Need formal reporting process |
| **Knowledge Base** | Missing | Not maintained | Need ongoing updated knowledge base |
| **Business Continuity Plan** | Missing | Not defined | Identify and develop business-specific BCP |
| **Backup & Recovery** | Partial | Procedures need formalization | Under review |
| **DR Testing** | Missing | Not conducted annually | Annual testing required |

---

## Part 4: External Threat Analysis Summary

### Key Findings from Cybeta External Analysis (January 2, 2026)

**Threat Beta Score: 1.04**
- Moderate breach likelihood
- 15% higher than identified peers
- Aligned with broader peer median

**Attack Surface**
- 16 externally visible IP addresses
- 177 open ports
- 19 identifiable technologies
- Exceeds peer median (increases attacker opportunity)

**Vulnerabilities**
- 12 externally visible vulnerabilities identified
- 4 priority vulnerabilities (remotely exploitable, no authentication required)
- None currently listed as CISA Known Exploited Vulnerabilities

**Brand Impersonation Risk**
- 7 potentially malicious domain registrations
- Closely resemble legitimate brand domains
- Several have active mail (MX) records
- Potential for phishing, brand impersonation, or BEC preparation

**Third-Party Risk**
- No vulnerable third-party cloud or externally hosted assets identified
- (Note: This analysis is point-in-time and external-only)

### Risk Mitigation Impact
- **Full vulnerability remediation:** Could reduce Threat Beta to ~1.01
- **Projected savings:** Nearly full $4M estimated loss amount
- **Key actions:** Reduce externally visible attack surface, validate patch status

---

## Part 5: Compliance Tracking Framework

### Tracking Structure for Governance Platform

The following structure outlines how Riverside requirements can be tracked within the Azure Multi-Tenant Governance Platform architecture described in the existing documentation.

#### Data Model Extensions

```sql
-- Riverside compliance tracking table
CREATE TABLE riverside_compliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_id TEXT NOT NULL,           -- e.g., "GS-10", "IAM-12"
    domain TEXT NOT NULL,                   -- e.g., "Governance", "IAM", "Network"
    category TEXT NOT NULL,                 -- "Do Now" or "Do Next"
    priority TEXT NOT NULL,                 -- "Critical", "High", "Medium"
    requirement_title TEXT NOT NULL,
    requirement_description TEXT,
    current_status TEXT NOT NULL,           -- "Not Started", "In Progress", "Complete"
    target_date DATE,                       -- July 8, 2026 deadline
    owner TEXT,                             -- Responsible party
    evidence_location TEXT,                 -- Link to documentation
    last_verified DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Multi-tenant MFA tracking
CREATE TABLE mfa_compliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    brand TEXT NOT NULL,                    -- HTT, BCC, FN, TLL
    total_users INTEGER,
    enabled_users INTEGER,
    mfa_registered INTEGER,
    mfa_percentage REAL,
    global_admins INTEGER,
    total_admins INTEGER,
    measurement_date DATE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Device compliance tracking
CREATE TABLE device_compliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    brand TEXT NOT NULL,
    total_devices INTEGER,
    enabled_devices INTEGER,
    windows_devices INTEGER,
    mobile_devices INTEGER,
    mdm_enrolled INTEGER,
    encryption_enabled INTEGER,
    measurement_date DATE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- External threat tracking
CREATE TABLE external_threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_date DATE,
    threat_beta_score REAL,
    peer_comparison TEXT,
    vulnerabilities_count INTEGER,
    priority_vulnerabilities INTEGER,
    malicious_domains INTEGER,
    potential_financial_impact REAL,
    last_updated TIMESTAMP
);
```

#### API Endpoints for Tracking

```
# Riverside-specific endpoints
GET  /api/v1/riverside/requirements           # All requirements with status
GET  /api/v1/riverside/requirements/{domain}  # Requirements by domain
GET  /api/v1/riverside/gaps                   # Current gaps summary
GET  /api/v1/riverside/timeline               # Timeline to deadline
GET  /api/v1/riverside/mfa-status             # Real-time MFA compliance
GET  /api/v1/riverside/device-status          # Device compliance status
GET  /api/v1/riverside/maturity-scores        # Domain maturity tracking

# Progress tracking
POST /api/v1/riverside/requirements/{id}/status    # Update requirement status
POST /api/v1/riverside/requirements/{id}/evidence  # Upload evidence
GET  /api/v1/riverside/dashboard              # Executive dashboard
```

#### HTMX Partials for Riverside Tracking

```
GET  /partials/riverside/requirements-table      # Requirements list
GET  /partials/riverside/mfa-gauge               # MFA compliance gauge
GET  /partials/riverside/maturity-chart          # Maturity scoring chart
GET  /partials/riverside/timeline-alert          # Days remaining alert
GET  /partials/riverside/threat-summary          # External threat summary
```

### Dashboard Components

#### 1. Executive Summary Panel
- **Days to Deadline:** Countdown timer
- **Overall Compliance %:** Progress bar
- **Critical Gaps Count:** Red/Amber/Green indicator
- **MFA Coverage:** Real-time percentage across all brands

#### 2. Domain Maturity Tracking
- Interactive radar chart showing current vs. target scores
- Drill-down capability per domain
- Historical trending

#### 3. Requirement Tracking Table
- Sortable/filterable table of all requirements
- Status indicators (Not Started, In Progress, Complete)
- Owner assignments
- Evidence links
- Due dates with countdown

#### 4. Multi-Tenant MFA Monitor
- Real-time MFA registration status per brand
- Visual indicators for gaps (0% = red, <50% = amber, >80% = green)
- Admin account monitoring
- Automated alerts for new unprotected accounts

#### 5. External Threat Monitor
- Current Threat Beta score
- Vulnerability count with priority flagging
- Malicious domain alerts
- Trending over time

### Alerting Configuration

| Alert | Trigger | Channel | Frequency |
|-------|---------|---------|-----------|
| Deadline Approaching | < 30 days remaining | Email + Teams | Daily |
| MFA Gap Detected | New user without MFA | Teams | Immediate |
| Critical Requirement Overdue | Past target date | Email + Teams | Daily |
| External Threat Change | New vulnerabilities | Teams | Immediate |
| Maturity Score Drop | > 0.5 point decrease | Teams | Weekly |

---

## Part 6: Implementation Roadmap

### Phase 1: Foundation (Days 1-30) - DO NOW Items

**Week 1-2: Immediate Actions**
1. **Enable MFA Everywhere (IAM-12)**
   - Emergency rollout across all 4 tenants
   - Target: 100% coverage within 14 days
   - Start with HTT and FN (currently 0%)
   - Communicate mandate to all users

2. **Establish Security Leadership (GS-10)**
   - Define director-level security lead role
   - Document responsibilities and authority
   - Create RACI matrix with Logically

3. **Emergency Policy Documentation (GS-20/21)**
   - Draft information security policy
   - Cover minimum 6 areas: access control, data handling, encryption, incident response, acceptable use, asset management

**Week 3-4: Infrastructure Hardening**
4. **Endpoint Protection (NI-41)**
   - Deploy EDR to all endpoints
   - Begin with highest-risk assets

5. **Email Security (NI-42)**
   - Review and strengthen filtering
   - Configure advanced threat protection

6. **MDM Acceleration (NI-43-48)**
   - Prioritize device enrollment
   - Enable remote wipe capabilities
   - Configure device encryption

### Phase 2: Documentation & Standardization (Days 31-90) - DO NEXT Items

**Month 2:**
7. **Formalize Security Initiatives (GS-1)**
   - Document complete initiative list
   - Define MSP roles clearly
   - Establish timelines

8. **Tenant Integration (IAM-1,2,8)**
   - Standardize Azure AD policies
   - Unified onboarding/offboarding process

9. **Password Management (IAM-4,5)**
   - Deploy enterprise password manager
   - Eliminate shared passwords

**Month 3:**
10. **Monitoring Infrastructure (M-1,3,8)**
    - Implement SIEM or MaaS
    - Ingest all logs
    - Define monitoring policies

11. **Incident Response (M-11,12,16)**
    - Create IR team
    - Define incident classifications
    - Document response procedures

### Phase 3: Optimization (Days 91-180)

**Months 4-5:**
12. **External Security Reviews**
    - Conduct penetration testing
    - Vulnerability scanning program
    - Remediate findings

13. **Business Continuity**
    - Develop formal BCP
    - Conduct DR testing
    - Document procedures

**Month 6:**
14. **Final Compliance Review**
    - Verify all requirements met
    - Compile evidence
    - Prepare Riverside reporting

---

## Part 7: Success Metrics

### Primary KPIs

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| MFA Coverage | 30% | 100% | Daily automated check |
| Maturity Score (Overall) | 2.4 | 3.0+ | Monthly assessment |
| Critical Gaps Remaining | 8 | 0 | Weekly tracking |
| External Vulnerabilities | 12 | 0 | Monthly scan |
| Threat Beta Score | 1.04 | <1.01 | Quarterly assessment |

### Secondary KPIs

| Metric | Baseline | Target |
|--------|----------|--------|
| Security Policy Coverage | 1 area | 10+ areas |
| Training Completion | Partial | 100% |
| Device MDM Enrollment | Partial | 100% |
| Endpoint EDR Coverage | 0% | 100% |
| Admin Account Review | Informal | Quarterly formal |

---

## Part 8: Evidence & Documentation Requirements

### Required Evidence per Requirement

Each requirement must have documented evidence of completion:

**Governance Requirements:**
- Security policy document (version controlled, dated)
- Org chart with security roles
- Training completion reports
- Vendor assessment questionnaires
- Cyber insurance policy documentation

**IAM Requirements:**
- Azure AD MFA configuration exports
- Conditional Access policy documentation
- Password manager deployment records
- Access review documentation
- Onboarding/offboarding procedures

**Infrastructure Requirements:**
- MDM enrollment reports
- EDR deployment logs
- Firewall configuration backups
- Asset inventory exports
- Change management tickets

**Monitoring Requirements:**
- SIEM/MaaS configuration
- Log aggregation verification
- Alert configuration
- Incident response runbooks

---

## Part 9: Risks & Dependencies

### Implementation Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| User resistance to MFA | High | Medium | Executive mandate, phased rollout, training |
| Logically bandwidth constraints | High | High | Clear RACI, dedicated project management |
| Acquisition distractions | High | High | Protected project time, executive sponsorship |
| Resource constraints (Tyler/Kristin) | Critical | High | Security hire priority, contractor support |
| Tool deployment delays | Medium | Medium | Early procurement, parallel workstreams |
| Cross-tenant complexity | Medium | Medium | Standardized approach, automation |

### External Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Logically MSP engagement | Tyler | In review |
| Riverside insurance policy | Leadership | Amount TBD |
| Executive team risk tolerance | Tyler | In discussion |
| Vendor contract security clauses | Legal | Under review |

---

## Part 10: Integration with Existing Platform

### Platform Capability Mapping

The existing Azure Multi-Tenant Governance Platform architecture can support Riverside tracking with these extensions:

#### Current Platform Strengths
- ✅ Multi-tenant Azure/M365 management
- ✅ Cost tracking across subscriptions
- ✅ Compliance monitoring (Azure Policy)
- ✅ Resource inventory
- ✅ Identity governance foundation

#### Required Extensions

| Riverside Need | Platform Extension | Effort |
|----------------|-------------------|--------|
| Requirement tracking | New `riverside_compliance` table + UI | Medium |
| MFA compliance monitoring | Extend identity module for per-user MFA status | Low |
| Maturity scoring | New dashboard component | Medium |
| Timeline tracking | Add deadline monitoring + alerts | Low |
| Evidence management | Document upload/link storage | Medium |
| External threat integration | API integration with Cybeta or similar | High |

### Recommended Development Priority

1. **Week 1:** Extend identity module for MFA tracking (critical need)
2. **Week 2-3:** Build requirement tracking database schema
3. **Week 4:** Create Riverside compliance dashboard
4. **Month 2:** Add evidence management capability
5. **Month 3:** Integrate external threat monitoring (if API available)

---

## Appendix A: Complete Requirement Catalog

### Governance & Strategy

| ID | Requirement | Maturity | Priority | Owner | Status |
|----|-------------|----------|----------|-------|--------|
| GS-1 | Formal list of security initiatives with MSP role clarity | 2→3 | High | Leadership | Not Started |
| GS-4 | Defined organizational risk tolerance | 2→3 | Medium | Leadership | In Progress |
| GS-6 | Cyber discussion in management meetings | 2→3 | Medium | Leadership | Partial |
| GS-8 | Business unit accountability for cyber risks | 2→3 | Medium | Leadership | Not Started |
| GS-9 | Dedicated cyber budget | 3→4 | Low | Finance | Partial |
| GS-10 | Dedicated security team/director-level lead | 2→3 | Critical | Leadership | **DO NOW** |
| GS-13 | Security authority and governance | 3→4 | Medium | Leadership | Partial |
| GS-15 | Hardware/software assessment process | 3→4 | Medium | IT | Partial |
| GS-18 | Succession planning for key roles | 2→3 | High | HR | **DO NEXT** |
| GS-20 | Documented information security policy | 2→3 | Critical | Legal/IT | **DO NOW** |
| GS-21 | Policy coverage of 10+ security areas | 2→3 | Critical | Legal/IT | **DO NOW** |
| GS-22 | Independent security reviews every 6 months | 3→4 | Medium | IT | Partial |
| GS-26 | Staff qualifications and training | 2→3 | Low | HR | Not Started |
| GS-29 | Background screening policy | 4→5 | Low | HR | Partial |
| GS-30 | Security awareness training program | 2→3 | Critical | HR/IT | **DO NOW** |
| GS-31 | Phishing training and exercises | 3→4 | Medium | HR/IT | Partial |
| GS-34 | Detailed cyber insurance policy | 3→4 | Medium | Leadership | Partial |
| GS-35 | Vendor screening process | 3→4 | Medium | Procurement | In Review |
| GS-36 | Security requirements in contracts | 3→4 | Medium | Legal | Partial |
| GS-39 | External provider assessment | N/A | N/A | N/A | N/A |
| GS-44 | Data destruction on contract termination | 2→3 | Medium | Legal | Partial |

### Network & Infrastructure

| ID | Requirement | Maturity | Priority | Owner | Status |
|----|-------------|----------|----------|-------|--------|
| NI-1 | Complete asset inventory | 2→3 | Medium | IT | In Progress |
| NI-2 | Asset prioritization by classification | 2→3 | Medium | IT | Not Started |
| NI-3 | Complete change management coverage | 3→4 | Medium | IT | Partial |
| NI-4 | Configuration standards | 2→3 | Medium | IT | In Progress |
| NI-5 | Authorized reseller policy | 3→4 | Low | Procurement | Partial |
| NI-6 | Documented firewall configuration | 2→3 | Medium | IT | Partial |
| NI-8 | Default "Deny All" posture | Non-compliant | High | IT | Not Started |
| NI-11 | Layered DMZ strategy | N/A | Medium | IT | Unknown |
| NI-15 | Enhanced wireless security controls | 3→4 | Medium | IT | Partial |
| NI-17 | IDS/IPS with automated remediation | 2→3 | Medium | IT | Partial |
| NI-41 | Endpoint protection (EDR) | 1→3 | Critical | IT | **DO NOW** |
| NI-42 | Email filtering and scanning | 2→3 | Critical | IT | **DO NOW** |
| NI-43-48 | Complete MDM rollout | 2→3 | Critical | IT | **DO NOW** |

### Identity & Access Management

| ID | Requirement | Maturity | Priority | Owner | Status |
|----|-------------|----------|----------|-------|--------|
| IAM-1 | Integrated Azure AD policies | 2→3 | High | IT | **DO NEXT** |
| IAM-2 | Standardized onboarding/offboarding | 2→3 | High | IT | **DO NEXT** |
| IAM-4 | Enterprise password manager | 1→3 | High | IT | **DO NEXT** |
| IAM-5 | Eliminate shared passwords | 2→3 | High | IT | **DO NEXT** |
| IAM-8 | Unified identity processes | 2→3 | High | IT | **DO NEXT** |
| IAM-12 | Universal MFA enforcement | 2→3 | Critical | IT | **DO NOW** |
| IAM-25 | MFA across all tenants | 2→3 | Critical | IT | **DO NOW** |

### Monitoring

| ID | Requirement | Maturity | Priority | Owner | Status |
|----|-------------|----------|----------|-------|--------|
| M-1 | System resource monitoring policies | 1→3 | High | IT | **DO NEXT** |
| M-3 | SIEM log ingestion | 1→3 | High | IT | **DO NEXT** |
| M-8 | Complete log coverage | 1→3 | High | IT | **DO NEXT** |
| M-11 | Incident response team | 1→3 | High | IT | **DO NEXT** |
| M-12 | Incident classification | 1→3 | High | IT | **DO NEXT** |
| M-16 | Knowledge base maintenance | 1→3 | High | IT | **DO NEXT** |

### Resilience

| ID | Requirement | Maturity | Priority | Owner | Status |
|----|-------------|----------|----------|-------|--------|
| E-3 | Optimized malware settings | 2→3 | Medium | IT | **DO NEXT** |
| E-4 | Office 365 security optimization | 2→3 | Medium | IT | **DO NEXT** |
| (BCP) | Business continuity plan | 1→3 | High | IT | Not Started |
| (DR) | DR testing program | 1→3 | High | IT | Not Started |

---

## Appendix B: Document Sources & Verification

### Primary Sources
1. **Head to Toe - Cyber Health Check Workbook - Final 08Jan26.xlsx** (187.4 KB)
   - Source: Riverside Company
   - Date: January 8, 2026
   - Contains: Full capability maturity assessment with scoring

2. **Head to Toe - Cyber Threat Analysis 02Jan2025.pdf** (979.6 KB)
   - Source: Cybeta (via Riverside)
   - Date: January 2, 2026
   - Contains: External threat analysis, Threat Beta scoring

3. **Head to Toe - External Cyber Threat Analysis Summary.docx** (23.2 KB)
   - Source: Cybeta/Riverside
   - Date: January 2, 2026
   - Contains: Executive summary of threat findings

4. **Head to Toe - RISO Baseline Report - Final 08Jan26.pptx** (1.3 MB)
   - Source: Riverside Company
   - Date: January 8, 2026
   - Contains: Executive summary, recommendations, maturity scoring methodology

### Source Verification Status
✅ All documents extracted and analyzed  
✅ No conflicting information identified  
✅ Data cross-referenced between sources  
⚠️ Some "Under Review" items require follow-up for current status

### Data Currency Notes
- MFA statistics point-in-time (January 2026)
- User/device counts may have changed since assessment
- Vulnerability data external-only, point-in-time
- "In Progress" items may have advanced since report date

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-26 | Web-Puppy | Initial consolidation of Riverside requirements |

### Next Review
- **Date:** Monthly until July 8, 2026 deadline
- **Trigger:** When "Under Review" items are completed
- **Owner:** Designated security lead (once GS-10 completed)

---

*This document serves as the authoritative source for Head to Toe Brands security requirements as stipulated by The Riverside Company. All compliance tracking should reference this document as the baseline.*
