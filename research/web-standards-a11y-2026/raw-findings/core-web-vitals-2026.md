# Core Web Vitals 2026

**Source**: web.dev / Google Chrome team  
**URL**: https://web.dev/articles/vitals  
**Last Updated**: September 2, 2025  
**Date Extracted**: March 2026  

---

## Executive Summary

**Status**: No changes from 2025 to 2026. Current thresholds remain stable.

**Key Update**: INP (Interaction to Next Paint) officially replaced FID (First Input Delay) in 2024 and is now a stable Core Web Vital.

---

## Current Metrics and Thresholds (2026)

### 1. Largest Contentful Paint (LCP)

**Definition**: Measures loading performance. Reports the render time of the largest image or text block visible within the viewport relative to when the page first started loading.

**Current Thresholds**:
| Rating | Threshold | Description |
|--------|-----------|-------------|
| 🟢 Good | ≤ 2.5 seconds | LCP occurred within 2.5s of page load start |
| 🟡 Needs Improvement | 2.5 - 4.0 seconds | LCP between 2.5s and 4.0s |
| 🔴 Poor | > 4.0 seconds | LCP took longer than 4.0s |

**Target**: 75th percentile of page loads, segmented by mobile and desktop

**LCP Elements**:
- `<img>` elements
- `<image>` elements inside an `<svg>` element
- `<video>` elements (poster image or first frame)
- Elements with background image loaded via `url()` (as opposed to CSS gradient)
- Block-level elements containing text nodes or other inline-level text elements

**Optimization**:
- Optimize and compress images
- Preload important resources
- Remove render-blocking resources
- Use a CDN

---

### 2. Interaction to Next Paint (INP)

**Definition**: Measures interactivity. Reports the latency of all interactions a user has made with the page throughout their visit. Final INP value is the longest interaction observed, ignoring outliers.

**History**:
- Initially experimental (2022)
- Promoted to pending status (2023)
- Replaced FID as Core Web Vital (2024)
- Now stable (2025+)

**Current Thresholds**:
| Rating | Threshold | Description |
|--------|-----------|-------------|
| 🟢 Good | ≤ 200 milliseconds | Page responds quickly to interactions |
| 🟡 Needs Improvement | 200 - 500 milliseconds | Page needs responsiveness improvement |
| 🔴 Poor | > 500 milliseconds | Page has poor responsiveness |

**Target**: 75th percentile of page loads, segmented by mobile and desktop

**How INP is Calculated**:
- INP observes all click, tap, and keyboard interactions
- Each interaction's latency = time from user initiation to next paint
- For most pages: worst interaction is reported as INP
- For high-interaction pages: ignore 1 highest per 50 interactions

**An interaction consists of**:
- **Input delay**: Time before event handlers start
- **Processing duration**: Time for all event handlers to execute
- **Presentation delay**: Time after handlers to next frame

**INP vs FID**:
- FID: Measured input delay of FIRST interaction only
- INP: Measures FULL duration of ALL interactions
- INP is more comprehensive and reliable

**What counts as an interaction**:
- Clicking with a mouse
- Tapping on touchscreen
- Pressing a key (physical or onscreen keyboard)

**What does NOT count**:
- Hovering
- Scrolling
- Zooming

**Optimization**:
- Break up long tasks
- Optimize event handlers
- Defer non-critical JavaScript
- Use `requestIdleCallback` for non-urgent work

---

### 3. Cumulative Layout Shift (CLS)

**Definition**: Measures visual stability. Quantifies how much unexpected layout shift occurs during the entire lifespan of the page.

**Current Thresholds**:
| Rating | Threshold | Description |
|--------|-----------|-------------|
| 🟢 Good | ≤ 0.1 | Minimal unexpected layout shifts |
| 🟡 Needs Improvement | 0.1 - 0.25 | Some layout shifts detected |
| 🔴 Poor | > 0.25 | Significant layout shift issues |

**Target**: 75th percentile of page loads, segmented by mobile and desktop

**Common CLS Causes**:
- Images without dimensions
- Ads, embeds, iframes without dimensions
- Dynamically injected content
- Web fonts causing FOIT/FOUT

**Optimization**:
- Always include width/height attributes on images
- Reserve space for ads/embeds
- Avoid inserting content above existing content
- Use font-display: optional for web fonts

---

## Project Context: HTMX Applications

### LCP Considerations

**Advantages**:
- Server-side rendering provides full HTML immediately
- No JavaScript bundle blocking render
- Progressive enhancement

**Considerations**:
- Chart.js may impact LCP if loaded synchronously
- HTMX partial updates don't affect LCP (already loaded)

**Recommendations**:
```html
<!-- Defer Chart.js to not block LCP -->
<script src="https://cdn.jsdelivr.net/npm/chart.js" defer></script>

<!-- Or use async for non-critical scripts -->
<script src="/static/js/analytics.js" async></script>
```

### INP Considerations

**HTMX-specific optimizations**:

1. **Minimize input delay**:
```javascript
// Use hx-trigger="change" instead of "input" for expensive operations
<input hx-get="/api/search" 
       hx-trigger="change" 
       hx-target="#results">
```

2. **Optimize event handlers**:
```javascript
// Debounce expensive operations
htmx.config.requestDelay = 300; // ms
```

3. **Use hx-indicator for feedback**:
```html
<button hx-get="/api/data" hx-indicator="#loading">
    Load Data
</button>
<div id="loading" class="htmx-indicator">Loading...</div>
```

4. **Avoid blocking the main thread**:
```javascript
// Move non-critical work off main thread
setTimeout(() => {
    // Non-critical initialization
}, 0);
```

### CLS Considerations

**HTMX-specific**:

1. **Reserve space for HTMX-loaded content**:
```html
<div id="dynamic-content"
     hx-get="/api/cards"
     hx-trigger="load"
     style="min-height: 200px;">
    <div class="htmx-indicator">Loading...</div>
</div>
```

2. **Avoid layout shifts on HTMX swaps**:
```css
/* Reserve space to prevent CLS */
.htmx-swapping {
    opacity: 0;
    min-height: 100px; /* Reserve space */
}
```

3. **Smooth transitions**:
```css
.htmx-swapping {
    opacity: 0;
    transition: opacity 150ms ease-out;
}

.htmx-settling {
    opacity: 1;
}
```

---

## Measurement Tools

### Field Data (Real User Monitoring)

**Chrome User Experience Report (CrUX)**:
- URL: https://developer.chrome.com/docs/crux
- Public dataset of Core Web Vitals from real Chrome users
- Origin and URL-level data available

**PageSpeed Insights**:
- URL: https://pagespeed.web.dev
- Uses CrUX data for field metrics
- Also provides lab data (Lighthouse)

**Search Console**:
- Core Web Vitals report
- URL-level grouping
- 28-day rolling window

### Lab Data (Synthetic Testing)

**Lighthouse**:
```bash
# Run Lighthouse CI
npm install -g @lhci/cli
lhci collect --url=http://localhost:8000
lhci assert --preset="lighthouse:recommended"
```

**Web Vitals Chrome Extension**:
- Real-time CWV metrics in browser
- Local development testing

**JavaScript API**:
```javascript
// Measure Web Vitals
import {onLCP, onINP, onCLS} from 'web-vitals';

onLCP(console.log);
onINP(console.log);
onCLS(console.log);
```

---

## Testing Strategy for Project

### Automated Testing

**Lighthouse CI** (already in project):
```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [push]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli@0.14.x
          lhci autorun --config=lighthouserc.json
```

**Lighthouse Configuration**:
```json
// lighthouserc.json
{
  "ci": {
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "interaction-to-next-paint": ["error", { "maxNumericValue": 200 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }]
      }
    }
  }
}
```

### Monitoring

**Application Insights** (already in project):
- Real User Monitoring for Web Vitals
- Custom events for INP tracking

**Implementation**:
```python
# Add to app/core/monitoring.py
from web_vitals import get_web_vitals

def track_web_vitals(request):
    """Track Core Web Vitals in Application Insights."""
    if request.headers.get('Sec-GPC') != '1':
        # Only track if GPC not enabled
        telemetry_client.track_metric("LCP", lcp_value)
        telemetry_client.track_metric("INP", inp_value)
        telemetry_client.track_metric("CLS", cls_value)
```

---

## 2026 Outlook

**Expected Stability**:
- Thresholds expected to remain unchanged through 2026
- No new Core Web Vitals planned
- INP now stable, replacing FID completely

**Potential Changes**:
- New experimental metrics under development
- Possible refinements to INP calculation
- Continued emphasis on mobile performance

---

## References

- Web Vitals Overview: https://web.dev/articles/vitals
- INP Documentation: https://web.dev/articles/inp
- LCP Documentation: https://web.dev/articles/lcp
- CLS Documentation: https://web.dev/articles/cls
- web-vitals JavaScript library: https://github.com/GoogleChrome/web-vitals

---

*Extracted: March 2026*  
*Source Tier: 1 (Google Official)*  
*Last Updated: September 2025*
