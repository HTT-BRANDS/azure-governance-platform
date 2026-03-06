# Privacy-by-Design UI Patterns

**Date:** March 6, 2026  
**Scope:** GDPR/CCPA Compliance, GPC Support, Consent Management  
**Target:** Azure Governance Platform

---

## Quick Reference

| Pattern | GDPR | CCPA | Implementation Complexity |
|---------|------|------|--------------------------|
| Cookie Banner | Required | Required | Low |
| Preference Center | Required | Required | Medium |
| GPC Support | Optional | Required | Low |
| Data Export | Required | Required | High |
| Account Deletion | Required | Required | High |
| Just-in-Time Consent | Best Practice | Best Practice | Medium |

---

## 1. Cookie Consent Banner

### Implementation

```html
<!-- templates/components/cookie-banner.html -->
<div 
  id="cookie-banner"
  role="region"
  aria-label="Cookie preferences"
  class="cookie-banner"
  data-nosnippet
>
  <div class="cookie-banner__content">
    <p class="cookie-banner__text">
      We use cookies and similar technologies to enhance your experience, 
      analyze traffic, and serve relevant content. 
      <a href="/privacy/cookies" class="cookie-banner__link">
        Learn more about cookies
      </a>
    </p>
    
    <div class="cookie-banner__actions">
      <!-- Accept All -->
      <button 
        type="button"
        class="btn btn--primary"
        data-action="accept-all"
        aria-label="Accept all cookies"
      >
        Accept All
      </button>
      
      <!-- Reject Non-Essential -->
      <button 
        type="button"
        class="btn btn--secondary"
        data-action="reject-optional"
        aria-label="Reject optional cookies"
      >
        Reject Optional
      </button>
      
      <!-- Customize -->
      <button 
        type="button"
        class="btn btn--text"
        data-action="open-preferences"
        aria-label="Customize cookie preferences"
      >
        Customize
      </button>
    </div>
  </div>
</div>
```

```javascript
// static/js/cookie-banner.js
class CookieBanner {
  constructor() {
    this.banner = document.getElementById('cookie-banner');
    this.consentKey = 'cookie-consent';
    this.gpcSignal = this.detectGPC();
    
    this.init();
  }
  
  init() {
    // Check for existing consent
    const existingConsent = this.getStoredConsent();
    
    // If GPC signal detected, respect it
    if (this.gpcSignal && !existingConsent) {
      this.applyGPCPreferences();
      return;
    }
    
    // Show banner if no consent
    if (!existingConsent) {
      this.show();
    }
  }
  
  detectGPC() {
    // Global Privacy Control detection
    return navigator.globalPrivacyControl === true ||
           document.doNotTrack === '1' ||
           navigator.doNotTrack === '1';
  }
  
  applyGPCPreferences() {
    // GPC = opt-out of sale/sharing
    this.saveConsent({
      essential: true,
      analytics: false,
      marketing: false,
      personalization: false,
      timestamp: new Date().toISOString(),
      gpcApplied: true
    });
    
    this.logGPCApplication();
  }
  
  saveConsent(preferences) {
    localStorage.setItem(this.consentKey, JSON.stringify(preferences));
    
    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('cookieConsentUpdated', {
      detail: preferences
    }));
  }
  
  show() {
    this.banner.hidden = false;
    this.banner.focus();
    
    // Trap focus within banner
    this.trapFocus();
  }
  
  hide() {
    this.banner.hidden = true;
    this.releaseFocus();
  }
  
  trapFocus() {
    // Focus management for accessibility
    const focusableElements = this.banner.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  new CookieBanner();
});
```

```python
# app/api/routes/privacy.py
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])

class CookieConsent(BaseModel):
    essential: bool = True
    analytics: bool = False
    marketing: bool = False
    personalization: bool = False
    timestamp: datetime
    gpc_applied: bool = False

@router.post("/consent")
async def record_consent(
    consent: CookieConsent,
    request: Request
):
    """Record user's cookie consent preferences."""
    
    # Detect GPC signal
    gpc_header = request.headers.get("Sec-GPC", "0")
    gpc_signal = gpc_header == "1"
    
    # If GPC is enabled, override non-essential preferences
    if gpc_signal:
        consent.analytics = False
        consent.marketing = False
        consent.personalization = False
        consent.gpc_applied = True
    
    # Store in database
    await store_consent_preferences(
        user_id=get_user_id(request),
        consent=consent,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    # Log for audit
    await log_consent_event(consent)
    
    return {"status": "success", "gpc_honored": gpc_signal}

@router.get("/gpc-status")
async def check_gpc_status(request: Request):
    """Check if GPC signal is present."""
    gpc_header = request.headers.get("Sec-GPC", "0")
    return {
        "gpc_enabled": gpc_header == "1",
        "message": "Global Privacy Control signal detected" if gpc_header == "1" else "No GPC signal"
    }
```

---

## 2. Preference Center

### Implementation

```html
<!-- templates/pages/privacy-preferences.html -->
{% extends "base.html" %}

{% block content %}
<div class="container">
  <h1>Privacy Preferences</h1>
  <p class="lead">
    Manage your privacy settings. Changes take effect immediately.
  </p>
  
  <!-- GPC Status -->
  <div id="gpc-status" class="alert" hidden>
    <strong>Global Privacy Control Detected</strong>
    <p>
      Your browser has signaled that you do not want your personal information 
      sold or shared. We have automatically opted you out of data sharing.
    </p>
  </div>
  
  <!-- Consent Categories -->
  <form id="privacy-preferences-form" class="preferences-form">
    
    <!-- Essential (Required) -->
    <fieldset class="preference-category">
      <legend>
        Essential
        <span class="badge badge--required">Required</span>
      </legend>
      <p>These cookies are necessary for the website to function.</p>
      <label class="toggle">
        <input 
          type="checkbox" 
          checked 
          disabled
          name="essential"
          aria-describedby="essential-desc"
        >
        <span class="toggle__slider"></span>
        <span class="sr-only">Essential cookies enabled (cannot be disabled)</span>
      </label>
      <p id="essential-desc" class="sr-only">
        Essential cookies cannot be disabled. These include session management, 
        security, and basic functionality.
      </p>
    </fieldset>
    
    <!-- Analytics -->
    <fieldset class="preference-category">
      <legend>Analytics</legend>
      <p>Help us understand how you use our website.</p>
      <label class="toggle">
        <input 
          type="checkbox" 
          name="analytics"
          id="analytics-toggle"
          aria-describedby="analytics-desc"
        >
        <span class="toggle__slider"></span>
        <span class="toggle__label">Enable analytics cookies</span>
      </label>
      <p id="analytics-desc" class="preference-description">
        We use these cookies to analyze site traffic and improve our services. 
        Data is aggregated and anonymized where possible.
      </p>
    </fieldset>
    
    <!-- Marketing -->
    <fieldset class="preference-category">
      <legend>Marketing</legend>
      <p>Allow us to show you relevant content.</p>
      <label class="toggle">
        <input 
          type="checkbox" 
          name="marketing"
          id="marketing-toggle"
          aria-describedby="marketing-desc"
        >
        <span class="toggle__slider"></span>
        <span class="toggle__label">Enable marketing cookies</span>
      </label>
      <p id="marketing-desc" class="preference-description">
        These cookies help us show you relevant advertisements and content. 
        You have the right to opt-out under CCPA.
      </p>
    </fieldset>
    
    <!-- Personalization -->
    <fieldset class="preference-category">
      <legend>Personalization</legend>
      <p>Customize your experience.</p>
      <label class="toggle">
        <input 
          type="checkbox" 
          name="personalization"
          id="personalization-toggle"
          aria-describedby="personalization-desc"
        >
        <span class="toggle__slider"></span>
        <span class="toggle__label">Enable personalization</span>
      </label>
      <p id="personalization-desc" class="preference-description">
        We use this data to personalize your dashboard and recommendations.
      </p>
    </fieldset>
    
    <!-- Actions -->
    <div class="form-actions">
      <button type="submit" class="btn btn--primary">
        Save Preferences
      </button>
      <button type="button" class="btn btn--secondary" id="reject-all">
        Reject All Optional
      </button>
    </div>
    
  </form>
  
  <!-- CCPA Rights -->
  <section class="ccpa-rights" aria-labelledby="ccpa-heading">
    <h2 id="ccpa-heading">Your California Privacy Rights</h2>
    <ul class="rights-list">
      <li>
        <a href="/privacy/know">Right to Know</a> - See what data we have about you
      </li>
      <li>
        <a href="/privacy/delete">Right to Delete</a> - Request deletion of your data
      </li>
      <li>
        <a href="/privacy/correct">Right to Correct</a> - Update inaccurate information
      </li>
      <li>
        <a href="/privacy/opt-out">Right to Opt-Out</a> - Stop sale/sharing of data
      </li>
      <li>
        <a href="/privacy/limit">Right to Limit</a> - Restrict use of sensitive data
      </li>
    </ul>
  </section>
  
  <!-- Data Export -->
  <section class="data-export" aria-labelledby="export-heading">
    <h2 id="export-heading">Export Your Data</h2>
    <p>
      Download a copy of your personal information. We will email you when 
      your export is ready (up to 45 days).
    </p>
    <button 
      type="button" 
      class="btn btn--outline"
      id="request-export"
    >
      Request Data Export
    </button>
  </section>
  
  <!-- Account Deletion -->
  <section class="account-deletion" aria-labelledby="deletion-heading">
    <h2 id="deletion-heading">Delete Your Account</h2>
    <p>
      Permanently delete your account and personal information. This action 
      cannot be undone.
    </p>
    <button 
      type="button" 
      class="btn btn--danger"
      id="request-deletion"
    >
      Request Account Deletion
    </button>
  </section>
  
</div>

<script>
// Load current preferences
document.addEventListener('DOMContentLoaded', async () => {
  const response = await fetch('/api/v1/privacy/preferences');
  const preferences = await response.json();
  
  // Set toggle states
  document.getElementById('analytics-toggle').checked = preferences.analytics;
  document.getElementById('marketing-toggle').checked = preferences.marketing;
  document.getElementById('personalization-toggle').checked = preferences.personalization;
  
  // Show GPC notice if applicable
  if (preferences.gpc_applied) {
    document.getElementById('gpc-status').hidden = false;
    document.getElementById('marketing-toggle').disabled = true;
    document.getElementById('personalization-toggle').disabled = true;
  }
});

// Handle form submission
document.getElementById('privacy-preferences-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const preferences = {
    essential: true,
    analytics: formData.get('analytics') === 'on',
    marketing: formData.get('marketing') === 'on',
    personalization: formData.get('personalization') === 'on',
    timestamp: new Date().toISOString()
  };
  
  const response = await fetch('/api/v1/privacy/consent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preferences)
  });
  
  if (response.ok) {
    showNotification('Preferences saved successfully', 'success');
  } else {
    showNotification('Failed to save preferences', 'error');
  }
});
</script>
{% endblock %}
```

---

## 3. Just-in-Time Consent

### Pattern

Show consent request when user accesses a feature that requires specific data.

```javascript
// static/js/consent-manager.js
class ConsentManager {
  constructor() {
    this.consentStore = new Map();
  }
  
  // Check if consent needed before action
  async requireConsent(feature, dataTypes) {
    const existingConsent = this.getConsent(feature);
    
    if (existingConsent && existingConsent.granted) {
      return true;
    }
    
    // Show just-in-time consent dialog
    const granted = await this.showConsentDialog(feature, dataTypes);
    
    if (granted) {
      this.recordConsent(feature, dataTypes);
    }
    
    return granted;
  }
  
  async showConsentDialog(feature, dataTypes) {
    return new Promise((resolve) => {
      const dialog = document.createElement('dialog');
      dialog.innerHTML = `
        <form method="dialog">
          <h2>Allow ${feature}?</h2>
          <p>This feature needs access to:</p>
          <ul>
            ${dataTypes.map(type => `<li>${this.describeDataType(type)}</li>`).join('')}
          </ul>
          <p>
            <a href="/privacy/data-use" target="_blank">
              Learn how we use this data
            </a>
          </p>
          <div class="dialog-actions">
            <button value="deny">Not Now</button>
            <button value="allow" class="btn--primary">Allow</button>
          </div>
        </form>
      `;
      
      document.body.appendChild(dialog);
      dialog.showModal();
      
      dialog.addEventListener('close', () => {
        const granted = dialog.returnValue === 'allow';
        document.body.removeChild(dialog);
        resolve(granted);
      });
    });
  }
  
  describeDataType(type) {
    const descriptions = {
      'location': 'Your precise location',
      'contacts': 'Your contact list',
      'calendar': 'Your calendar events',
      'camera': 'Camera access',
      'microphone': 'Microphone access'
    };
    return descriptions[type] || type;
  }
}

// Usage example
const consentManager = new ConsentManager();

// Before accessing location
document.getElementById('map-button').addEventListener('click', async () => {
  const allowed = await consentManager.requireConsent(
    'Azure Region Map',
    ['location']
  );
  
  if (allowed) {
    initMap();
  } else {
    showFallback('Location access required for this feature');
  }
});
```

---

## 4. Data Minimization Patterns

### Progressive Profiling

```javascript
// Collect data incrementally
class ProgressiveProfiler {
  constructor() {
    this.collectedData = new Set();
  }
  
  async requestData(field, reason) {
    // Check if already collected
    if (this.collectedData.has(field)) {
      return this.getStoredValue(field);
    }
    
    // Only ask if necessary
    if (!this.isDataNecessary(field, reason)) {
      return null;
    }
    
    // Request data with clear purpose
    const value = await this.promptForData(field, reason);
    
    if (value) {
      this.collectedData.add(field);
      this.storeValue(field, value, reason);
    }
    
    return value;
  }
  
  isDataNecessary(field, reason) {
    // Don't collect if not required for this purpose
    const requiredFields = this.getRequiredFields(reason);
    return requiredFields.includes(field);
  }
  
  promptForData(field, reason) {
    return new Promise((resolve) => {
      // Show modal explaining why we need this data
      const modal = createDataRequestModal(field, reason);
      modal.onComplete = resolve;
    });
  }
}
```

---

## 5. CCPA Compliance Implementation

### API Routes

```python
# app/api/routes/ccpa.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

router = APIRouter(prefix="/api/v1/ccpa", tags=["ccpa"])

class DataExportRequest(BaseModel):
    email: EmailStr
    format: str = "json"  # json, csv, pdf

class DataCorrectionRequest(BaseModel):
    field: str
    current_value: str
    proposed_value: str
    reason: Optional[str] = None

@router.post("/export-request")
async def request_data_export(
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Handle CCPA Right to Know / Data Portability.
    
    - Must respond within 45 days
    - Must provide data in readily usable format
    - Must cover preceding 12 months
    """
    
    # Validate request limit (max 2 per year)
    request_count = await get_export_request_count(user.id, days=365)
    if request_count >= 2:
        raise HTTPException(
            status_code=429,
            detail="Maximum 2 export requests per year allowed"
        )
    
    # Queue export job
    export_id = await create_export_job(
        user_id=user.id,
        email=request.email,
        format=request.format
    )
    
    # Send confirmation
    await send_export_request_confirmation(user.email, export_id)
    
    return {
        "message": "Export request received",
        "export_id": export_id,
        "expected_completion": "within 45 days"
    }

@router.get("/personal-data")
async def get_personal_data(
    user: User = Depends(get_current_user)
):
    """
    Return categories and specific pieces of personal information.
    """
    
    data = await collect_personal_data(user.id)
    
    return {
        "categories_collected": [
            {
                "category": "Identifiers",
                "examples": ["name", "email", "IP address"],
                "sources": ["user input", "analytics"],
                "purposes": ["authentication", "communication"],
                "third_parties": ["AWS", "Azure AD"]
            },
            {
                "category": "Commercial Information",
                "examples": ["subscription tier"],
                "sources": ["Stripe"],
                "purposes": ["billing"],
                "third_parties": ["Stripe"]
            }
        ],
        "specific_data": data,  # Filtered to user's data only
        "retention_periods": await get_retention_policies()
    }

@router.delete("/delete-request")
async def request_data_deletion(
    user: User = Depends(get_current_user)
):
    """
    Handle CCPA Right to Delete.
    
    Must delete and notify service providers.
    Exceptions apply (legal obligations, security, etc.)
    """
    
    # Create deletion request
    deletion_id = await create_deletion_request(user.id)
    
    # Start deletion workflow
    await initiate_deletion_workflow(user.id, deletion_id)
    
    # Notify service providers
    await notify_service_providers(user.id, "DELETION_REQUEST")
    
    return {
        "message": "Deletion request received",
        "deletion_id": deletion_id,
        "expected_completion": "within 45 days",
        "exceptions": [
            "Data required for legal compliance",
            "Data necessary for security purposes"
        ]
    }

@router.post("/correction-request")
async def request_data_correction(
    correction: DataCorrectionRequest,
    user: User = Depends(get_current_user)
):
    """
    Handle CPRA Right to Correct.
    
    New in CPRA (January 2023).
    """
    
    correction_id = await create_correction_request(
        user_id=user.id,
        field=correction.field,
        current_value=correction.current_value,
        proposed_value=correction.proposed_value,
        reason=correction.reason
    )
    
    # Verify the proposed value
    if not await verify_correction(user.id, correction):
        raise HTTPException(
            status_code=400,
            detail="Could not verify correction"
        )
    
    # Apply correction
    await apply_correction(user.id, correction)
    
    # Notify downstream systems
    await propagate_correction(user.id, correction)
    
    return {
        "message": "Correction applied successfully",
        "correction_id": correction_id
    }

@router.post("/opt-out")
async def opt_out_of_sale(
    user: User = Depends(get_current_user)
):
    """
    Handle CCPA Right to Opt-Out of Sale/Sharing.
    
    Must be honored immediately.
    Must wait 12 months before re-requesting opt-in.
    """
    
    # Record opt-out
    await record_opt_out(user.id)
    
    # Immediately stop sharing/selling
    await disable_data_sharing(user.id)
    
    # Update all systems
    await propagate_opt_out(user.id)
    
    return {
        "message": "Opt-out recorded",
        "effective_date": datetime.utcnow().isoformat(),
        "re_opt_in_date": (datetime.utcnow().replace(year=datetime.utcnow().year + 1)).isoformat()
    }

@router.post("/limit-use")
async def limit_sensitive_data_use(
    categories: List[str],
    user: User = Depends(get_current_user)
):
    """
    Handle CPRA Right to Limit Use of Sensitive Personal Information.
    
    New in CPRA (January 2023).
    Applies to: SSN, financial data, geolocation, contents of communications,
    genetic data, biometrics, health/sexual info, racial/religious info.
    """
    
    valid_categories = [
        "ssn", "financial", "geolocation", "communications",
        "genetic", "biometrics", "health", "racial_ethnic"
    ]
    
    for category in categories:
        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}"
            )
    
    await limit_sensitive_data(user.id, categories)
    
    return {
        "message": "Sensitive data use limited",
        "limited_categories": categories,
        "allowed_uses": ["providing requested services"]
    }
```

---

## 6. GPC (Global Privacy Control) Implementation

### Middleware

```python
# app/core/gpc_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class GPCMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and honor Global Privacy Control signals.
    
    CCPA requires honoring GPC as a valid opt-out mechanism.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check for GPC header
        gpc_header = request.headers.get("Sec-GPC", "0")
        gpc_enabled = gpc_header == "1"
        
        # Also check JavaScript property (for SSR)
        js_gpc = request.headers.get("X-GPC-JS", "false")
        js_gpc_enabled = js_gpc.lower() == "true"
        
        # Set GPC status on request state
        request.state.gpc_enabled = gpc_enabled or js_gpc_enabled
        
        # If GPC is enabled, ensure opt-out is applied
        if request.state.gpc_enabled:
            # This will be checked in business logic
            request.state.data_sharing_allowed = False
            request.state.targeted_advertising_allowed = False
        
        response = await call_next(request)
        
        # Add GPC support header to response
        response.headers["GPC-Support"] = "1"
        
        return response

# Add to FastAPI app
app.add_middleware(GPCMiddleware)
```

### Business Logic Integration

```python
# app/services/privacy_service.py
class PrivacyService:
    def __init__(self, request: Request):
        self.request = request
        self.gpc_enabled = getattr(request.state, 'gpc_enabled', False)
    
    def can_share_data(self, user_id: str) -> bool:
        """
        Check if data can be shared/sold for user.
        
        Honors:
        1. GPC signal (immediate)
        2. User's explicit opt-out (stored)
        3. CPRA sensitive data limits
        """
        
        # GPC takes precedence
        if self.gpc_enabled:
            return False
        
        # Check stored preference
        user_pref = self.get_user_privacy_preference(user_id)
        if user_pref and user_pref.opt_out:
            return False
        
        # Check sensitive data limits
        if self.is_sensitive_data_limited(user_id):
            return False
        
        return True
    
    def log_gpc_honored(self, user_id: str, context: str):
        """Audit log for GPC compliance."""
        
        self.audit_logger.info(
            "GPC honored",
            extra={
                "user_id": user_id,
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": self.request.client.host,
                "user_agent": self.request.headers.get("user-agent")
            }
        )
```

---

## 7. Audit and Compliance Logging

```python
# app/services/audit_service.py
from datetime import datetime
from typing import Optional, Dict, Any

class PrivacyAuditService:
    """
    Comprehensive audit logging for privacy compliance.
    
    Required for CCPA/GDPR compliance and breach investigation.
    """
    
    async def log_consent_event(
        self,
        user_id: str,
        event_type: str,  # granted, withdrawn, updated
        consent_details: Dict[str, Any],
        ip_address: str,
        user_agent: str
    ):
        """
        Log consent events with full context.
        Required for demonstrating compliance.
        """
        
        await self.store_audit_record({
            "event_type": "consent",
            "consent_event": event_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "consent": consent_details,
            "context": {
                "ip_address": self.hash_ip(ip_address),
                "user_agent": user_agent,
                "gpc_enabled": consent_details.get("gpc_applied", False),
                "referrer": consent_details.get("referrer")
            },
            "retention_days": 365  # Keep for 1 year minimum
        })
    
    async def log_data_access(
        self,
        user_id: str,
        data_subject_id: str,  # Whose data was accessed
        data_categories: List[str],
        purpose: str,
        legal_basis: str
    ):
        """
        Log data access for Right to Know and accountability.
        """
        
        await self.store_audit_record({
            "event_type": "data_access",
            "accessed_by": user_id,
            "data_subject": data_subject_id,
            "categories": data_categories,
            "purpose": purpose,
            "legal_basis": legal_basis,
            "timestamp": datetime.utcnow().isoformat(),
            "retention_days": 2555  # 7 years for legal purposes
        })
    
    async def log_deletion(
        self,
        user_id: str,
        deletion_scope: str,  # partial, full
        exceptions: List[str],
        initiated_by: str  # user, admin, system
    ):
        """
        Log deletion requests and fulfillment.
        Required for Right to Delete compliance.
        """
        
        await self.store_audit_record({
            "event_type": "deletion",
            "user_id": user_id,
            "scope": deletion_scope,
            "exceptions": exceptions,
            "initiated_by": initiated_by,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "initiated",
            "retention_days": 2555  # 7 years
        })
    
    async def log_data_sharing(
        self,
        user_id: str,
        recipient: str,
        data_categories: List[str],
        purpose: str,
        user_opted_out: bool
    ):
        """
        Log all data sharing/selling events.
        Required for CCPA disclosure requirements.
        """
        
        if user_opted_out:
            # This should not happen - log as error
            await self.log_compliance_violation(
                "Data shared despite opt-out",
                {"user_id": user_id, "recipient": recipient}
            )
            return
        
        await self.store_audit_record({
            "event_type": "data_sharing",
            "user_id": user_id,
            "recipient": recipient,
            "categories": data_categories,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat(),
            "retention_days": 2555  # 7 years
        })
```

---

## Testing

### Unit Tests

```python
# tests/unit/test_privacy.py
import pytest
from fastapi.testclient import TestClient

class TestGPC:
    def test_gpc_header_detected(self, client: TestClient):
        response = client.get(
            "/api/v1/privacy/gpc-status",
            headers={"Sec-GPC": "1"}
        )
        assert response.status_code == 200
        assert response.json()["gpc_enabled"] is True
    
    def test_gpc_honored_in_data_sharing(self, client: TestClient, auth_headers):
        # Set GPC header
        response = client.post(
            "/api/v1/some-feature",
            headers={**auth_headers, "Sec-GPC": "1"}
        )
        
        # Verify no data sharing occurred
        # Check audit logs
        logs = get_audit_logs(event_type="data_sharing")
        assert len(logs) == 0  # No sharing should occur

class TestCCPARights:
    def test_right_to_know(self, client: TestClient, auth_headers):
        response = client.get(
            "/api/v1/ccpa/personal-data",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories_collected" in data
        assert "specific_data" in data
    
    def test_right_to_delete(self, client: TestClient, auth_headers):
        response = client.delete(
            "/api/v1/ccpa/delete-request",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "deletion_id" in response.json()
    
    def test_export_rate_limit(self, client: TestClient, auth_headers):
        # Make 3 requests (limit is 2 per year)
        for _ in range(3):
            response = client.post(
                "/api/v1/ccpa/export-request",
                headers=auth_headers,
                json={"email": "test@example.com", "format": "json"}
            )
        
        # Third request should fail
        assert response.status_code == 429
```

---

## References

- [CCPA Regulations](https://oag.ca.gov/privacy/ccpa)
- [Global Privacy Control](https://globalprivacycontrol.org/)
- [GDPR Guidelines](https://gdpr.eu/)
- [W3C Privacy-by-Design](https://www.w3.org/Privacy/)

---

*Last updated: March 6, 2026*
