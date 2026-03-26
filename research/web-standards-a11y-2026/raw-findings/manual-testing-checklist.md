# Manual Accessibility Testing Checklist

**Based on**: WCAG 2.2, HTMX best practices, and industry standards  
**Date**: March 2026  
**Purpose**: The 43% of WCAG 2.2 AA issues that cannot be detected by automated tools

---

## Executive Summary

**Automated testing coverage**: ~57% of WCAG 2.2 AA issues can be detected by tools like axe-core  
**Manual testing required**: 43% of issues require human evaluation

**The 7 criteria requiring manual testing**:
1. 2.4.11 Focus Not Obscured (AA) - Sticky elements hiding focus
2. 2.4.13 Focus Appearance (AAA) - Focus indicator visibility
3. 2.5.7 Dragging Movements (AA) - Alternative input methods
4. 2.5.8 Target Size (AA) - Pointer target sizing (partial automation)
5. 3.2.6 Consistent Help (A) - Help location consistency
6. 3.3.7 Redundant Entry (A) - Form auto-population
7. 3.3.8 Accessible Authentication (AA) - Cognitive function alternatives

---

## Testing Environment Setup

### Required Tools

1. **Screen Readers**:
   - NVDA (Windows) - Free
   - JAWS (Windows) - Industry standard
   - VoiceOver (macOS/iOS) - Built-in
   - TalkBack (Android) - Built-in

2. **Browser DevTools**:
   - Chrome DevTools Accessibility panel
   - Firefox Accessibility Inspector
   - axe DevTools extension

3. **Manual Testing Tools**:
   - Color contrast analyzer
   - WAVE browser extension
   - HeadingsMap extension
   - TabA11y (tab order checker)

### Browser Matrix

| Browser | Version | Screen Reader | Notes |
|---------|---------|---------------|-------|
| Chrome | Latest | NVDA, JAWS | Primary testing |
| Firefox | Latest | NVDA | Secondary testing |
| Safari | Latest | VoiceOver | macOS testing |
| Edge | Latest | NVDA, JAWS | Enterprise testing |

### Device Matrix

| Device | Viewport | Zoom Level | Notes |
|--------|----------|------------|-------|
| Desktop | 1920x1080 | 100%, 200%, 400% | Standard |
| Tablet | 768x1024 | 100% | iPad |
| Mobile | 375x667 | 100% | iPhone |
| Mobile | 360x640 | 100% | Android |

---

## WCAG 2.2 Manual Testing Criteria

### 1. Focus Not Obscured (2.4.11) - AA

**Automated Detection**: None

**Test Procedure**:

1. **Sticky Header Test**:
   - Open page with sticky header
   - Scroll to middle of page
   - Tab backwards (Shift+Tab) to elements near top
   - ✅ Verify focused element is at least partially visible
   - ❌ Fail if completely hidden by header

2. **Sticky Footer Test**:
   - Scroll to bottom of page
   - Tab backwards to last few elements
   - ✅ Verify focused element is at least partially visible
   - ❌ Fail if completely hidden by footer

3. **Modal/Popover Test**:
   - Open modal/popover
   - Tab to elements underneath
   - ✅ Verify can dismiss with Escape
   - ❌ Fail if cannot dismiss or see focused element

**HTMX-Specific**:
- Test after HTMX navigation (`hx-boost`)
- Test after HTMX partial updates
- Verify focus visible after content swaps

**Remediation**:
```css
html {
    scroll-padding-top: 80px; /* Match header height */
    scroll-padding-bottom: 60px; /* Match footer height */
}
```

---

### 2. Focus Appearance (2.4.13) - AAA (Optional)

**Automated Detection**: None (contrast calculation possible but not reliable)

**Test Procedure**:

1. **Size Check**:
   - Tab to each interactive element
   - Verify focus indicator is visible
   - Measure: at least 2px thick perimeter

2. **Contrast Check**:
   - Use color contrast analyzer
   - Check focused vs unfocused state
   - ✅ Pass if contrast ratio ≥ 3:1

3. **Visibility Check**:
   - Tab through all elements
   - Verify focus visible on every element
   - Test at 200% zoom
   - Test with Windows High Contrast mode

**Current Project Check**:
```css
/* In app/static/css/accessibility.css */
:focus-visible {
    outline: 3px solid #0053e2; /* Should be 3:1 contrast */
    outline-offset: 2px;
}
```

**Quick Test**:
```javascript
// Check all focusable elements
const elements = document.querySelectorAll('a, button, input, select, textarea');
elements.forEach(el => {
    el.focus();
    // Visually verify focus indicator is visible
});
```

---

### 3. Dragging Movements (2.5.7) - AA

**Automated Detection**: None (requires semantic understanding)

**Test Procedure**:

1. **Identify Drag Interactions**:
   - Search for draggable elements
   - Check for: `draggable="true"`, drag event handlers
   - Check Chart.js charts for draggable features

2. **Alternative Input Test**:
   - Try to complete action with keyboard only
   - Look for: arrow buttons, up/down controls
   - Check if drag is essential (e.g., drawing app)

**Project Review**:
- Chart.js: Check if charts are draggable
- Riverside: Check for drag-drop in compliance matrix
- Resources: Check for drag-sorting

**Remediation**:
```html
<!-- Bad: Drag only -->
<div draggable="true">Item</div>

<!-- Good: Drag + keyboard -->
<div draggable="true">
    Item
    <button aria-label="Move up">↑</button>
    <button aria-label="Move down">↓</button>
</div>
```

---

### 4. Target Size (2.5.8) - AA

**Automated Detection**: Partial (inline targets difficult)

**Test Procedure**:

1. **Size Measurement**:
   ```javascript
   // Check all interactive elements
   const elements = document.querySelectorAll(
       'a, button, input, select, textarea, [role="button"]'
   );
   elements.forEach(el => {
       const rect = el.getBoundingClientRect();
       console.log(`${el.tagName}: ${rect.width}x${rect.height}px`);
   });
   ```

2. **Minimum Size Check**:
   - All targets must be ≥ 24x24 CSS pixels
   - Or have 24px spacing (circles don't intersect)

3. **Exception Review**:
   - Inline links in text: Exempt
   - User-agent controls: Exempt
   - Essential presentation: Document if applicable

**Current Project Check**:
```css
/* In app/static/css/accessibility.css */
a, button, [role="button"], input, select, textarea, summary {
    min-height: 44px; /* Exceeds 24px minimum ✅ */
    min-width: 44px;
}
```

**Quick Check**:
```javascript
// Find small targets
const small = [...document.querySelectorAll('a, button, input, select, textarea')]
    .filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.width < 24 || rect.height < 24;
    });
console.log(`${small.length} small targets found`, small);
```

---

### 5. Consistent Help (3.2.6) - A

**Automated Detection**: None (requires semantic understanding)

**Test Procedure**:

1. **Identify Help Mechanisms**:
   - Human contact (phone, chat, email)
   - Self-help (FAQs, documentation)
   - Automated contact (chatbot)

2. **Location Consistency**:
   - Navigate to 5+ pages
   - Note help location on each
   - ✅ Pass if in same relative order
   - ❌ Fail if location changes

**Project Review**:
- Footer help links
- Riverside help icons
- Dashboard info tooltips
- Navigation help menu

**Checklist**:
- [ ] Help link always in footer
- [ ] Contact info always in same position
- [ ] Help icon always in header (if present)
- [ ] Consistent across all pages

---

### 6. Redundant Entry (3.3.7) - A

**Automated Detection**: Limited (requires form tracking)

**Test Procedure**:

1. **Multi-Step Forms**:
   - Complete step 1 of wizard
   - Proceed to step 2
   - Check if previously entered data available

2. **Auto-Population Check**:
   - Enter data in form A
   - Navigate to form B
   - ✅ Pass if data auto-filled or selectable

3. **Security Exception Check**:
   - Password fields: Can require re-entry ✅
   - Security questions: Can require re-entry ✅

**Project Areas to Test**:
- `/onboarding` - tenant setup wizard
- `/preflight` - configuration steps
- `/riverside` - compliance requirements
- Budget/cost forms

**Remediation**:
```html
<!-- Auto-populate from session -->
<input type="text" name="tenant_name" 
       value="{{ session.previous_tenant_name }}"
       autocomplete="organization">
```

---

### 7. Accessible Authentication (3.3.8) - AA

**Automated Detection**: None (requires cognitive assessment)

**Test Procedure**:

1. **Login Flow Test**:
   - Navigate to `/login`
   - Verify password manager works (1Password, LastPass)
   - Check for CAPTCHA

2. **CAPTCHA Check**:
   - If CAPTCHA present, verify alternatives:
     - Audio CAPTCHA
     - Email verification option
     - Alternative challenge

3. **Cognitive Function Check**:
   - No "select all images with cars" without alternative
   - No memory-based puzzles
   - No math problems without alternative

**Current Project Check**:
- `/login` uses OIDC/OAuth
- Verify Azure AD handles accessibility
- Check for any custom CAPTCHA

**✅ Likely Pass**: Project uses standard OIDC/OAuth

---

## HTMX-Specific Manual Tests

### Navigation Testing

1. **hx-boost Navigation**:
   - Navigate using keyboard only
   - Verify page title announced
   - Verify focus in logical location
   - Test back/forward buttons

2. **Focus Management**:
   - Navigate with `hx-boost`
   - Tab to interactive element
   - Navigate to new page
   - Tab again
   - ✅ Verify focus visible and logical

3. **Screen Reader Announcement**:
   - Turn on NVDA/VoiceOver
   - Navigate with `hx-boost`
   - ✅ Verify "Page loaded" or new title announced
   - ❌ Fail if silent navigation

### Dynamic Content Testing

1. **HTMX Swap Announcement**:
   - Trigger HTMX request
   - Verify loading state announced
   - Verify new content announced
   - ✅ Pass if `aria-live` works

2. **Focus After Swap**:
   - Trigger HTMX update
   - Verify focus not lost
   - If focus lost, verify in logical location

---

## Screen Reader Testing Protocol

### NVDA Testing (Windows)

**Setup**:
1. Download from https://www.nvaccess.org/
2. Install and run
3. Use Caps Lock as NVDA key

**Test Script**:

1. **Page Load**:
   ```
   Action: Open page
   Expected: "Page title, heading level 1" announced
   ```

2. **Navigation**:
   ```
   Action: Tab through navigation
   Expected: Each link name announced
   ```

3. **HTMX Navigation**:
   ```
   Action: Activate link with hx-boost
   Expected: "Page updated" or new title announced
   ```

4. **Form Submission**:
   ```
   Action: Submit form
   Expected: Success/error announced
   ```

5. **Dynamic Content**:
   ```
   Action: Trigger HTMX request
   Expected: "Loading" then "Content updated"
   ```

### VoiceOver Testing (macOS)

**Setup**:
1. Command + F5 to enable
2. Use Control + Option as VoiceOver key

**Test Script**:

1. **Rotor Test**:
   ```
   Action: Control + Option + U (headings rotor)
   Expected: All headings listed
   ```

2. **Landmarks**:
   ```
   Action: Control + Option + U (landmarks)
   Expected: nav, main, footer listed
   ```

---

## Color Contrast Testing

### Required Contrast Ratios

| Element | Required Ratio | WCAG Level |
|---------|-----------------|------------|
| Normal text (< 18pt) | 4.5:1 | AA |
| Large text (≥ 18pt bold / 24pt) | 3:1 | AA |
| UI Components (focus, borders) | 3:1 | AA |
| Graphical objects | 3:1 | AA |

### Testing Tools

1. **Browser DevTools**:
   - Chrome: Elements panel → Accessibility → Contrast
   - Firefox: Accessibility panel → Check contrast

2. **Standalone Tools**:
   - WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
   - Colour Contrast Analyser (download)

### Project Testing

**Test Areas**:
- Brand colors (each tenant)
- Text on backgrounds
- Focus indicators
- Chart.js colors
- Button text
- Links vs surrounding text

**Quick Check**:
```javascript
// Check contrast of all text elements
// Use axe DevTools for automated check
```

---

## Keyboard Testing

### Keyboard Navigation Checklist

- [ ] All interactive elements reachable with Tab
- [ ] Tab order is logical (left-to-right, top-to-bottom)
- [ ] No keyboard traps (can Tab out of every element)
- [ ] Focus visible on all elements
- [ ] Enter activates links and buttons
- [ ] Space activates buttons
- [ ] Arrow keys work in radio groups, menus
- [ ] Escape closes modals/menus
- [ ] Home/End work in lists

### Keyboard Testing Script

1. **Document Tab Order**:
   ```javascript
   // Log tab order
   let tabIndex = 0;
   document.addEventListener('focusin', (e) => {
       console.log(`${++tabIndex}: ${e.target.tagName} - ${e.target.textContent?.slice(0, 50)}`);
   });
   ```

2. **Test Without Mouse**:
   - Unplug mouse
   - Complete common tasks:
     - Navigate to Dashboard
     - View costs
     - Run preflight check
     - Check Riverside compliance
   - ✅ Pass if all tasks completable

---

## Zoom Testing

### Required Testing

**Zoom to 200%**:
- No loss of content
- No horizontal scrolling (unless table/data requires it)
- All functionality works

**Zoom to 400%**:
- Content still accessible
- Navigation still usable
- Forms still usable

**Browser Zoom**:
- Chrome: Ctrl + Plus/Ctrl + Minus
- Firefox: Ctrl + Plus/Ctrl + Minus
- Safari: Command + Plus/Command + Minus

### Project-Specific Tests

1. **Navigation at 200%**:
   - Does hamburger menu appear?
   - Are nav items still accessible?

2. **Tables at 200%**:
   - Can all data be viewed?
   - Horizontal scrolling acceptable for data tables

3. **Forms at 400%**:
   - Can all fields be accessed?
   - Do labels stay associated?

---

## Reduced Motion Testing

### Required

Respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

**Project Check**:
```css
/* In app/static/css/accessibility.css */
@media (prefers-reduced-motion:reduce) {
    *,*::before,*::after {
        animation-duration:0.01ms !important;
        transition-duration:0.01ms !important;
        scroll-behavior:auto !important;
    }
}
```

**✅ Already implemented**

---

## Testing Schedule

### Monthly Automated Testing

- axe-core full scan
- Lighthouse accessibility audit
- WAVE scan
- Color contrast check

### Quarterly Manual Testing

- Screen reader testing (NVDA)
- Keyboard navigation audit
- Zoom 200%/400% testing
- Focus Not Obscured verification
- HTMX accessibility review

### Annual Comprehensive Audit

- Full WCAG 2.2 AA manual testing
- Multi-browser testing
- Multi-device testing
- User testing with disabled users

---

## Documentation

### Test Results Template

```markdown
## Accessibility Test Results - [Date]

### Tester: [Name]
### Browser: [Browser + Version]
### Screen Reader: [Name + Version]

### Pages Tested:
- [ ] /
- [ ] /dashboard
- [ ] /costs
- [ ] /compliance
- [ ] /riverside
- [ ] /preflight
- [ ] /login

### Results Summary:
- WCAG 2.2 AA: [Pass/Fail]
- Critical Issues: [Count]
- High Priority: [Count]
- Medium Priority: [Count]
- Low Priority: [Count]

### Detailed Findings:

#### Issue 1: [Title]
- **Criterion**: [WCAG ref]
- **Severity**: [Critical/High/Medium/Low]
- **Page**: [URL]
- **Description**: [What was found]
- **Recommendation**: [How to fix]
- **Screenshot**: [If applicable]

### Remediation Tracking:
| Issue | Assigned | Status | Due Date |
|-------|----------|--------|----------|
```

---

## Quick Reference: WCAG 2.2 Manual Tests

| Criterion | Level | Test Time | Difficulty |
|-----------|-------|-----------|------------|
| 2.4.11 Focus Not Obscured | AA | 15 min | Easy |
| 2.4.13 Focus Appearance | AAA | 10 min | Easy |
| 2.5.7 Dragging Movements | AA | 5 min | Easy |
| 2.5.8 Target Size | AA | 15 min | Medium |
| 3.2.6 Consistent Help | A | 10 min | Easy |
| 3.3.7 Redundant Entry | A | 20 min | Medium |
| 3.3.8 Accessible Authentication | AA | 10 min | Easy |

**Total estimated time**: ~85 minutes per audit

---

## Resources

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- ARIA APG: https://www.w3.org/WAI/ARIA/apg/
- HTMX Docs: https://htmx.org/docs/
- NVDA: https://www.nvaccess.org/
- axe-core: https://www.deque.com/axe/
- WebAIM: https://webaim.org/

---

*Created: March 2026*  
*For: Azure Governance Platform Accessibility Audit*
