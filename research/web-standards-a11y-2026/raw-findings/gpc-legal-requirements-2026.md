# GPC (Global Privacy Control) Legal Requirements - March 2026

**Source**: Global Privacy Control specification, CCPA/CPRA, state privacy laws  
**Status**: As of January 2025  
**Date Extracted**: March 2026

---

## Executive Summary

**Global Privacy Control (GPC)** is a browser signal that communicates a user's request to opt out of the sale or sharing of their personal information. As of January 2025, **four states explicitly require** businesses to honor GPC signals, with **eight additional states** requiring recognition of universal opt-out mechanisms.

**Critical**: GPC is **legally binding** and non-compliance carries **statutory penalties**.

---

## Technical Specification

### HTTP Header

```http
Sec-GPC: 1
```

| Property | Value |
|----------|-------|
| **Header Name** | `Sec-GPC` (case-insensitive) |
| **Valid Values** | `1` (enabled) or absent (disabled) |
| **Transmission** | Sent on every HTTP request |
| **Scope** | Origin receiving request + all embedded resources |
| **Persistence** | Session-scoped (browser manages) |
| **JavaScript API** | `navigator.globalPrivacyControl` (boolean) |
| **W3C Status** | Official W3C Privacy Working Group work item (Nov 2024) |

### JavaScript Detection

```javascript
// Check GPC status
if (navigator.globalPrivacyControl) {
    console.log('GPC is enabled');
}

// Or check header server-side
```

---

## Legal Status by Jurisdiction

### California - CCPA/CPRA

**Statutory Authority**:
- **California Civil Code §1798.135(b)(1)**: "A business that is subject to this title shall treat user-enabled global privacy controls... as a **valid request** submitted pursuant to subdivision (a)"
- **CCPA Regulations §999.315**: "User-enabled global privacy controls... shall be considered a request directly from the consumer"

**Legal Interpretation**:
- **"Shall treat"** = **MANDATORY**, not optional
- **"Valid request"** = Same legal effect as user clicking "Do Not Sell"
- **No additional confirmation required** - signal alone is sufficient
- **Applies immediately** - no grace period

**Penalties**:
- **Intentional violations**: **$7,500 per violation**
- **Unintentional violations**: **$2,500 per violation**
- **Each user interaction** can be a separate violation
- **Example**: 1,000 users × 10 page views × $2,500 = **$25 million exposure**

**California Privacy Protection Agency (CPPA) Enforcement**:
- **2023 Priority**: Honoring opt-out preference signals (including GPC)
- **2024 Enforcement**: First GPC-related enforcement action Q4 2025
- **2025 Trend**: Multi-million dollar settlements

**Example Enforcement**:
- **Healthline.com (July 2025)**: $1.55 million settlement
- **Sephora (August 2022)**: $1.2 million settlement (data sales)
- **Rural lifestyle retailer (September 2025)**: $1.35 million settlement

---

### Colorado - Colorado Privacy Act (CPA)

**Statutory Authority**:
- **CRS §6-1-1306(1)(a)(I)(A)**: "Requires businesses to honor universal opt-out mechanisms such as GPC"

**Effective Date**: July 1, 2023

**Penalties**:
- **$2,000-$20,000 per violation** (CRS §6-1-1313)

---

### Connecticut - Connecticut Data Privacy Act (CTDPA)

**Statutory Authority**:
- **CGS §42-520(a)(1)**: "Controllers shall recognize universal opt-out mechanisms as valid consumer requests"

**Effective Date**: July 1, 2023

**Penalties**:
- **$5,000 per violation** (CGS §42-524)

---

### New Jersey - New Jersey Data Privacy Act

**Status**: As of October 2025, New Jersey law explicitly requires GPC recognition

**Source**: California governor signed new law requiring in-browser opt-out preference signal (October 7, 2025)

---

### Additional States (Universal Opt-Out Required)

Eight additional states require recognition of universal opt-out mechanisms (likely including GPC):

| State | Law | Effective Date |
|-------|-----|----------------|
| Virginia | VCDPA | January 1, 2023 |
| Utah | UCPA (amended) | December 31, 2023 |
| Delaware | DPDPA | January 1, 2025 |
| Iowa | ICDPA | January 1, 2025 |
| New Hampshire | NHPA | January 1, 2025 |
| Nebraska | NDPA | January 1, 2025 |
| Maryland | MDPA | January 1, 2026 |
| Minnesota | MCDPA | July 1, 2025 |

---

## GDPR (European Union)

### Legal Basis

While GDPR does not explicitly reference GPC:

**Article 21 - Right to Object**:
> "The data subject shall have the right to object, on grounds relating to his or her particular situation, at any time to processing of personal data concerning him or her"

GPC signal = clear manifestation of objection to processing.

**EDPB Guidance** (Guidelines 05/2020 on consent):
- Consent mechanisms must be as easy to withdraw as to give
- Technical signals (like GPC) constitute valid withdrawal
- Controllers must honor such signals **without undue delay**

---

## Implementation Requirements

### 1. Server-Side Detection

**Required**: Check `Sec-GPC: 1` header on every request

```python
# FastAPI/Starlette example
from starlette.middleware.base import BaseHTTPMiddleware

class GPCMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Detect GPC (case-insensitive)
        gpc_header = request.headers.get("Sec-GPC", "").strip()
        gpc_enabled = gpc_header == "1"
        
        # Store in request state
        request.state.gpc_enabled = gpc_enabled
        
        # Persist in session
        if gpc_enabled and hasattr(request, "session"):
            request.session["gpc_enabled"] = True
        
        response = await call_next(request)
        return response
```

### 2. Cookie Management

**When GPC enabled**:

**BLOCK**:
- Analytics cookies (Google Analytics, Adobe Analytics)
- Marketing cookies
- Third-party tracking cookies
- Social media widgets
- A/B testing cookies
- Personalization cookies

**ALLOW** (Essential):
- Session cookies (authentication)
- Security cookies (CSRF tokens)
- Functional cookies (preferences that don't track)

```python
# Example cookie filtering
def set_cookie_if_permitted(response, name, value, essential=False, request=None):
    if essential or not getattr(request.state, "gpc_enabled", False):
        response.set_cookie(name, value)
    else:
        # Log for audit but don't set cookie
        logger.info(f"Cookie '{name}' blocked due to GPC")
```

### 3. Third-Party Data Sharing

**When GPC enabled, disable or anonymize**:

1. **Analytics**:
   - Google Analytics: Set `anonymizeIp: true`, disable `allowAdFeatures`
   - Azure Application Insights: Server-side only, strip PII

2. **CDN**:
   - Strip `Referer` headers
   - Disable user-agent fingerprinting

3. **Third-Party APIs**:
   - Don't share user identifiers (email, user ID, tenant ID)
   - Use anonymized/aggregated data only

4. **Email Services**:
   - Disable tracking pixels
   - Disable link click tracking

### 4. Session Persistence

**GPC applies for duration of user session**:

```python
# On first request with GPC
if gpc_enabled:
    request.session["privacy_mode"] = "gpc_enabled"
    request.session["analytics_disabled"] = True
    request.session["third_party_sharing_disabled"] = True

# On subsequent requests (even without header)
if request.session.get("gpc_enabled"):
    request.state.gpc_enabled = True
```

### 5. User Experience

**PROHIBITED** (CCPA violation):
- ❌ "We detected GPC. Click here to confirm."
- ❌ Cookie consent banner that ignores GPC
- ❌ Requiring login to complete opt-out
- ❌ CAPTCHA for GPC-enabled requests

**PERMITTED**:
- ✅ Silent GPC enforcement
- ✅ Confirmation message: "Your privacy preferences are honored."
- ✅ Offering opt-in for specific features: "Enable analytics to see insights."

### 6. Audit Logging

**Required**: Log GPC detection (privacy-preserving)

```json
{
  "event": "gpc_signal_honored",
  "timestamp": "2026-03-26T14:23:11Z",
  "path": "/api/dashboard",
  "actions_taken": [
    "disabled_analytics_cookies",
    "blocked_third_party_tracking"
  ]
  // DO NOT LOG: session_id, user_id, ip_address, user_agent
}
```

**Retention**: 90 days (CCPA §1798.130)

---

## Browser Support

### Native Support (2026)

| Browser | Support | Version | Default |
|---------|---------|---------|---------|
| **Firefox** | ✅ Native | 120+ | Settings toggle |
| **Brave** | ✅ Native | 1.42+ | Enabled by default |
| **DuckDuckGo** | ✅ Native | All | Enabled by default |
| **Safari** | ⚠️ Extension | — | Privacy extensions available |
| **Chrome** | ⚠️ Extension | — | OptMeowt, Privacy Badger |
| **Edge** | ⚠️ Extension | — | Chrome extensions compatible |

**Estimated Reach**: ~15-20% of web users (growing 40% YoY)

---

## Compliance Checklist

### P0 - Critical (Legal Requirement)

| # | Requirement | Status | Test |
|---|-------------|--------|------|
| 1 | Detect `Sec-GPC: 1` header | Required | `curl -H "Sec-GPC: 1" http://localhost:8000/` |
| 2 | Store in request state | Required | Verify `request.state.gpc_enabled` |
| 3 | Session persistence | Required | Test with multiple requests |
| 4 | Disable analytics cookies | Required | Check for `_ga`, `_gid` cookies |
| 5 | Disable tracking pixels | Required | Check network tab |
| 6 | Privacy-preserving logging | Required | No PII in logs |
| 7 | No confirmation required | Required | No additional user action |

### P1 - High Priority

| # | Requirement | Status | Test |
|---|-------------|--------|------|
| 8 | Azure App Insights filtering | Recommended | Server-side telemetry only |
| 9 | Third-party API anonymization | Recommended | Strip user identifiers |
| 10 | CDN referer stripping | Recommended | Check headers |
| 11 | Privacy policy update | Recommended | Mention GPC compliance |
| 12 | Session expiry handling | Recommended | Reset on logout |

### P2 - Medium Priority

| # | Requirement | Status | Test |
|---|-------------|--------|------|
| 13 | JavaScript API support | Optional | `navigator.globalPrivacyControl` |
| 14 | User-facing confirmation | Optional | Banner: "Privacy mode enabled" |
| 15 | Dashboard for GPC status | Optional | Privacy settings page |

---

## Testing

### Unit Tests

```python
def test_gpc_header_detection():
    """Test that Sec-GPC: 1 is correctly detected."""
    client = TestClient(app)
    response = client.get("/", headers={"Sec-GPC": "1"})
    assert response.request.state.gpc_enabled is True

def test_gpc_session_persistence():
    """Test GPC persists across requests."""
    client = TestClient(app)
    response1 = client.get("/", headers={"Sec-GPC": "1"})
    session = response1.cookies.get("session")
    
    response2 = client.get("/", cookies={"session": session})
    assert response2.request.state.gpc_enabled is True

def test_gpc_blocks_analytics_cookies():
    """Test analytics cookies blocked when GPC enabled."""
    client = TestClient(app)
    response = client.get("/", headers={"Sec-GPC": "1"})
    assert "_ga" not in response.cookies
```

### Manual Testing

1. **Firefox**:
   - Enable "Tell websites not to sell or share my data"
   - Navigate to application
   - Verify `Sec-GPC: 1` in Network tab

2. **curl**:
   ```bash
   curl -H "Sec-GPC: 1" -v http://localhost:8000/
   # Verify no analytics cookies in response
   ```

3. **Browser Console**:
   ```javascript
   // Check JavaScript API
   navigator.globalPrivacyControl
   // Should be true if enabled
   ```

---

## Timeline

**Critical Path**:
- Week 1: Implement GPC middleware
- Week 2: Update templates, disable analytics
- Week 3: Testing and validation
- Week 4: Documentation and rollout

**Ongoing**:
- Monthly: Compliance audits
- Quarterly: Privacy policy review
- Annually: Legal requirement updates

---

## References

### Legal
- CCPA: https://oag.ca.gov/privacy/ccpa
- CCPA Regulations: https://oag.ca.gov/privacy/ccpa/regs
- CPRA: https://cppa.ca.gov/

### Technical
- GPC Spec: https://w3c.github.io/gpc/
- GPC Website: https://globalprivacycontrol.org/
- W3C Privacy WG: https://www.w3.org/groups/wg/privacy/

### Enforcement
- CPPA Enforcement: https://cppa.ca.gov/enforcement/
- Healthline Settlement: https://oag.ca.gov/news/press-releases/2025-07-01

---

**Classification**: P0 - Legal Compliance (Critical)  
**Risk**: $2,500-$7,500 per violation  
**Deadline**: Immediate implementation required

*Extracted: March 2026*  
*Source Tier: 1 (Legal/Regulatory)*
