# Visual Parity Testing

Automated visual regression testing for the 5 design-system-migrated pages
(`dashboard`, `costs`, `compliance`, `resources`, `identity`).

Ticket: [py7u.4](../../.beads/) · Scope: Phase 4d of py7u (dark mode + WCAG audit + visual parity)

## What it does

Compares a pixel-by-pixel rendered screenshot of each page against a pinned
PNG baseline. Differences exceeding a tolerance threshold fail the test and
write `current`, `baseline`, and amplified `diff` PNGs to
`tests/e2e/visual_diffs/` for review.

## Stack

| Piece | Choice | Why |
|---|---|---|
| Browser driver | Playwright (already a dev dep) | Shared fixtures with the rest of `tests/e2e/` |
| Image diff | Pillow (`ImageChops.difference`) | Pure Python, no native bindings |
| Marker | `-m visual` | Opt-in so CI isn't broken by missing baselines |
| Viewport | `1280×720` | Matches `tests/e2e/conftest.py` browser_context_args |
| Tolerance | 0.5% pixel diff (env: `VISUAL_TOLERANCE_PCT`) | Absorbs anti-aliasing without hiding real regressions |

## First-time setup

```bash
# 1. Install dev deps (Pillow arrives here)
uv sync

# 2. Install Playwright browsers (one-time per machine)
uv run playwright install chromium

# 3. Capture baselines from the local app
uv run python scripts/capture_visual_baselines.py

# 4. Verify the suite passes against the just-captured baselines
uv run pytest -m visual
```

## Daily use

### Run the suite

```bash
uv run pytest -m visual                          # all pages
uv run pytest -m visual -k dashboard             # one page
VISUAL_TOLERANCE_PCT=1.0 uv run pytest -m visual # looser tolerance
```

### When a test fails

1. Look at the test output — the failure message reports the exact pixel
   percentage that differed and where the artifacts are saved.
2. Open `tests/e2e/visual_diffs/{page}.diff.png` to see which regions
   changed. The diff is amplified 10× so subtle shifts are visible.
3. Compare `{page}.current.png` (now) against `{page}.baseline.png` (pinned).
4. Decide: **regression** or **intentional change**?

### Updating baselines after an intentional change

```bash
# Re-capture just the changed page(s)
uv run python scripts/capture_visual_baselines.py --only dashboard

# Verify new baseline looks right (open in Preview / your image viewer)
open tests/e2e/baselines/dashboard.png

# Commit the PNG alongside the code change so review sees the visual delta
git add tests/e2e/baselines/dashboard.png app/templates/pages/dashboard.html
git commit
```

Including the updated baseline in the same commit makes the visual decision
part of code review.

## CI considerations

Currently opt-in. To wire into CI:

1. Ensure the CI image has Playwright browsers available (Ubuntu:
   `playwright install-deps chromium && playwright install chromium`).
2. Commit baselines to git (they're the contract; they must be version-controlled).
3. Add a workflow step after unit tests:
   ```yaml
   - name: Visual parity
     run: uv run pytest -m visual --tb=short
   - name: Upload diffs on failure
     if: failure()
     uses: actions/upload-artifact@v4
     with:
       name: visual-diffs
       path: tests/e2e/visual_diffs/
   ```
4. Consider tightening `VISUAL_TOLERANCE_PCT` to `0.25` in CI (stricter
   than local dev where font hinting may vary between machines).

## Troubleshooting

### "No baseline for {page}"

The test skipped. Run `scripts/capture_visual_baselines.py` to populate
baselines, or manually drop a PNG into `tests/e2e/baselines/`.

### "viewport size mismatch"

Baseline captured at a different window size. Either re-capture, or check
whether a CSS change pushed content below the fold (full-page screenshots
are sensitive to vertical-layout changes).

### Flaky failures below tolerance

Anti-aliasing on different OSes / fonts can cause tiny drift. Options:

- Raise `VISUAL_TOLERANCE_PCT` (quick, blunt)
- Capture baselines on the same OS family as CI (Linux → Linux)
- Mask volatile regions via CSS-injected transparent overlays on
  timestamps and live-data elements (not currently implemented; file a bd
  issue if this becomes necessary)

### Chromium rendering differences from Firefox / WebKit

Baselines are Chromium-only. If cross-browser parity matters later, switch
the capture script to loop over `[chromium, firefox, webkit]` and store
baselines as `{page}.{browser}.png`.

## Why not use Playwright's built-in `toHaveScreenshot()`?

Playwright ships a snapshot comparator, but it's JavaScript-side. We use
`pytest-playwright` in sync Python, and the Python binding doesn't expose
the same API. Pillow + `ImageChops.difference` is 30 lines, explicit, and
gives us full control over tolerance and artifact output.

## Related

- `tests/e2e/test_visual_parity.py` — the test file
- `tests/e2e/baselines/README.md` — directory-scoped usage notes
- `scripts/capture_visual_baselines.py` — capture/refresh utility
- `tests/e2e/conftest.py` — Playwright fixtures reused here
