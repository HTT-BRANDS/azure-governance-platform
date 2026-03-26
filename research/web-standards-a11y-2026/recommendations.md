# Project-Specific Recommendations - UI/UX Audit

## Executive Summary

Based on analysis of the Azure Governance Platform codebase and current web standards (March 2026), this document provides prioritized, actionable recommendations for accessibility and standards compliance.

**Critical Finding**: GPC (Global Privacy Control) implementation is **mandatory** and currently **missing**. This represents a P0 legal compliance gap.

---

## P0 - Critical (Immediate Action Required)

### 1. Implement GPC (Global Privacy Control) Middleware

**Why Critical**:
- Legally binding in 4 states (CA, CO, CT, NJ) as of January 2025
- $2,500-$7,500 per violation under CCPA §1798.155
- CPPA began enforcement actions Q4 2025

**Implementation**:

Create `app/core/gpc.py`:
```python
"""Global Privacy Control (GPC) middleware for CCPA/CPRA compliance.

GPC signals via Sec-GPC: 1 HTTP header are legally binding opt-out requests.
Reference: CCPA §1798.135, https://w3c.github.io/gpc/
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)

class GPCMiddleware(BaseHTTPMiddleware):
    """Detect and enforce Global Privacy Control signals."""
    
    async def dispatch(self, request: Request, call_next):
        # Detect GPC header (case-insensitive per spec)
        gpc_header = request.headers.get("Sec-GPC", "").strip()
        gpc_enabled = gpc_header == "1"
        
        # Store in request state for downstream access
        request.state.gpc_enabled = gpc_enabled
        
        # Persist in session for subsequent requests
        if gpc_enabled and hasattr(request, "session"):
            request.session["gpc_enabled"] = True
            request.session["analytics_disabled"] = True
        elif hasattr(request, "session"):
            # Check if already enabled in session
            request.state.gpc_enabled = request.session.get("gpc_enabled", False)
        
        # Privacy-preserving audit log (NO PII)
        if gpc_enabled:
            logger.info(
                "GPC signal honored",
                extra={
                    "event": "gpc_detected",
                    "path": request.url.path,
                    "method": request.method,
                    # DO NOT LOG: ip, user_id, session_id, user_agent
                }
            )
        
        response = await call_next(request)
        
        # Add GPC response header to indicate support
        response.headers["Accept-CH"] = "Sec-GPC"
        
        return response


def is_gpc_enabled(request) -> bool:
    """Check if GPC is enabled for current request."""
    return getattr(request.state, "gpc_enabled", False) or \
           getattr(request, "session", {}).get("gpc_enabled", False)
```

Update `app/main.py`:
```python
from app.core.gpc import GPCMiddleware

# Add middleware (order matters - add early in pipeline)
app.add_middleware(GPCMiddleware)
```

**Template Updates** (`app/templates/base.html`):
```html
<!-- Conditional analytics based on GPC -->
{% if not request.state.gpc_enabled %}
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={{ ga_id }}"></script>
    <script nonce="{{ request.state.csp_nonce }}">
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', '{{ ga_id }}');
    </script>
{% endif %}

<!-- Optional: Privacy confirmation -->
{% if request.state.gpc_enabled %}
    <div class="sr-only" role="status" aria-live="polite">
        Privacy mode enabled — analytics disabled
    </div>
{% endif %}
```

**Validation**:
```python
# tests/unit/test_gpc.py
def test_gpc_header_detection():
    response = client.get("/", headers={"Sec-GPC": "1"})
    assert response.request.state.gpc_enabled is True

def test_gpc_session_persistence():
    # First request with GPC
    response1 = client.get("/", headers={"Sec-GPC": "1"})
    session_cookie = response1.cookies.get("session")
    
    # Second request without header
    response2 = client.get("/", cookies={"session": session_cookie})
    assert response2.request.state.gpc_enabled is True
```

**Timeline**: Complete within 7 days
**Owner**: Backend team
**Validation**: See `docs/security/gpc-compliance.md` checklist

---

### 2. Upgrade axe-core to 4.11.1

**Current**: v4.10.x (estimated)
**Latest**: v4.11.1 (January 2025)

**Update**:
```bash
npm install axe-core@4.11.1 --save-dev
```

**Check `package.json`**:
```json
{
  "devDependencies": {
    "axe-core": "^4.11.1"
  }
}
```

**What's New in 4.11.x**:
- Improved WCAG 2.2 AA support
- Better focus indicator detection
- Enhanced semantic HTML validation
- Custom element support improvements

**Timeline**: Complete within 3 days
**Owner**: Frontend/DevOps

---

## P1 - High Priority (Next 30 Days)

### 3. WCAG 2.2 Manual Testing - 7 Non-Automatable Criteria

#### 3.1 Focus Not Obscured (2.4.11) - AA

**Current Status**: ⚠️ Review Required

**What to Check**:
1. Sticky header doesn't obscure focused elements
2. Sticky footer doesn't obscure focused elements
3. Cookie banners/modals handled correctly

**Project-Specific Areas**:
- Navigation bar (`nav` in `base.html`) - sticky positioning
- HTMX progress bar (`#htmx-progress-bar`) - fixed positioning
- Toast notifications (if any)

**Test Procedure**:
1. Open any page
2. Tab through all interactive elements
3. Verify focused element is at least partially visible
4. Check at different viewport sizes (mobile, tablet, desktop)

**Remediation**:
```css
/* Add to accessibility.css */
html {
    scroll-padding-top: 64px; /* Match sticky header height */
    scroll-padding-bottom: 60px; /* Match sticky footer height */
}
```

#### 3.2 Focus Appearance (2.4.13) - AAA (Optional but Recommended)

**Current**: 3px solid outline at 3:1 contrast ✅

**Verification**:
```css
/* Current in accessibility.css */
:focus-visible {
    outline: 3px solid #0053e2;
    outline-offset: 2px;
    border-radius: 2px;
}
```

**Check**:
- Contrast ratio of focus indicator vs background ≥ 3:1
- Focus indicator size ≥ 2 CSS pixel thick perimeter

#### 3.3 Dragging Movements (2.5.7) - AA

**Current Status**: ✅ Likely Pass (No drag interactions found)

**What to Check**:
- Any drag-to-reorder functionality?
- Drag sliders for budget/resource allocation?
- Map panning?

**Project Review**:
- Dashboard: Chart.js charts (check if draggable)
- Riverside compliance: Any drag-drop?
- Resource management: Any drag-sorting?

**If dragging exists**, provide alternative:
```html
<!-- Instead of drag-only -->
<button aria-label="Move item up">↑</button>
<button aria-label="Move item down">↓</button>
```

#### 3.4 Target Size (2.5.8) - AA

**Current**: ✅ Already compliant

**Verification**:
- `accessibility.css` sets `min-height: 44px; min-width: 44px;`
- This exceeds the 24x24 CSS pixel minimum

**Exceptions to Check**:
- Inline links in text (allowed exception)
- User-agent controlled elements (browser default)

#### 3.5 Consistent Help (3.2.6) - A

**Current Status**: ⚠️ Review Required

**What to Check**:
- Help links in consistent location across pages
- Contact information in same relative order
- Self-help resources consistently positioned

**Project Review**:
- Footer help links
- Riverside help/documentation links
- Dashboard help tooltips

**Requirement**:
Help mechanism must be in same relative order across pages.

#### 3.6 Redundant Entry (3.3.7) - A

**Current Status**: ⚠️ Review Required

**What to Check**:
- Multi-step forms (preflight, onboarding)
- Auto-population of previously entered data
- Available for user selection

**Project Areas**:
- `/onboarding` - tenant setup wizard
- `/preflight` - configuration steps
- `/riverside` - compliance requirements

**Implementation**:
```html
<!-- Auto-populate from previous entry -->
<input type="text" name="tenant_name" 
       value="{{ previous_values.tenant_name }}" 
       autocomplete="organization">
```

#### 3.7 Accessible Authentication (3.3.8) - AA

**Current Status**: ✅ Likely Pass

**What to Check**:
- No cognitive function tests required (CAPTCHA without alternative)
- Object recognition ("Select all images with cars") must have alternative
- Password managers work

**Project Review**:
- Login at `/login` - OIDC/OAuth flow
- Check for CAPTCHA usage
- Verify password manager auto-fill works

---

### 4. HTMX Accessibility Enhancements

#### 4.1 Focus Management

**Current Issue**: HTMX swaps don't manage focus automatically

**Implementation**:
```javascript
// Add to app/static/js/navigation/index.js

// Focus management for HTMX swaps
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // If swap target has hx-swap="outerHTML", restore focus
    if (evt.detail.swapStyle === 'outerHTML') {
        const focusable = evt.detail.elt.querySelector(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable) {
            focusable.focus();
        }
    }
});

// Announce HTMX events to screen readers
document.body.addEventListener('htmx:afterSwap', function(evt) {
    const announcer = document.getElementById('page-announcer');
    if (announcer) {
        // Get page title or meaningful content
        const title = evt.detail.elt.querySelector('h1, h2');
        if (title) {
            announcer.textContent = `Loaded: ${title.textContent}`;
        } else {
            announcer.textContent = 'Content updated';
        }
    }
});
```

#### 4.2 ARIA Current State

**Current Issue**: Navigation doesn't show current page

**Implementation**:
```html
<!-- In base.html navigation -->
<a href="/" 
   class="nav-item {% if request.path == '/' %}nav-active{% endif %}"
   {% if request.path == '/' %}aria-current="page"{% endif %}>
    Dashboard
</a>
```

#### 4.3 HTMX Loading States

**Current**: Good implementation with `htmx-indicator`

**Enhancement**:
```html
<!-- Add aria-busy to loading regions -->
<div id="riverside-badge"
     hx-get="/partials/riverside-badge"
     hx-trigger="load, every 60s"
     hx-target="#riverside-badge"
     hx-swap="innerHTML"
     hx-indicator="#riverside-loading"
     aria-live="polite"
     aria-busy="false">
</div>

<script>
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    evt.detail.elt.setAttribute('aria-busy', 'true');
});
document.body.addEventListener('htmx:afterRequest', function(evt) {
    evt.detail.elt.setAttribute('aria-busy', 'false');
});
</script>
```

---

### 5. Core Web Vitals Optimization

#### 5.1 LCP (Largest Contentful Paint)

**Current Assessment**:
- Server-side rendering helps LCP
- Chart.js may block LCP if not deferred

**Recommendations**:
```html
<!-- Defer non-critical scripts -->
<script src="https://cdn.jsdelivr.net/npm/chart.js" 
        defer 
        nonce="{{ request.state.csp_nonce }}"></script>

<!-- Or use loading="lazy" for below-fold images -->
<img src="/static/assets/logo.svg" loading="lazy" alt="Company logo">
```

#### 5.2 INP (Interaction to Next Paint)

**HTMX Considerations**:
- Ensure HTMX requests resolve quickly
- Use `hx-trigger="change"` instead of `input` for expensive operations
- Consider debouncing for search/filter inputs

```javascript
// Debounce search inputs
htmx.config.requestDelay = 300; // ms
```

#### 5.3 CLS (Cumulative Layout Shift)

**HTMX Considerations**:
- Reserve space for async content
- Set `min-height` on containers that load HTMX content

```html
<!-- Reserve space for HTMX-loaded content -->
<div id="dashboard-cards" 
     hx-get="/api/dashboard/cards"
     hx-trigger="load"
     style="min-height: 200px;">
    <div class="htmx-indicator">Loading...</div>
</div>
```

---

## P2 - Medium Priority (Next 90 Days)

### 6. Tailwind CSS v4 Accessibility Utilities

**Current**: Project appears to be using Tailwind v4 CSS-first approach

**Verify**:
```bash
cat package.json | grep tailwind
```

**Leverage New Features**:
```css
/* prefers-reduced-motion */
@media (prefers-reduced-motion: reduce) {
    .transition-custom {
        transition: none;
    }
}

/* Tailwind v4 built-in: */
/* motion-safe:* and motion-reduce:* variants */
```

### 7. Manual Testing Checklist

**Quarterly Accessibility Audit**:

| Test | Tool | Frequency |
|------|------|-----------|
| Keyboard navigation | Manual | Monthly |
| Screen reader (NVDA) | NVDA | Quarterly |
| Color contrast | axe DevTools | Monthly |
| Focus indicators | Manual | Monthly |
| Zoom 200% | Browser | Quarterly |
| Reduced motion | OS setting | Quarterly |

### 8. Documentation Updates

**Update**:
1. `DESIGN_SYSTEM_AUDIT.md` - add WCAG 2.2 criteria
2. `docs/patterns/privacy-by-design.md` - add GPC patterns
3. `SECURITY_IMPLEMENTATION.md` - add GPC section
4. Create `docs/ACCESSIBILITY.md` - comprehensive guide

---

## Testing Strategy

### Automated Testing

**Current**: axe-core in CI/CD

**Enhancement**:
```python
# tests/e2e/test_accessibility.py
def test_wcag_22_aa_compliance(page):
    """Test page compliance with WCAG 2.2 AA."""
    page.goto("http://localhost:8000/")
    
    # Run axe-core
    results = page.evaluate("""
        async () => {
            return await axe.run();
        }
    """)
    
    # Check for violations
    assert len(results['violations']) == 0, f"Accessibility violations: {results['violations']}"
```

### Manual Testing Checklist

**Create `tests/accessibility/manual-checklist.md`**:
```markdown
## Manual Accessibility Checklist

### Keyboard Navigation
- [ ] Tab order is logical
- [ ] All interactive elements reachable
- [ ] Focus visible on all elements
- [ ] No keyboard traps

### Screen Reader (NVDA)
- [ ] Page title announced
- [ ] Headings in proper hierarchy
- [ ] Form labels associated
- [ ] Dynamic content announced

### Focus Not Obscured (WCAG 2.4.11)
- [ ] Sticky header doesn't hide focus
- [ ] Sticky footer doesn't hide focus
- [ ] Modal dialogs trap focus

### Target Size (WCAG 2.5.8)
- [ ] All targets ≥ 24x24px
- [ ] Adequate spacing between targets
```

---

## Success Metrics

### GPC Compliance
- [ ] Middleware implemented
- [ ] Templates updated
- [ ] Tests passing
- [ ] Privacy policy updated

### WCAG 2.2 AA
- [ ] 0 axe-core violations
- [ ] Manual testing complete
- [ ] Focus Not Obscured verified
- [ ] Target Size verified

### Core Web Vitals
- [ ] LCP ≤ 2.5s (mobile)
- [ ] INP ≤ 200ms
- [ ] CLS ≤ 0.1

---

## Appendix: Quick Reference

### WCAG 2.2 New Criteria (7 Manual Tests)

| Criterion | Level | Automation | Action |
|-----------|-------|------------|--------|
| 2.4.11 Focus Not Obscured | AA | None | Check sticky elements |
| 2.4.13 Focus Appearance | AAA | None | Verify contrast 3:1 |
| 2.5.7 Dragging Movements | AA | None | Check drag alternatives |
| 2.5.8 Target Size | AA | Partial | Verify 24x24px |
| 3.2.6 Consistent Help | A | None | Check help placement |
| 3.3.7 Redundant Entry | A | Limited | Check form prefill |
| 3.3.8 Accessible Authentication | AA | None | Check CAPTCHA alternatives |

### GPC Implementation Checklist

- [ ] `GPCMiddleware` created
- [ ] Middleware registered in `main.py`
- [ ] `request.state.gpc_enabled` accessible in templates
- [ ] Analytics conditionally loaded
- [ ] Session persistence implemented
- [ ] Privacy-preserving logging
- [ ] Unit tests created
- [ ] Integration tests created
- [ ] Manual QA complete

---

*Recommendations compiled: March 2026*  
*For: Azure Governance Platform UI/UX Audit*
