# WCAG 2.2 AA Accessibility Audit

**Scope:** azure-governance-platform (all migrated pages + core primitives)
**Standard:** WCAG 2.2 Level AA (full) + select AAA spot-checks
**Audit method:** Static analysis via `tests/unit/test_wcag_accessibility.py` (60 tests, all green)
**Audit date:** 2026-04-20 (Phase 4c of ADR-0005)
**Issue:** `azure-governance-platform-py7u.3`

---

## TL;DR

- ✅ **All 2.1 AA criteria** we tested in Phase 1 still pass.
- ✅ **All 6 new 2.2 AA criteria** (SC 2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8) pass.
- 🐛 **1 real bug found + fixed this audit**: dark-mode `--border-color` was 1.86:1 on `--bg-primary` (WCAG 1.4.11 requires ≥3:1 for non-text). Bumped to `#6B7280` (3.96:1).
- ➕ **7 new tests added** across 3 test classes to close gaps in dark-mode and ds-primitive coverage.

---

## 1. Criterion-by-criterion results

### Level A

| SC | Title | Status | Test class |
|----|-------|--------|------------|
| 1.3.1 | Info and Relationships | ✅ PASS | `TestSemanticStructure`, `TestAriaAttributes` |
| 2.4.1 | Bypass Blocks | ✅ PASS | `TestBypassBlocks` |
| 3.2.6 | Consistent Help *(new in 2.2)* | ✅ PASS | `TestConsistentHelp` |
| 3.3.7 | Redundant Entry *(new in 2.2)* | ✅ PASS | `TestRedundantEntry` |
| 4.1.2 | Name, Role, Value | ✅ PASS | `TestAriaAttributes` |

### Level AA

| SC | Title | Status | Test class | Notes |
|----|-------|--------|------------|-------|
| 1.4.3 | Contrast (Minimum) | ✅ PASS | `TestContrastRequirements` | 4.5:1 body text, 3:1 large |
| 1.4.11 | Non-text Contrast | ✅ PASS | `TestNonTextContrast` + `TestDarkModeContrast` | **Fixed dark border in this audit** |
| 2.4.7 | Focus Visible | ✅ PASS | `TestFocusVisible`, `TestDsPrimitiveFocusVisible` | Global rule + per-primitive |
| 2.4.11 | Focus Not Obscured (Min) *(new in 2.2)* | ✅ PASS | `TestFocusNotObscured` | `scroll-margin-top` on `:focus` |
| 2.5.7 | Dragging Movements *(new in 2.2)* | ✅ PASS | `TestDraggingMovements` | No drag-and-drop in app |
| 2.5.8 | Target Size (Minimum) *(new in 2.2)* | ✅ PASS | `TestTargetSizeMinimum`, `TestDsButtonTargetSize` | 24×24 CSS px; ds_button ~36px tall |
| 3.3.8 | Accessible Authentication (Min) *(new in 2.2)* | ✅ PASS | `TestAccessibleAuthentication` | Azure AD SSO primary, no CAPTCHA |

### Level AAA (spot-checks)

| SC | Title | Status | Notes |
|----|-------|--------|-------|
| 1.4.6 | Contrast (Enhanced — 7:1) | ⚠️ partial | Light `--text-primary` on `--bg-primary` exceeds 7:1; dark `--text-muted` at 7.55:1. Not required. |
| 2.4.12 | Focus Not Obscured (Enhanced) | not targeted | Requires zero obscuration. We meet minimum (partial allowed). |

---

## 2. Findings & fixes (this audit)

### 🐛 Bug #1 — Dark-mode border contrast failure

**Finding:** `--border-color: #374151` on `--bg-primary: #0F0F0F` renders at **1.86:1** — fails WCAG 1.4.11 (3:1 non-text minimum).

**Discovery:** New test `TestDarkModeContrast.test_dark_mode_border_contrast` fired on first run.

**User impact:** In dark mode, borders around cards, tables, and form inputs were barely visible — users relying on them to distinguish interactive boundaries (especially low-vision users) would struggle.

**Fix:** `app/static/css/design-tokens.css`
- `.dark { --border-color: }` → `#6B7280` (3.96:1) ✓
- `.dark { --border-default: }` → `#6B7280` (synonym, same fix)
- `.dark { --border-light: }` → `#4B5563` (subtle divider, 2.54:1 — documented as decorative, not an active UI boundary)
- Same fix applied to `@media (prefers-color-scheme: dark)` fallback block so system-preference users get the fix without an explicit toggle.

**Verification:** 60/60 WCAG tests green post-fix.

---

## 3. Test coverage additions (this audit)

Added 9 new tests across 3 classes in `tests/unit/test_wcag_accessibility.py`:

### `TestDarkModeContrast` (+4 tests)
Previous coverage: 1 test (muted text only). Now comprehensive:
- `test_dark_mode_primary_text_contrast` — 18.34:1 ✓
- `test_dark_mode_secondary_text_contrast` — 13.01:1 ✓
- `test_dark_mode_border_contrast` — 3.96:1 ✓ *(fired on bug; fixed)*
- `test_dark_mode_text_secondary_on_surface` — AA on card backgrounds

### `TestDsButtonTargetSize` (+3 tests)
Previous coverage: nav-element CSS only. Now audits ds_button source directly:
- `test_ds_button_has_adequate_vertical_padding` — rejects `py-0/0.5/1/1.5`
- `test_ds_button_has_adequate_horizontal_padding` — requires `px-3` or larger
- `test_ds_button_uses_text_sm_or_larger` — rejects `text-xs` to guarantee line-height ≥20px

Computed button height: `20px line-height + 8px×2 padding = 36px` — 50% margin over 24px floor.

### `TestDsPrimitiveFocusVisible` (+2 tests)
Previous coverage: global `:focus-visible` selector presence. Now verifies:
- Global rule still covers `button` and `a` (both ds_button render modes)
- Rule doesn't declare `outline: none` without a replacement visual indicator (box-shadow or border)

---

## 4. What's explicitly OUT OF SCOPE

Per `py7u.3` acceptance criteria, the following remain for future sessions:

- **axe-core via Playwright on live pages** — requires a running app + browser automation, better suited for `py7u.4` (visual diff) which already needs Playwright infra.
- **Screen-reader manual test** — cannot be automated; requires NVDA/JAWS/VoiceOver sessions.
- **Keyboard-only navigation walkthrough** — partially covered by static focus-visible tests; full walkthrough is a manual QA activity.

---

## 5. Regression discipline

Every new WCAG-relevant token, primitive, or page **must** have a corresponding test in `test_wcag_accessibility.py` before merge. The test file's module docstring lists every covered SC and points here. If you add a criterion, add both:
1. A test class (even if it's a 1-liner stub documenting "this criterion is satisfied by design because X")
2. A row in the tables above

This keeps WCAG compliance as a *tested invariant* rather than a point-in-time audit that drifts.
