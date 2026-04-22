# Visual Parity Baselines

This directory holds pinned PNG screenshots used by
`tests/e2e/test_visual_parity.py` (py7u.4).

## What's expected here

One PNG per migrated page. File names must match the `PAGES` list in the
test file:

- `dashboard.png`
- `costs.png`
- `compliance.png`
- `resources.png`
- `identity.png`

## How to populate

### Option A — capture from this app (self-baseline)

Useful for regression-testing design-system refactors against a known-good
local state:

```bash
uv run python scripts/capture_visual_baselines.py
```

This spins up the app on `127.0.0.1:8099`, logs in as admin, screenshots
each page at `1280×720` full-page, and writes the PNGs here.

### Option B — capture from Domain-Intelligence (parity baseline)

To verify this app stays visually consistent with the Domain-Intelligence
reference:

```bash
uv run python scripts/capture_visual_baselines.py \
    --base-url https://domain-intelligence-prod.example.com
```

(You'll need a valid admin session / access token configured for that URL.)

### Option C — only update a subset

```bash
uv run python scripts/capture_visual_baselines.py --only dashboard costs
```

## Running the tests

These tests are opt-in via the `visual` pytest marker. They don't run by
default (so CI without Playwright browsers isn't broken):

```bash
uv run pytest -m visual                # run all 5 visual tests
uv run pytest -m visual -k dashboard   # just one page
```

If a test fails, before/after/diff PNGs land in `tests/e2e/visual_diffs/`
(git-ignored). Inspect the `.diff.png` to see exactly what changed.

## Tolerance

Default: 0.5% of pixels may differ (font anti-aliasing, sub-pixel layout).
Override via env var:

```bash
VISUAL_TOLERANCE_PCT=1.0 uv run pytest -m visual
```

## When a design change is intentional

If a commit legitimately changes how a page looks, re-run
`scripts/capture_visual_baselines.py` to update the baseline(s), then
commit the updated PNG(s) alongside the code change. This makes the
design decision visible in diff review.

See `docs/testing/visual-parity.md` for the full procedure.
