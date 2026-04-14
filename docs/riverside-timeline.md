---
title: Riverside Compliance Timeline
---

# Riverside Compliance Timeline

**Deadline: July 8, 2026**

<div id="countdown" style="font-size:1.5rem;font-weight:bold;margin:1rem 0">
  Loading countdown…
</div>
<script>
(function () {
  const deadline = new Date('2026-07-08T00:00:00Z').getTime();
  const el = document.getElementById('countdown');
  function tick() {
    const diff = deadline - Date.now();
    if (diff <= 0) {
      el.textContent = 'Deadline reached.';
      return;
    }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff / 3600000) % 24);
    const m = Math.floor((diff / 60000) % 60);
    el.textContent = `${d} days · ${h} hours · ${m} minutes remaining`;
  }
  tick();
  setInterval(tick, 60000);
})();
</script>

## Scope

Head-to-Toe Brands is evaluated against Riverside's Cyber Health Check
framework across 7 capability domains. See
[`riverside-security-requirements/HEAD-TO-TOE-SECURITY-REQUIREMENTS-OUTLINE.md`](../riverside-security-requirements/HEAD-TO-TOE-SECURITY-REQUIREMENTS-OUTLINE.md)
for the authoritative requirements document.

## Maturity targets

| Domain | Current | Target |
|---|---|---|
| Governance & Strategy | 2.4 | 3.0 |
| Network & Infrastructure | 2.5 | 3.0 |
| Identity & Access Management | 2.3 | 3.0 |
| Application Security | 2.2 | 3.0 |
| Data Protection | — | 3.0 |
| Monitoring | — | 3.0 |
| Resilience | — | 3.0 |

_Scores update from the live platform (`/riverside/dashboard`) once the
sync jobs have populated `RiversideCompliance`. Until then, these are the
baseline numbers from the January 2026 Riverside health check._

## What's blocking go-live

Run `python scripts/audit_production.py --env production` then see
[status.md](status.md) for:

- Tenants missing Reader RBAC
- Tenants missing admin consent on required Graph scopes
- Domains with stale sync data
