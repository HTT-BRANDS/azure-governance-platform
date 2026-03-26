# WCAG 2.2 - Target Size (Minimum) (2.5.8)

**Source**: W3C WCAG 2.2 Specification  
**URL**: https://www.w3.org/TR/WCAG22/#target-size-minimum  
**Date Extracted**: March 2026  
**Level**: AA  
**Automated Detection**: Partial (inline targets difficult to detect automatically)

---

## Success Criterion

**2.5.8 Target Size (Minimum)** (Level AA)

> The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:

### Exceptions

1. **Spacing**: Undersized targets (those less than 24 by 24 CSS pixels) are positioned so that if a 24 CSS pixel diameter circle is centered on the bounding box of each, the circles do not intersect another target or the circle for another undersized target;

2. **Equivalent**: The function can be achieved through a different control on the same page that meets this criterion;

3. **Inline**: The target is in a sentence or its size is otherwise constrained by the line-height of non-target text;

4. **User Agent Control**: The size of the target is determined by the user agent and is not modified by the author;

5. **Essential**: A particular presentation of the target is essential or is legally required for the information being conveyed.

### Notes

**Note 1**: Targets that allow for values to be selected spatially based on position within the target are considered one target for the purpose of the success criterion. Examples include sliders, color pickers displaying a gradient of colors, or editable areas where you position the cursor.

**Note 2**: For inline targets the line-height should be interpreted as perpendicular to the flow of text. For example, in a language displayed vertically, the line-height would be horizontal.

---

## Intent

The intent of this success criterion is to ensure that target sizes are large enough to be operated by users with limited dexterity or mobility impairments. This includes users who have difficulty holding a pointing device steady, or who use alternative input methods such as a mouth stick or head pointer.

The 24x24 CSS pixel minimum is based on research showing this size reduces the likelihood of accidental activation while still allowing dense user interfaces.

---

## Project Current Implementation

**File**: `app/static/css/accessibility.css`

```css
/* Current implementation - exceeds minimum */
a, button, [role="button"], input, select, textarea, summary {
    min-height: 44px;
    min-width: 44px;
}

nav a, nav button {
    display: inline-flex;
    align-items: center;
    min-height: 44px;
    padding: 8px 12px;
}
```

**Assessment**: ✅ **COMPLIANT** - Current implementation uses 44px minimum, which exceeds the 24px requirement.

---

## Exceptions Explained

### Exception 1: Spacing

If targets are smaller than 24x24px, they must have enough space around them so that 24px circles centered on each target don't overlap.

**Example**:
```css
/* Small targets with spacing */
.small-button {
    width: 20px;
    height: 20px;
    margin: 4px; /* Provides spacing to meet 24px minimum */
}
```

### Exception 2: Equivalent

A smaller target is acceptable if there's another way to achieve the same function with a properly-sized target.

**Example**: A small "x" button on a modal can be accompanied by a larger "Close" button.

### Exception 3: Inline

Links within paragraphs of text are exempt because their size is constrained by line-height.

**Example**:
```html
<p>Read more about our <a href="#">privacy policy</a> and terms.</p>
<!-- The link "privacy policy" is inline and exempt -->
```

### Exception 4: User Agent Control

Default browser controls (like checkboxes, radio buttons) are exempt unless the author modifies them.

### Exception 5: Essential

A particular presentation is required (e.g., legal document with specific layout requirements).

---

## Testing Procedure

### Automated Testing (Partial)

**axe-core rule**: `target-size`

```javascript
// Example axe-core configuration
const axeConfig = {
    rules: [
        {
            id: 'target-size',
            enabled: true
        }
    ]
};
```

**Limitations**: 
- Cannot reliably detect inline targets
- Cannot determine if equivalent control exists
- Cannot assess "essential" exceptions

### Manual Testing

1. **Inspect all interactive elements**:
   - Buttons
   - Links (non-inline)
   - Form controls
   - Custom controls

2. **Check computed size**:
   ```javascript
   // In browser console
   document.querySelectorAll('button, a, input, select, textarea').forEach(el => {
       const rect = el.getBoundingClientRect();
       console.log(`${el.tagName}: ${rect.width}x${rect.height}`);
   });
   ```

3. **Verify minimum 24x24px**:
   - Or check spacing exception
   - Or verify equivalent control
   - Or confirm inline context

4. **Check at different zoom levels**:
   - 100%
   - 200%
   - 400%

---

## HTMX Considerations

**Dynamic content loaded via HTMX**:

1. Targets added via HTMX swaps must also meet size requirements
2. Event handlers on small elements should meet requirements
3. Custom HTMX indicators should be properly sized

**Example**:
```html
<!-- Good: Properly sized HTMX trigger -->
<button hx-get="/api/data"
        hx-target="#result"
        style="min-width: 44px; min-height: 44px;">
    Load Data
</button>

<!-- Bad: Small icon button without proper sizing -->
<button hx-get="/api/delete"
        style="width: 16px; height: 16px;">
    ❌
</button>
```

---

## Common Failures

### Failure Example 1: Icon-only buttons

```html
<!-- FAILS: 20x20px icon button -->
<button class="icon-button">
    <svg width="20" height="20"><!-- icon --></svg>
</button>

<!-- PASSES: 44x44px with icon centered -->
<button class="icon-button" style="width: 44px; height: 44px;">
    <svg width="20" height="20"><!-- icon --></svg>
</button>
```

### Failure Example 2: Close buttons on modals

```html
<!-- FAILS: Small close button -->
<button class="close" style="width: 16px; height: 16px;">×</button>

<!-- PASSES: Larger close button -->
<button class="close" style="width: 44px; height: 44px;" aria-label="Close">×</button>
```

---

## References

- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/#target-size-minimum
- Understanding SC 2.5.8: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum
- axe-core rule: https://dequeuniversity.com/rules/axe/4.11/target-size

---

*Extracted: March 2026*  
*Source Tier: 1 (W3C Official)*
