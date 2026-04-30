#!/usr/bin/env python3
"""Fetch coarse DuckDuckGo HTML snippets for naming candidates.

Purpose: capture reproducible, human-reviewable public search snippets for a
shortlist. This is not a comprehensive search or legal clearance.
"""

from __future__ import annotations

import html
import re
import time
import urllib.parse
import urllib.request

QUERIES = [
    '"Switchyard" "cloud governance"',
    '"Aerie" "cloud governance"',
    '"Crossdock" "cloud" SaaS',
    '"Yardmaster" "cloud" software',
    '"RelayDeck" software',
    '"Loomline" software',
    '"Brandyard" software',
    '"TenantForge" software',
    '"FleetGlass" software',
    '"Hubwright" software',
    '"BrandPlane" software',
    '"Operatorium" software',
]

RESULT_RE = re.compile(
    r'<a rel="nofollow" class="result__a" href="(?P<href>[^"]+)">(?P<title>.*?)</a>', re.S
)
TAG_RE = re.compile(r"<.*?>", re.S)


def clean(value: str) -> str:
    return html.unescape(TAG_RE.sub("", value)).strip()


def fetch(query: str) -> list[tuple[str, str]]:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 naming research"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return [("ERROR", str(exc))]
    results: list[tuple[str, str]] = []
    for match in RESULT_RE.finditer(body):
        href = html.unescape(match.group("href"))
        title = clean(match.group("title"))
        results.append((title, href))
        if len(results) >= 5:
            break
    return results


def main() -> int:
    for query in QUERIES:
        print(f"## {query}")
        for title, href in fetch(query):
            print(f"- {title} — {href}")
        print()
        time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
