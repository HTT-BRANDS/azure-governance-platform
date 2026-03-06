# axe-core Implementation Guide

**Date:** March 6, 2026  
**Version:** 4.11.1  
**Target:** Azure Governance Platform

---

## Quick Start

### Installation

```bash
# For Node.js projects
npm install --save-dev axe-core

# For Python projects (via Playwright/Selenium integration)
pip install axe-core-python
```

### Basic Usage

```javascript
// In your test file
const axe = require('axe-core');

// Run accessibility check
const results = await axe.run(document);

// Check for violations
if (results.violations.length > 0) {
  console.error('Accessibility violations found:', results.violations);
}
```

---

## Integration with CI/CD

### GitHub Actions Workflow

```yaml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Start application
        run: |
          npm run start &
          sleep 10
      
      - name: Run axe-core tests
        run: npm run test:a11y
      
      - name: Upload results
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: accessibility-report
          path: ./a11y-report.json
```

### Test Script

```javascript
// test/accessibility.test.js
const { test, expect } = require('@playwright/test');
const { injectAxe, checkA11y } = require('axe-playwright');

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000');
    await injectAxe(page);
  });

  test('should have no accessibility violations', async ({ page }) => {
    await checkA11y(page, {
      // WCAG 2.2 AA compliance
      axeOptions: {
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa', 'wcag22aa', 'best-practice']
        }
      },
      detailedReport: true,
      detailedReportOptions: {
        html: true
      }
    });
  });

  test('should have no violations on login page', async ({ page }) => {
    await page.goto('http://localhost:8000/login');
    await injectAxe(page);
    await checkA11y(page, null, 'strict');
  });
});
```

---

## Configuration Options

### WCAG 2.2 Configuration

```javascript
// axe.config.js
module.exports = {
  // Run only WCAG 2.2 AA rules
  runOnly: {
    type: 'tag',
    values: [
      'wcag2a',
      'wcag2aa', 
      'wcag22aa',
      'best-practice'
    ]
  },
  
  // Rules to disable (if needed)
  rules: {
    // Disable specific rules that don't apply
    'color-contrast': { enabled: true },
    'focusable-content': { enabled: true }
  },
  
  // Reporting options
  reporter: 'v2',
  
  // Result types to include
  resultTypes: ['violations', 'incomplete', 'inapplicable']
};
```

### Custom Rules

```javascript
// Custom rule for Azure Governance Platform specific requirements
axe.configure({
  rules: [
    {
      id: 'azure-accessible-card',
      enabled: true,
      selector: '[class*="card"]',
      tags: ['best-practice'],
      metadata: {
        description: 'Cards must have proper heading structure',
        help: 'Cards should have a heading element (h2-h6)'
      },
      all: ['card-has-heading'],
      any: [],
      none: []
    }
  ],
  checks: [
    {
      id: 'card-has-heading',
      evaluate: function(node) {
        return node.querySelector('h2, h3, h4, h5, h6') !== null;
      }
    }
  ]
});
```

---

## Coverage Gaps and Workarounds

### Automated vs. Manual Testing

| WCAG 2.2 Criterion | Automated | Workaround |
|-------------------|-----------|------------|
| 2.4.11 Focus Not Obscured | Partial | Visual regression tests |
| 2.4.12 Focus Not Obscured (Enhanced) | Partial | Manual testing |
| 2.4.13 Focus Appearance | Limited | Design system enforcement |
| 2.5.7 Dragging Movements | None | Functional testing |
| 2.5.8 Target Size | Partial | Visual inspection |
| 3.2.6 Consistent Help | None | Content audit |
| 3.3.7 Redundant Entry | Limited | UX review |
| 3.3.8/9 Accessible Authentication | None | User testing |

### Manual Testing Checklist

```markdown
## WCAG 2.2 Manual Testing

### Focus Management
- [ ] Focus is never completely obscured (2.4.11)
- [ ] Focus indicator is visible and has sufficient contrast (2.4.13)
- [ ] Focus moves logically through the page

### Input Assistance
- [ ] Dragging actions have single-pointer alternatives (2.5.7)
- [ ] Targets meet minimum size (24x24px) or have spacing (2.5.8)
- [ ] Help mechanisms are in consistent locations (3.2.6)
- [ ] Previously entered information is auto-populated (3.3.7)
- [ ] Authentication doesn't require cognitive tests (3.3.8/9)

### Testing Tools
- [ ] Keyboard-only navigation
- [ ] Screen reader testing (NVDA, VoiceOver)
- [ ] Zoom testing (200%, 400%)
- [ ] Mobile touch testing
```

---

## Python Integration (FastAPI)

### Using axe-core with Selenium

```python
# tests/accessibility/test_a11y.py
import pytest
from selenium import webdriver
from axe_core import Axe

class TestAccessibility:
    @pytest.fixture(scope="class")
    def driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()
    
    def test_homepage_accessibility(self, driver):
        driver.get("http://localhost:8000")
        
        axe = Axe(driver)
        axe.inject()
        
        results = axe.run()
        
        # Assert no violations
        assert len(results["violations"]) == 0, \
            f"Found {len(results['violations'])} accessibility violations"
    
    def test_dashboard_accessibility(self, driver):
        # Login first
        driver.get("http://localhost:8000/login")
        # ... perform login ...
        
        driver.get("http://localhost:8000/dashboard")
        
        axe = Axe(driver)
        axe.inject()
        
        results = axe.run()
        
        # Save report
        axe.write_results("./a11y-dashboard-report.json", results)
        
        # Assert no violations
        assert len(results["violations"]) == 0
```

### Using with Playwright

```python
# tests/accessibility/test_playwright_a11y.py
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_page_accessibility():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        
        # Inject axe-core
        await page.add_script_tag(
            url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.11.1/axe.min.js"
        )
        
        # Run axe
        results = await page.evaluate("""
            async () => {
                return await axe.run({
                    runOnly: {
                        type: 'tag',
                        values: ['wcag2a', 'wcag2aa', 'wcag22aa']
                    }
                });
            }
        """)
        
        await browser.close()
        
        # Check results
        assert len(results["violations"]) == 0, \
            f"Accessibility violations: {results['violations']}"
```

---

## Reporting and Monitoring

### JSON Report Format

```javascript
// Generate structured report
const createReport = (results) => {
  return {
    timestamp: new Date().toISOString(),
    url: window.location.href,
    summary: {
      violations: results.violations.length,
      incomplete: results.incomplete.length,
      passes: results.passes.length
    },
    violations: results.violations.map(v => ({
      rule: v.id,
      impact: v.impact,
      description: v.description,
      help: v.help,
      helpUrl: v.helpUrl,
      elements: v.nodes.map(n => ({
        target: n.target,
        html: n.html,
        failureSummary: n.failureSummary
      }))
    }))
  };
};

// Save to file (in Node.js)
const fs = require('fs');
const report = createReport(results);
fs.writeFileSync('a11y-report.json', JSON.stringify(report, null, 2));
```

### Slack Integration

```javascript
// Send critical violations to Slack
const sendToSlack = async (violations) => {
  const critical = violations.filter(v => v.impact === 'critical');
  
  if (critical.length === 0) return;
  
  const webhook = process.env.SLACK_WEBHOOK_URL;
  
  await fetch(webhook, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `🚨 ${critical.length} critical accessibility violations found!`,
      attachments: critical.map(v => ({
        color: 'danger',
        title: v.id,
        text: v.help,
        title_link: v.helpUrl
      }))
    })
  });
};
```

---

## Best Practices

### 1. Run Early and Often

```yaml
# .github/workflows/pr.yml
name: PR Accessibility Check

on:
  pull_request:
    paths:
      - 'templates/**'
      - 'static/css/**'
      - 'static/js/**'

jobs:
  a11y-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run axe on changed pages
        run: |
          # Get list of changed templates
          CHANGED=$(git diff --name-only HEAD~1 | grep 'templates/')
          
          # Run axe on each
          for file in $CHANGED; do
            url="http://localhost:8000${file//templates/}"
            npx axe "$url"
          done
```

### 2. Set Thresholds

```javascript
// Fail build if threshold exceeded
const thresholds = {
  critical: 0,
  serious: 0,
  moderate: 10,  // Allow some moderate issues
  minor: 20
};

const checkThresholds = (results) => {
  const byImpact = results.violations.reduce((acc, v) => {
    acc[v.impact] = (acc[v.impact] || 0) + 1;
    return acc;
  }, {});
  
  for (const [impact, count] of Object.entries(byImpact)) {
    if (count > (thresholds[impact] || 0)) {
      throw new Error(
        `${impact} violations (${count}) exceed threshold (${thresholds[impact]})`
      );
    }
  }
};
```

### 3. Exclude Known Issues

```javascript
// .axeignore.js
module.exports = {
  // Exclude third-party widgets
  exclude: [
    '#intercom-container',
    '.cookie-banner'
  ],
  
  // Disable rules for specific selectors
  rules: [
    {
      id: 'color-contrast',
      exclude: ['.chart-legend']
    }
  ]
};
```

### 4. Integrate with Development Workflow

```json
// package.json
{
  "scripts": {
    "test:a11y": "jest tests/accessibility",
    "test:a11y:watch": "jest tests/accessibility --watch",
    "test:a11y:ci": "jest tests/accessibility --ci --reporters=default --reporters=jest-junit",
    "a11y:report": "node scripts/generate-a11y-report.js"
  },
  "husky": {
    "hooks": {
      "pre-commit": "npm run test:a11y -- --changedSince HEAD~1"
    }
  }
}
```

---

## Troubleshooting

### Common Issues

**Issue:** "Axe is already running" error
```javascript
// Fix: Ensure axe isn't injected multiple times
if (!window.axe) {
  await injectAxe(page);
}
```

**Issue:** False positives on dynamic content
```javascript
// Fix: Wait for content to stabilize
await page.waitForSelector('[data-loaded="true"]');
await checkA11y(page);
```

**Issue:** Timeouts on large pages
```javascript
// Fix: Increase timeout
await checkA11y(page, null, {
  timeout: 30000  // 30 seconds
});
```

---

## References

- [axe-core Documentation](https://www.deque.com/axe/core/documentation/)
- [axe-playwright](https://github.com/abhinaba-ghosh/axe-playwright)
- [axe-core Python](https://github.com/dequelabs/axe-core-python)
- [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)

---

*Last updated: March 6, 2026*
