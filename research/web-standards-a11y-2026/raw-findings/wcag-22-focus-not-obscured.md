# WCAG 2.2 - Focus Not Obscured (Minimum) (2.4.11)

**Source**: W3C WCAG 2.2 Specification  
**URL**: https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum  
**Date Extracted**: March 2026  
**Level**: AA  
**Automated Detection**: None (requires manual testing)

---

## Success Criterion

**2.4.11 Focus Not Obscured (Minimum)** (Level AA)

> When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content.

### Notes

**Note 1**: Where content in a configurable interface can be repositioned by the user, then only the initial positions of user-movable content are considered for testing and conformance of this success criterion.

**Note 2**: Content opened by the user may obscure the component receiving focus. If the user can reveal the focused component without advancing focus (e.g., using the Escape key to dismiss the obscuring content, scrolling to reveal the focused component, or using keys to move between overlays), the component with focus is not considered visually hidden due to author-created content.

---

## Intent

The intent of this success criterion is to ensure that the item receiving keyboard focus is always partially visible in the user's viewport. For sighted people who rely on a keyboard (or on a device that operates through the keyboard interface, such as a switch or voice input), knowing the current point of focus is critical.

Where users cannot see the item with focus, they may not know how to proceed, or may even think the system has become unresponsive.

In recognition of the complex responsive designs common today, this AA criterion allows for the component receiving focus to be partially obscured by other author-created content. A partly obscured component can still be very visible, although the more of it that is obscured, the less easy it is to see.

**Typical types of content that can overlap focused items**:
- Sticky footers
- Sticky headers
- Non-modal dialogs
- Cookie banners
- Chat widgets

---

## Sufficient Techniques

### Technique C43: Using CSS scroll-padding to un-obscure content

```css
html {
    scroll-padding-top: 80px; /* Height of sticky header */
    scroll-padding-bottom: 60px; /* Height of sticky footer */
}
```

---

## Common Failures

### Failure F110: Sticky footer or header completely hiding focused elements

**Example**: A sticky footer covers the bottom 60px of the viewport. When tabbing to the last few elements on the page, they become completely obscured by the footer.

**Solution**: 
1. Use `scroll-padding-bottom` to ensure focused elements scroll into view
2. Make footer non-sticky (scroll naturally with page)
3. Use modal dialogs that take focus

---

## User-Opened Content

Content opened by the user may obscure the component receiving focus. If the user can reveal the focused component using a method without having to navigate back to the user-opened content to dismiss it, this criterion would be passed.

**Keyboard actions that may allow the item with focus to be revealed**:
- Using the Escape key to dismiss the obscuring content
- Using keys to scroll the content in the viewport to reveal the item with focus
- Issuing a key to move between overlays (e.g., F6 to toggle stacking order)

**Example scenarios**:

1. **Chat widget**: User opens chat, obscures content below. User tabs to obscured link, presses Escape to close chat, link is revealed.

2. **Fixed feedback component**: User expands feedback form at bottom. Tabbing to obscured link and pressing Down Arrow or Space scrolls content to reveal the link.

3. **Multiple overlays**: User opens contributor list overlay, then opens second overlay showing contributions. Pressing F6 toggles stacking order of overlays.

---

## Modal Dialogs

A properly constructed modal dialog will always pass this SC. Even if it appears directly on top of an item with focus, the dialog takes focus on appearance, and thus the item receiving focus (the dialog or one of its components) is visible.

**Properly constructed modal**:
- Takes focus on appearance
- Maintains focus within the modal
- Prevents interaction outside the modal until dismissed

**Dialog-like overlay that fails**:
- Does not take focus on appearance
- Does not constrain interaction to the overlay
- Does not dismiss itself on loss of focus

---

## Application to HTMX

**Considerations for server-rendered HTMX applications**:

1. **HTMX-boosted navigation**: Ensure focus moves to new content after navigation
2. **HTMX partial updates**: Ensure focused element isn't obscured by sticky headers/footers after swap
3. **Modal dialogs**: If using HTMX to load modal content, ensure focus management

**Implementation**:
```javascript
// After HTMX swap, ensure focus is visible
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Scroll focused element into view if obscured
    const focused = document.activeElement;
    if (focused) {
        focused.scrollIntoView({ block: 'nearest' });
    }
});
```

---

## Testing Procedure

### Manual Testing Steps

1. **Open the page**
2. **Tab through all interactive elements** (links, buttons, form controls)
3. **Verify**: Each focused element is at least partially visible
4. **Test at different viewport sizes**:
   - Desktop (1920x1080)
   - Tablet (768x1024)
   - Mobile (375x667)
5. **Check sticky elements**:
   - Scroll to bottom of page
   - Tab backwards (Shift+Tab) to elements near bottom
   - Verify not obscured by sticky footer

### Tools

- **Browser DevTools**: Check computed styles for `position: sticky` and `position: fixed`
- **Keyboard**: Tab navigation
- **Visual inspection**: Ensure focused element visible

---

## References

- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum
- Understanding SC 2.4.11: https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum
- Technique C43: https://www.w3.org/WAI/WCAG22/Techniques/css/C43
- Failure F110: https://www.w3.org/WAI/WCAG22/Techniques/failures/F110

---

*Extracted: March 2026*  
*Source Tier: 1 (W3C Official)*
