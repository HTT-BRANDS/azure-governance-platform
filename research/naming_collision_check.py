#!/usr/bin/env python3
"""Lightweight public collision checks for naming candidates.

This is not legal/trademark clearance. It gathers reproducible public signals:
- DNS A/AAAA/CNAME/NS presence for common domains
- PyPI exact package existence
- npm exact package existence
- GitHub repository search count for exact-ish candidate text

Keep it dependency-free so it can run from a stock Python environment.
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

CANDIDATES = [
    # V2 candidates
    "switchyard",
    "aerie",
    "hangar",
    "dispatch",
    "meridian",
    # central hub / operations metaphors
    "concourse",
    "waypoint",
    "switchboard",
    "crossdock",
    "yardmaster",
    "interlock",
    "conductor",
    "relaydeck",
    "portico",
    "cartographer",
    "tessera",
    "loomline",
    "brandyard",
    "tenantforge",
    "portfolium",
    "fleetglass",
    "hubwright",
    "cloudfolio",
    "brandplane",
    "operatorium",
]

TLDS = ["com", "io", "app", "dev", "cloud", "ai"]
USER_AGENT = "HTT naming workshop collision checker; contact: repo local research"


@dataclass
class CandidateResult:
    name: str
    domains_with_dns: list[str]
    pypi_exists: bool | None
    npm_exists: bool | None
    github_repo_count: int | None
    notes: list[str]


def request_json(url: str, *, timeout: int = 12) -> tuple[int, Any | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except Exception:
        return 0, None


def has_dns(domain: str) -> bool:
    try:
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror:
        # Some parked domains only expose NS. Fall back to dig if available.
        try:
            result = subprocess.run(
                ["dig", "+short", "NS", domain],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            return False
        return bool(result.stdout.strip())


def pypi_exists(name: str) -> bool | None:
    status, _ = request_json(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
    if status == 200:
        return True
    if status == 404:
        return False
    return None


def npm_exists(name: str) -> bool | None:
    status, _ = request_json(f"https://registry.npmjs.org/{urllib.parse.quote(name)}")
    if status == 200:
        return True
    if status == 404:
        return False
    return None


def github_repo_count(name: str) -> int | None:
    query = urllib.parse.quote(f'"{name}" in:name')
    status, payload = request_json(f"https://api.github.com/search/repositories?q={query}")
    if status == 200 and isinstance(payload, dict):
        value = payload.get("total_count")
        return int(value) if isinstance(value, int) else None
    return None


def check_candidate(name: str) -> CandidateResult:
    domains = [f"{name}.{tld}" for tld in TLDS]
    domains_with_dns = [domain for domain in domains if has_dns(domain)]
    notes: list[str] = []

    if len(domains_with_dns) >= 4:
        notes.append("many common domains resolve")
    elif not domains_with_dns:
        notes.append("no DNS found for checked common domains")

    result = CandidateResult(
        name=name,
        domains_with_dns=domains_with_dns,
        pypi_exists=pypi_exists(name),
        npm_exists=npm_exists(name),
        github_repo_count=github_repo_count(name),
        notes=notes,
    )

    # Be polite-ish to unauthenticated APIs. Not perfect, but better than being a bot-goblin.
    time.sleep(0.5)
    return result


def main() -> int:
    results = [check_candidate(name) for name in CANDIDATES]
    payload = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "disclaimer": "Lightweight public collision check only; not trademark/legal clearance.",
        "tlds_checked": TLDS,
        "results": [asdict(result) for result in results],
    }
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
