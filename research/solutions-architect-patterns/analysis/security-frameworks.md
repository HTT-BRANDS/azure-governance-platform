# Analysis: Security-by-Design Integration

## Overview

Security-by-Design integrates security considerations at the design phase rather than as an afterthought. This analysis covers frameworks and practices for automated/AI-assisted security workflows.

## Leading Security Frameworks (2024-2025)

### 1. STRIDE

**Origin:** Microsoft (1999)  
**Status:** Industry standard, widely adopted  
**Best For:** General threat modeling, Microsoft environments

**Categories:**
| Threat | Description | Example Mitigation |
|--------|-------------|-------------------|
| **S**poofing | Impersonating something/someone | Authentication, MFA |
| **T**ampering | Modifying data/code | Integrity checks, signing |
| **R**epudiation | Denying actions | Logging, auditing |
| **I**nformation Disclosure | Exposing data | Encryption, access controls |
| **D**enial of Service | Crashing systems | Rate limiting, redundancy |
| **E**levation of Privilege | Unauthorized access | Authorization checks, RBAC |

**Process:**
1. Create data flow diagrams (DFDs)
2. Apply STRIDE per element
3. Identify threats
4. Rate and prioritize
5. Mitigate and validate

**Automation Potential:** ⭐⭐⭐☆☆ (Medium)
- DFD generation can be semi-automated
- Threat identification benefits from AI assistance
- Mitigation validation can be automated

### 2. PASTA (Process for Attack Simulation and Threat Analysis)

**Origin:** OWASP (Risk-centric)  
**Status:** Growing adoption, financial services favorite  
**Best For:** Risk-focused organizations, compliance-driven

**Seven Stages:**
1. Define objectives and business context
2. Define technical scope
3. Application decomposition
4. Threat analysis
5. Vulnerability analysis
6. Attack enumeration
7. Risk and impact analysis

**Automation Potential:** ⭐⭐⭐⭐☆ (Good)
- Vulnerability analysis automated (SAST/DAST)
- Attack enumeration can use threat intelligence
- Risk scoring can be automated

### 3. OWASP Threat Modeling

**Resource:** https://owasp.org/www-project-threat-modeling/  
**Status:** Community-driven, actively maintained  
**Best For:** Web applications, OWASP alignment

**Key Approaches:**
- **Threat Modeling Manifesto** (values/principles)
- **Cheat Sheet Series**
- **Threat Dragon** (tool)
- **Threat Modeling Process**

**Four Question Framework:**
1. What are we building?
2. What can go wrong?
3. What are we going to do about it?
4. Did we do a good enough job?

**Automation Potential:** ⭐⭐⭐⭐☆ (Good)
- Threat Dragon tool provides automation
- Integration with CI/CD possible
- Question 1 & 4 benefit from AI assistance

### 4. Attack Trees

**Origin:** Schneier (1999)  
**Status:** Mature, used in high-security environments  
**Best For:** Complex attack scenarios, detailed analysis

**Structure:**
- Root: Attack goal
- Nodes: Sub-goals
- Leaves: Attack methods

**Automation Potential:** ⭐⭐⭐☆☆ (Medium)
- Tree generation from patterns
- AI assistance for completeness
- Validation against known attacks

### 5. CVSS (Common Vulnerability Scoring System)

**Version:** 4.0 (2023)  
**Status:** Industry standard for vulnerability scoring  
**Use:** Prioritization, risk communication

**Metrics:**
- Base (exploitability, impact)
- Threat (exploit maturity)
- Environmental (business context)
- Supplemental (safety, automation)

**Automation Potential:** ⭐⭐⭐⭐⭐ (High)
- Fully automatable scoring
- Tooling widely available
- Integrated in scanners

## Framework Comparison

| Framework | Learning Curve | Time Investment | Output Quality | Automation Fit |
|-----------|---------------|-----------------|----------------|----------------|
| **STRIDE** | Medium | Low-Medium | Good | Medium |
| **PASTA** | High | High | Excellent | Good |
| **OWASP** | Low | Low-Medium | Good | Good |
| **Attack Trees** | Medium | High | Excellent | Medium |
| **CVSS** | Low | Low | Standard | Excellent |

## Automated/AI-Assisted Security Workflows

### 1. Design Phase Integration

**Pattern: Security Design Review Checkpoint**
```
Feature Design → Security Review → ADR Documentation → Implementation
                    ↓
            [STRIDE Analysis]
            [Threat Modeling]
            [Risk Assessment]
```

**Implementation:**
```markdown
<!-- ADR Template Extension for Security -->
## Security Considerations

### Threat Model
- **Asset:** {what are we protecting}
- **Threats:** {STRIDE/PASTA analysis}
- **Mitigations:** {how we address them}

### Risk Assessment
- **Likelihood:** {High/Medium/Low}
- **Impact:** {High/Medium/Low}
- **Residual Risk:** {after mitigations}

### Compliance Requirements
- [ ] Data classification applied
- [ ] Access controls defined
- [ ] Audit logging specified
- [ ] Encryption requirements met
```

### 2. AI-Assisted Threat Modeling

**Capabilities:**
- Generate DFDs from code/documentation
- Suggest threats based on patterns
- Recommend mitigations from knowledge base
- Validate completeness

**Limitations:**
- Context understanding
- Novel threat recognition
- Business logic comprehension
- False positives

**Best Practice:**
> "AI assists, human validates"

### 3. Security-as-Code Patterns

**Pattern 1: Security Fitness Functions**
```python
def test_security_headers_present():
    """ADR-0015: All API responses include security headers."""
    response = client.get('/health')
    assert 'X-Content-Type-Options' in response.headers
    assert response.headers['X-Frame-Options'] == 'DENY'
```

**Pattern 2: Security Gates in CI**
```yaml
# .github/workflows/security.yml
name: Security Compliance
on: [pull_request]
jobs:
  threat-model-compliance:
    runs-on: ubuntu-latest
    steps:
      - name: Check ADR Security Section
        run: python scripts/check_adr_security.py
      - name: Run Security Tests
        run: pytest tests/security/
```

## Multi-Dimensional Analysis

### Security (Primary)
- **Rating:** ⭐⭐⭐⭐⭐ (Critical)
- Frameworks provide structured security analysis
- Automation reduces human error
- Continuous validation prevents drift

### Cost
- **Rating:** ⭐⭐⭐☆☆ (Medium)
- Tool licensing (some commercial)
- Time investment for modeling
- Prevents expensive breaches

### Implementation Complexity
- **Rating:** ⭐⭐⭐☆☆ (Medium)
- STRIDE: Moderate learning curve
- PASTA: Complex, requires expertise
- OWASP: Accessible to most teams

### Stability
- **Rating:** ⭐⭐⭐⭐⭐ (High)
- All frameworks mature
- Industry adoption widespread
- Standards-backed

### Optimization
- **Rating:** ⭐⭐⭐☆☆ (Medium)
- Manual effort still required
- Automation assists but doesn't replace
- Iterative improvement needed

### Compatibility
- **Rating:** ⭐⭐⭐⭐☆ (Good)
- Frameworks language-agnostic
- Tools vary by platform
- Azure integration available

### Maintenance
- **Rating:** ⭐⭐⭐☆☆ (Medium)
- Threat models require updates
- Tool updates needed
- Review cycle recommended

## Recommendations for Azure Governance Platform

### Immediate Actions

1. **Adopt STRIDE for Threat Modeling**
   - Simple, well-documented
   - Fits Azure ecosystem
   - Good balance of rigor vs. effort

2. **Extend ADR Template**
   ```markdown
   ## Security Considerations
   
   ### STRIDE Analysis
   | Threat | Present | Mitigation |
   |--------|---------|------------|
   | Spoofing | Yes/No | {mitigation} |
   | Tampering | Yes/No | {mitigation} |
   | Repudiation | Yes/No | {mitigation} |
   | Information Disclosure | Yes/No | {mitigation} |
   | DoS | Yes/No | {mitigation} |
   | Elevation of Privilege | Yes/No | {mitigation} |
   
   ### Compliance Mapping
   - [ ] Riverside IAM requirements
   - [ ] Azure Security Baseline
   - [ ] OWASP Top 10
   ```

### Short-term (Month 1)

1. **Implement Security Fitness Functions**
   ```python
   # tests/security/test_azure_security.py
   def test_azure_credential_secure_usage():
       """ADR-0020: Use DefaultAzureCredential only"""
       for file in Path('app').rglob('*.py'):
           content = file.read_text()
           assert 'ClientSecretCredential' not in content, \
               f"Hardcoded credentials in {file}"
   
   def test_api_rate_limiting_configured():
       """ADR-0021: Rate limiting on all public endpoints"""
       # Check FastAPI middleware configuration
       pass
   ```

2. **Integrate with Azure Security Tools**
   - Microsoft Defender for Cloud
   - Azure Policy compliance scanning
   - Key Vault access monitoring

### Medium-term (Quarter 1)

1. **Threat Modeling as Code**
   ```yaml
   # threat-models/user-auth.yaml
   component: User Authentication
   description: Azure AD SSO integration
   
   threats:
     - type: spoofing
       description: Fake Azure AD tokens
       mitigation: Validate token signature
       verification: test_token_validation.py
       
     - type: elevation
       description: Privilege escalation
       mitigation: RBAC enforcement
       verification: test_rbac_enforcement.py
   ```

2. **Automated Threat Model Updates**
   - Generate from code analysis
   - Compare against baseline
   - Flag changes for review

## Security-Specific ADR Categories

### Category: Security Architecture
- Authentication methods
- Authorization patterns
- Encryption standards
- Secret management

### Category: Compliance
- Data residency
- Audit requirements
- Retention policies
- Access logging

### Category: Threat Mitigation
- DDoS protection
- Injection prevention
- XSS protection
- CSRF mitigation

## Integration with Azure Security

### Native Tools to Leverage

| Tool | Purpose | Integration |
|------|---------|-------------|
| **Microsoft Entra ID** | Identity | SSO, MFA enforcement |
| **Azure Policy** | Compliance | Automated remediation |
| **Key Vault** | Secrets | ADR-0005: Centralized secrets |
| **Defender for Cloud** | Security posture | Continuous monitoring |
| **Sentinel** | SIEM | Threat detection |

### Azure-Specific Security Patterns

1. **Managed Identity Over Service Principals**
   - Reduces credential management
   - Automatic rotation
   - Better audit trail

2. **Azure Lighthouse for Multi-Tenant**
   - Centralized governance
   - Delegated access
   - Consistent policies

3. **Private Endpoints**
   - Network isolation
   - Reduced attack surface
   - Compliance requirements

---

## References

- OWASP Threat Modeling: https://owasp.org/www-project-threat-modeling/
- STRIDE: https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats
- PASTA: https://owasp.org/www-pdf-archive/ASDC12-PASTA.pdf
- CVSS v4.0: https://www.first.org/cvss/
- Azure Security Baseline: https://docs.microsoft.com/en-us/security/benchmark/azure/
