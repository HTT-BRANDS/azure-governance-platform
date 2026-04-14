"""Render scripts/audit_output.json into docs/status.md for GitHub Pages.

Runs as a step inside .github/workflows/pages.yml. Safe to run when the
audit output is missing — produces a "no data" placeholder.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def render(report: dict[str, Any] | None) -> str:
    now = datetime.now(UTC).isoformat()
    if not report:
        return (
            "---\ntitle: Platform Status\n---\n\n"
            "# Platform Status\n\n"
            "_No audit output available yet._\n\n"
            f"Last page build: `{now}`\n"
        )

    lines: list[str] = [
        "---",
        "title: Platform Status",
        "---",
        "",
        "# Platform Status",
        "",
        f"Generated: `{report.get('generated_at', now)}`  ",
        f"Environment: **{report.get('environment', 'unknown')}**  ",
        "",
        "## Tenant health",
        "",
        "| Tenant | Reader | Consent | Missing scopes |",
        "|---|---|---|---|",
    ]
    for t in report.get("tenants", []):
        reader = "✅" if t["reader"].get("ok") else "❌"
        consent = "✅" if t["graph_consent"].get("ok") else "❌"
        missing = ", ".join(t["graph_consent"].get("missing", [])) or "—"
        lines.append(f"| {t['code']} | {reader} | {consent} | `{missing}` |")

    lines += ["", "## UI-fixture leaks", ""]
    leaks = report.get("ui_fixture_leaks", [])
    if not leaks:
        lines.append("_None — no MOCK_ / fixture imports in page routes or templates._")
    else:
        for p in leaks:
            lines.append(f"- `{p}`")
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render audit JSON into docs/status.md.")
    p.add_argument("--input", default=str(REPO_ROOT / "scripts" / "audit_output.json"))
    p.add_argument("--output", default=str(REPO_ROOT / "docs" / "status.md"))
    args = p.parse_args(argv)

    report = _load(Path(args.input))
    Path(args.output).write_text(render(report), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
