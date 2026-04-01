# GitHub Pages Cross-Browser Testing

Automated cross-browser testing for the Azure Governance Platform GitHub Pages site using Playwright.

## Overview

This test suite validates that all pages on the GitHub Pages site render correctly across:
- **3 Browsers**: Chromium (Chrome), Firefox, WebKit (Safari)
- **3 Viewport Sizes**: Mobile (375x667), Tablet (768x1024), Desktop (1280x720)
- **All Pages**: Hub pages (HTML) and Detail pages (Markdown)

## Quick Start

### Prerequisites

```bash
# Install Node.js dependencies
cd tests/e2e/github-pages
npm install

# Install Playwright browsers
npx playwright install

# Or install all browsers with system dependencies
npx playwright install --with-deps
```

### Run Tests

```bash
# Run all tests (all browsers, all viewports)
npm test

# Run with UI mode for debugging
npm run test:ui

# Run specific browser
npm run test:chromium
npm run test:firefox
npm run test:webkit

# Run specific viewport
npm run test:desktop
npm run test:tablet
npm run test:mobile

# Debug mode
npm run test:debug
```

## Testing Against Different Environments

### Test Deployed Site (Default)

```bash
# Tests run against https://htt-brands.github.io/azure-governance-platform/
npm test
```

### Test Local File Server

```bash
# Start a local server
cd docs
npx http-server -p 8080

# In another terminal, run tests against local server
GH_PAGES_URL=http://localhost:8080/ npm test
```

### Test Specific URL

```bash
GH_PAGES_URL=https://your-custom-domain.com/ npm test
```

## Project Structure

```
tests/e2e/github-pages/
├── playwright.config.js      # Multi-browser test configuration
├── package.json              # Dependencies and scripts
├── README.md                 # This file
├── pages/
│   └── index.js              # Page Object Model (all page definitions)
├── specs/
│   ├── all-pages.spec.js     # Main cross-browser test suite
│   └── responsive.spec.js    # Responsive breakpoint tests
├── utils/
│   └── test-helpers.js       # Test utilities (screenshots, console checking)
└── screenshots/
    └── .gitkeep              # Screenshot output directory
```

## Page Coverage

### Hub Pages (HTML)
- `/` - Homepage
- `/architecture/` - Architecture hub
- `/operations/` - Operations hub
- `/api/` - API reference hub
- `/decisions/` - ADR hub

### Detail Pages (Markdown)
- `/architecture/overview`
- `/architecture/authentication`
- `/architecture/data-flow`
- `/operations/runbook`
- `/operations/playbook`
- `/operations/cost-analysis`
- `/api/overview`
- `/decisions/adr-0001` through `adr-0009`

## What Gets Tested

Each page test validates:
1. ✅ Page loads successfully (200 status)
2. ✅ Page title matches expected pattern
3. ✅ No unexpected console errors
4. ✅ Key elements visible (heading, nav, footer, content)
5. ✅ Screenshots captured for visual regression

## Viewport Configurations

| Viewport | Dimensions | Description |
|----------|------------|-------------|
| Mobile | 375x667 | iPhone SE size |
| Tablet | 768x1024 | iPad portrait |
| Desktop | 1280x720 | Standard HD |

## Browser Projects

The test suite runs 9 configurations (3 browsers × 3 viewports):

- `chromium-desktop`
- `chromium-tablet`
- `chromium-mobile`
- `firefox-desktop`
- `firefox-tablet`
- `firefox-mobile`
- `webkit-desktop`
- `webkit-tablet`
- `webkit-mobile`

## Updating Screenshots

Screenshots are automatically captured on test runs. To update baseline screenshots:

```bash
# Update all screenshots
npx playwright test --update-snapshots

# Update for specific project
npx playwright test --project=chromium-desktop --update-snapshots
```

## CI/CD Integration

Tests run automatically via GitHub Actions:
- On push to `docs/**`
- On PRs touching documentation
- Weekly scheduled runs (Sundays 3 AM UTC)
- Manual dispatch available

### Workflow Features
- Matrix strategy: 3 browsers × 3 viewports = 9 parallel jobs
- Screenshots uploaded as artifacts
- Test results summary posted to PR/commit
- Automatic baseline screenshot updates (manual trigger)

## Troubleshooting

### Tests failing on first run

Playwright browsers need to be installed:
```bash
npx playwright install
```

### Timeouts on slow connections

Increase timeout in `playwright.config.js`:
```javascript
expect: {
  timeout: 30000, // Increase from default 5000ms
}
```

### Screenshot differences

Minor visual differences across browsers are expected. The tests:
- Capture screenshots for manual review
- Don't fail on minor pixel differences
- Upload artifacts for analysis

### Console errors from third-party scripts

Common expected errors are filtered (analytics, extensions, etc.). See `COMMON_EXPECTED_ERRORS` in `utils/test-helpers.js`.

## Adding New Pages

1. Add page definition to `pages/index.js`:
```javascript
myNewPage: {
  url: '/my-new-page/',
  expectedTitle: /My New Page/,
  keySelectors: {
    heading: 'h1',
    nav: 'nav',
    footer: 'footer',
  },
  description: 'My new page description',
}
```

2. Tests automatically pick up new pages via dynamic iteration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GH_PAGES_URL` | `https://htt-brands.github.io/azure-governance-platform/` | Base URL to test |
| `LOCAL_SERVER_PORT` | - | Port for local server mode |
| `CI` | - | Set by CI environments, affects retries and workers |

## License

Part of Azure Governance Platform - Internal Use Only
