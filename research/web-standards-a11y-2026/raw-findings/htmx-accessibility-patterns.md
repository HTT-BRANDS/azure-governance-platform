# HTMX Accessibility Best Practices

**Source**: HTMX Documentation, ARIA APG, Community Best Practices  
**Version**: HTMX 1.9.12 (matches project)  
**Date Extracted**: March 2026

---

## Executive Summary

HTMX enables server-rendered applications to have rich interactions while maintaining strong accessibility foundations. Since HTMX uses standard HTML patterns with progressive enhancement, it works well with assistive technologies when implemented correctly.

**Key Principle**: "HTMX applications should follow standard HTML accessibility recommendations."

---

## Core Accessibility Concepts

### Progressive Enhancement

HTMX's core philosophy aligns with accessibility:
- Works without JavaScript (graceful degradation)
- Uses standard HTML semantics
- Server renders full content
- JavaScript enhances rather than replaces

**Benefits**:
- Screen readers get full content immediately
- No JavaScript hydration delays
- SEO-friendly
- Works with JavaScript disabled

---

## Focus Management

### The Problem

HTMX swaps content without browser navigation, which means:
- Focus may be lost when content changes
- Screen readers may not announce updates
- Users may be disoriented

### Solutions

#### 1. Focus Restoration After Swap

```javascript
// Add to app/static/js/navigation/index.js

document.body.addEventListener('htmx:afterSwap', function(evt) {
    // If the swapped element contains the previously focused element,
    // restore focus to it
    const focused = document.activeElement;
    if (focused && evt.detail.elt.contains(focused)) {
        focused.focus();
    }
});
```

#### 2. Set Focus on New Content

```javascript
// Focus first interactive element after swap
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Only if this was a major content update (e.g., navigation)
    if (evt.detail.swapStyle === 'outerHTML') {
        const firstFocusable = evt.detail.elt.querySelector(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (firstFocusable) {
            firstFocusable.focus();
        }
    }
});
```

#### 3. Focus Container Pattern

```html
<!-- Set focus on container after swap -->
<div id="modal-content" 
     hx-get="/modal/content"
     hx-target="#modal-content"
     hx-swap="innerHTML"
     tabindex="-1">
    <!-- Content loaded here -->
</div>

<script>
document.getElementById('modal-content').addEventListener('htmx:afterSwap', function() {
    this.focus();
});
</script>
```

---

## ARIA Live Regions

### The Problem

HTMX updates content dynamically. Screen readers need to know when content changes.

### Solution: aria-live Regions

**Project Implementation** (in `base.html`):
```html
<!-- Screen Reader Announcer -->
<div id="page-announcer" class="sr-only" aria-live="polite" aria-atomic="true"></div>
```

**Use for HTMX Updates**:
```javascript
// Announce HTMX events to screen readers
document.body.addEventListener('htmx:afterSwap', function(evt) {
    const announcer = document.getElementById('page-announcer');
    if (announcer) {
        // Get page title or meaningful content
        const title = evt.detail.elt.querySelector('h1, h2');
        if (title) {
            announcer.textContent = `Page updated: ${title.textContent}`;
        } else {
            announcer.textContent = 'Content updated';
        }
    }
});
```

### aria-live Values

| Value | Use Case | Example |
|-------|----------|---------|
| `polite` | Non-urgent updates | Page content updates |
| `assertive` | Critical alerts | Form errors, confirmations |
| `off` | No announcement | Decorative updates |

### ARIA Atomic

```html
<!-- aria-atomic="true": Announce entire region -->
<div aria-live="polite" aria-atomic="true">
    <p>Status: <span id="status">Loading...</span></p>
</div>

<!-- aria-atomic="false": Announce only changed node -->
<div aria-live="polite" aria-atomic="false">
    <p>Items: <span id="count">5</span></p>
</div>
```

---

## Keyboard Navigation

### HTMX-Boosted Links

**Current Project Implementation**:
```html
<!-- In base.html navigation -->
<nav hx-boost="true" hx-select="main" hx-target="main" hx-swap="outerHTML settle:150ms">
```

**Keyboard Accessibility**:
- `hx-boost` preserves standard link behavior
- Tab navigation works automatically
- Enter/Space activation works
- Focus indicators must be visible

**Enhancement: Focus Indicator**:
```css
/* Ensure focus visible on boosted links */
[hx-boost] a:focus-visible,
a[hx-boost]:focus-visible {
    outline: 3px solid #0053e2;
    outline-offset: 2px;
}
```

### Keyboard Shortcuts

**Use sparingly** and document:
```html
<button hx-get="/save" accesskey="s">
    Save <span class="sr-only">(Alt+S)</span>
</button>
```

---

## Loading States

### Current Project Implementation

```html
<!-- HTMX Progress Bar -->
<div id="htmx-progress-bar" aria-hidden="true"></div>

<!-- Loading indicator -->
<div id="nav-loading-indicator" class="htmx-indicator">
    <span class="sr-only">Loading</span>
</div>
```

### Accessibility Enhancement

```html
<!-- Add aria-busy for live regions -->
<div id="dynamic-content"
     hx-get="/api/data"
     hx-target="#dynamic-content"
     aria-live="polite"
     aria-busy="false">
    <div class="htmx-indicator">Loading...</div>
</div>

<script>
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    if (evt.detail.target.hasAttribute('aria-live')) {
        evt.detail.target.setAttribute('aria-busy', 'true');
    }
});

document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.target.hasAttribute('aria-live')) {
        evt.detail.target.setAttribute('aria-busy', 'false');
    }
});
</script>
```

---

## Current Page Indication

### The Problem

With `hx-boost`, the page doesn't reload, so screen readers don't announce navigation.

### Solution

**Add aria-current to navigation**:
```html
<!-- In base.html navigation -->
<a href="/" 
   class="nav-item {% if request.path == '/' %}nav-active{% endif %}"
   {% if request.path == '/' %}aria-current="page"{% endif %}>
    Dashboard
</a>
```

**Programmatically with HTMX**:
```javascript
// Update aria-current after navigation
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Remove aria-current from all nav items
    document.querySelectorAll('[aria-current="page"]').forEach(el => {
        el.removeAttribute('aria-current');
    });
    
    // Add to current page
    const currentPath = window.location.pathname;
    document.querySelectorAll('nav a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.setAttribute('aria-current', 'page');
        }
    });
});
```

---

## Modal Dialogs

### HTMX Modal Pattern

```html
<!-- Trigger -->
<button hx-get="/modal/content"
        hx-target="#modal"
        hx-swap="innerHTML"
        aria-haspopup="dialog"
        aria-expanded="false">
    Open Modal
</button>

<!-- Modal container -->
<div id="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <!-- HTMX loads content here -->
</div>
```

### Focus Management for Modals

```javascript
let lastFocusedElement = null;

document.body.addEventListener('htmx:beforeSwap', function(evt) {
    // Store last focused element before modal opens
    if (evt.detail.target.id === 'modal') {
        lastFocusedElement = document.activeElement;
    }
});

document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'modal') {
        // Focus first element in modal
        const firstFocusable = evt.detail.target.querySelector(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (firstFocusable) {
            firstFocusable.focus();
        }
    }
});

// Close modal and restore focus
document.getElementById('modal').addEventListener('close', function() {
    if (lastFocusedElement) {
        lastFocusedElement.focus();
    }
});
```

---

## Form Handling

### Error Messages

```html
<form hx-post="/api/submit" hx-target="#form-result">
    <label for="email">Email</label>
    <input type="email" id="email" name="email" required
           aria-required="true"
           aria-describedby="email-error">
    <div id="email-error" role="alert" aria-live="assertive"></div>
    
    <button type="submit">Submit</button>
</form>

<div id="form-result" aria-live="polite"></div>
```

### Server Response with Errors

```html
<!-- Server returns this on validation error -->
<div id="email-error">
    <p>Please enter a valid email address.</p>
</div>
```

---

## Skip Links

**Current Project Implementation**:
```html
<a href="#main-content" class="skip-link">Skip to main content</a>
```

**With HTMX**:
- Skip links work normally
- Ensure `#main-content` exists after HTMX swaps
- May need to refocus after navigation

```javascript
// Restore skip link functionality after HTMX navigation
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Skip link should work on new content
    document.querySelector('.skip-link').addEventListener('click', function(e) {
        e.preventDefault();
        const main = document.getElementById('main-content');
        if (main) {
            main.setAttribute('tabindex', '-1');
            main.focus();
        }
    });
});
```

---

## Screen Reader Testing

### Test Scenarios

1. **Navigation**:
   - Tab through navigation
   - Activate link with Enter
   - Verify new page announced
   - Verify focus in logical place

2. **Form Submission**:
   - Fill form
   - Submit
   - Verify success/error announced
   - Verify focus on error or success message

3. **Dynamic Content**:
   - Trigger HTMX request
   - Verify loading announced
   - Verify new content announced
   - Verify focus managed

4. **Modal Dialogs**:
   - Open modal
   - Verify focus trapped
   - Close modal
   - Verify focus restored

### Recommended Screen Readers

- **NVDA** (Windows) - Free, widely used
- **JAWS** (Windows) - Industry standard
- **VoiceOver** (macOS/iOS) - Built-in
- **TalkBack** (Android) - Built-in

---

## HTMX Configuration for Accessibility

```javascript
// htmx.config options for accessibility
htmx.config = {
    // Allow focus to be restored after swap
    defaultFocusScroll: false,
    
    // Disable hx-boost for specific links (external, downloads)
    allowEval: false, // Security: disable eval
    
    // Custom swap style for accessibility
    defaultSwapStyle: 'innerHTML',
    defaultSwapDelay: 0,
    
    // History - ensure proper focus management
    historyEnabled: true,
    historyCacheSize: 10,
    refreshOnHistoryMiss: true
};
```

---

## Common Anti-patterns

### ❌ Bad: No Focus Management
```html
<div hx-get="/content" hx-swap="outerHTML">
    <!-- Focus lost when this is replaced -->
</div>
```

### ✅ Good: Preserve Focus
```html
<div id="content-container">
    <div hx-get="/content" hx-target="this">
        <!-- Focus preserved within container -->
    </div>
</div>
```

### ❌ Bad: No Loading Announcement
```html
<button hx-get="/data" hx-target="#result">Load</button>
<div id="result"></div>
<!-- No indication that loading is happening -->
```

### ✅ Good: Loading Announcement
```html
<button hx-get="/data" hx-target="#result">Load</button>
<div id="result" aria-live="polite" aria-busy="false">
    <div class="htmx-indicator">Loading data...</div>
</div>
```

### ❌ Bad: Silent Navigation
```html
<nav hx-boost="true">
    <a href="/page2">Page 2</a>
</nav>
<!-- No announcement when navigating -->
```

### ✅ Good: Announced Navigation
```html
<nav hx-boost="true" hx-select="main" hx-target="main">
    <a href="/page2">Page 2</a>
</nav>
<div id="page-announcer" class="sr-only" aria-live="polite"></div>

<script>
document.body.addEventListener('htmx:afterSwap', function() {
    document.getElementById('page-announcer').textContent = 
        `Navigated to: ${document.title}`;
});
</script>
```

---

## Project-Specific Recommendations

### For Azure Governance Platform

**Current State** (from `base.html` analysis):
- ✅ Skip link implemented
- ✅ ARIA live region present
- ✅ HTMX indicators with `sr-only` text
- ⚠️ Focus management needs enhancement
- ⚠️ `aria-current` navigation not implemented

**Recommended Implementation**:

1. **Add to `app/static/js/navigation/index.js`**:
```javascript
// Focus management and announcements
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Announce navigation
    const announcer = document.getElementById('page-announcer');
    if (announcer) {
        const title = document.querySelector('h1, h2');
        announcer.textContent = title ? 
            `Loaded: ${title.textContent}` : 
            'Page updated';
    }
    
    // Update navigation current state
    document.querySelectorAll('nav a').forEach(link => {
        link.removeAttribute('aria-current');
        if (link.getAttribute('href') === window.location.pathname) {
            link.setAttribute('aria-current', 'page');
        }
    });
});

// Skip link enhancement
document.querySelector('.skip-link')?.addEventListener('click', function(e) {
    e.preventDefault();
    const main = document.getElementById('main-content');
    if (main) {
        main.setAttribute('tabindex', '-1');
        main.focus();
        main.addEventListener('blur', function() {
            main.removeAttribute('tabindex');
        }, { once: true });
    }
});
```

2. **Update `base.html` navigation**:
```html
<a href="/" 
   class="nav-item {% if request.path == '/' %}nav-active{% endif %}"
   {% if request.path == '/' %}aria-current="page"{% endif %}>
    Dashboard
</a>
```

---

## References

- HTMX Documentation: https://htmx.org/docs/
- ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/
- MDN ARIA Live Regions: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions
- Inclusive Design Patterns: https://inclusive-design.patterns/

---

*Extracted: March 2026*  
*Source Tier: 2 (Community Best Practices)*
