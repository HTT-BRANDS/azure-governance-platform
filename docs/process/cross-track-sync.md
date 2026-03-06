# Cross-Track Synchronization Protocol

**Date:** 2026-03-06
**Owner:** Planning Agent 📋 + Pack Leader 🐺
**Sign-off:** Both (mutual)
**Task:** 3.3.3 / REQ-503

---

## Overview

When sprint-scale and large-scale tracks run concurrently, they must synchronize to avoid conflicts, duplicate work, and dependency violations. This document defines the protocol for cross-track coordination.

## The Problem

```
LARGE-SCALE TRACK                    SPRINT-SCALE TRACK
(Phase 2: Security Overhaul)         (Sprint 5: Auth Bug Fixes)
                                     
├── STRIDE analysis                  ├── Fix token refresh
├── YOLO_MODE audit                  ├── Fix session timeout
├── MCP trust boundaries             ├── Fix CORS headers
└── Self-modification protections    └── Fix rate limiter
                                     
Both tracks may touch:               
  - security/ directory              
  - auth middleware                   
  - configuration files              
  - shared dependencies              
```

Without synchronization, these tracks can produce merge conflicts, duplicate fixes, or contradictory changes.

---

## Shared Label Taxonomy

### Cross-Track Labels

Labels that apply to BOTH tracks use a shared namespace:

| Label | Meaning | Applied By |
|-------|---------|-----------|
| `security` | Security-related work | Any track |
| `architecture` | Architecture-related work | Any track |
| `ux-a11y` | UX/accessibility work | Any track |
| `testing` | Testing infrastructure | Any track |
| `documentation` | Documentation updates | Any track |

### Track-Specific Labels

| Label | Track | Example |
|-------|-------|---------|
| `sprint-N` | Sprint-scale | `sprint-1`, `sprint-5` |
| `phase-N` | Large-scale | `phase-2`, `phase-3` |

### Conflict Detection

```bash
# Find issues touching the same domain across tracks
bd list --label security --label sprint-5     # Sprint security work
bd list --label security --label phase-2      # Large-scale security work

# If both return results → POTENTIAL CONFLICT
# Pack Leader must review and coordinate
```

---

## Synchronization Protocol

### Daily Sync Check

Pack Leader performs at start of each work session:

```bash
# 1. Check both tracks
echo "=== SPRINT TRACK ==="
bd list --label sprint-$(CURRENT_SPRINT) --status open

echo "=== LARGE-SCALE TRACK ==="
bd list --label phase-$(CURRENT_PHASE) --status open

# 2. Check for domain overlaps
for domain in security architecture ux-a11y testing; do
  sprint_count=$(bd list --label sprint-$(CURRENT_SPRINT) --label $domain 2>/dev/null | wc -l)
  phase_count=$(bd list --label phase-$(CURRENT_PHASE) --label $domain 2>/dev/null | wc -l)
  if [ $sprint_count -gt 0 ] && [ $phase_count -gt 0 ]; then
    echo "⚠️  OVERLAP in $domain: $sprint_count sprint + $phase_count phase issues"
  fi
done

# 3. Check git for branch conflicts
git log --oneline feature/sprint-base..feature/phase-base  # What's different?
```

### Conflict Resolution Strategies

#### Strategy 1: Sequencing
When both tracks touch the same files:
```
Large-scale completes first → Sprint merges on top
OR
Sprint ships quick fix → Large-scale incorporates
```
**Decision criteria:** Which delivers more value sooner?

#### Strategy 2: Partitioning
Divide the domain so tracks don't overlap:
```
Large-scale: docs/security/ (policy documents)
Sprint: src/security/ (code fixes)
```
**Decision criteria:** Can work be cleanly separated?

#### Strategy 3: Shared Base
Both tracks merge to the same base branch:
```
feature/security-improvements ← both tracks merge here
```
**Decision criteria:** Work is tightly coupled

---

## Base Branch Management

### Independent Base Branches (Default)

```
main
├── feature/sprint-5-auth-fixes      ← Sprint base
└── feature/phase-2-security         ← Large-scale base
```

Each track merges to its own base. Final integration happens when both merge to main.

### Shared Base Branch (When Coupled)

```
main
└── feature/security-v2              ← Shared base
    ├── sprint work merges here
    └── phase work merges here
```

**When to use shared base:**
- Same files modified by both tracks
- Dependencies between sprint and phase work
- Pack Leader decides this during planning

### Merge Order

When merging to main:
1. Large-scale merges first (bigger scope, more files)
2. Sprint rebases on updated main
3. Sprint merges second
4. Resolve any remaining conflicts

---

## Communication Protocol

### Between Planning Agent and Pack Leader

```
Planning Agent: "Phase 3 tasks 3.1.2, 3.2.2, 3.3.3 are ready"
Pack Leader:    "Sprint 5 also has 3 auth fixes touching security/"
Planning Agent: "Recommend sequencing: sprint fixes first, phase work incorporates"
Pack Leader:    "Agreed. Sprint base: feature/sprint-5. Phase work starts after merge."
```

### Cross-Track bd Comments

When an issue in one track affects the other:
```bash
bd comment <sprint-id> "⚠️ Cross-track: Related to phase-2 issue <phase-id>. Coordinate before merge."
bd comment <phase-id> "⚠️ Cross-track: Sprint fix in <sprint-id> touches same files. Merge sprint first."
```

### Mutual Sign-off

Critical cross-track changes require both:
- **Planning Agent** signs off on roadmap alignment
- **Pack Leader** signs off on execution plan

```bash
bd comment <id> "✅ Planning Agent sign-off: Aligns with Phase 2 roadmap"
bd comment <id> "✅ Pack Leader sign-off: Execution plan approved, no conflicts"
```

---

## Dependency Management

### Cross-Track Dependencies

```bash
# Sprint task depends on phase work
bd create "Sprint: Update auth after STRIDE" \
  --deps "blocks:azure-governance-platform-xxx"  # Phase 2 STRIDE task

# Phase work depends on sprint fix
bd create "Phase: Incorporate auth fix in security docs" \
  --deps "blocks:azure-governance-platform-yyy"  # Sprint 5 auth fix
```

### Dependency Visualization

```bash
# View cross-track dependencies
bd dep tree <id>  # Shows full tree including cross-track deps

# Check for circular dependencies
bd blocked --json | jq '.[] | select(.labels | contains(["sprint"])) | select(.blocked_by | any(contains("phase")))'
```

---

## Integration Points

### WIGGUM_ROADMAP.md
Large-scale phases track strategic progress. Sprint work is noted but not individually tracked.

### TRACEABILITY_MATRIX.md
Both tracks contribute rows. Cross-track relationships noted in the "Notes" column.

### sync_roadmap.py
Only updates for large-scale task completion. Sprint work tracks separately via `bd`.

### bd
Single source of truth for BOTH tracks. Labels distinguish track membership.

---

## Example: SDLC Implementation + Maintenance

This project demonstrates cross-track sync:

**Large-Scale (Phase 2-3):** SDLC governance implementation
- STRIDE analysis, ADR workflow, fitness functions
- Process documentation, testing methodology

**Sprint (Concurrent):** Platform maintenance
- Replace fetch_data placeholders (azure-governance-platform-0p7)
- Add pre-commit hooks (azure-governance-platform-fp0)
- Deploy staging (azure-governance-platform-uh2)

**Sync Decision:** Sequential — SDLC phase work first (documentation), then sprint maintenance work (code changes). No file overlap.

---

## Checklist for New Cross-Track Scenarios

- [ ] Identify overlapping domains (use shared labels)
- [ ] Check for file-level conflicts
- [ ] Choose resolution strategy (sequence/partition/shared base)
- [ ] Document decision in bd comments
- [ ] Get mutual sign-off (Planning Agent + Pack Leader)
- [ ] Set merge order
- [ ] Monitor for emerging conflicts during execution

---

## References

- docs/process/sprint-track.md — Sprint-scale protocol
- docs/process/large-scale-track.md — Large-scale protocol
- docs/process/requirements-flow.md — How requirements enter both tracks

---

*Cross-track synchronization protocol. Owner: Planning Agent 📋 + Pack Leader 🐺. Mutual sign-off required.*
