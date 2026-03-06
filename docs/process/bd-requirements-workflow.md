# bd Workflows for Requirements Chain

**Date:** 2026-03-06
**Owner:** Bloodhound 🐕‍🦺
**Sign-off:** Planning Agent 📋
**Task:** 3.2.2 / REQ-402

---

## Overview

This document defines how bd issues flow through the requirements chain: from stakeholder request → BRD → user stories → sprint → delivery. Each stage has specific labels, transitions, and agent handoffs.

## Requirements Chain Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  STAKEHOLDER │────→│     BRD      │────→│ USER STORIES │
│   REQUEST    │     │  (Business   │     │  (Refined &  │
│              │     │  Requirements│     │   Estimated) │
│ Label:       │     │  Document)   │     │              │
│  stakeholder │     │ Label: brd   │     │ Label: story │
│ Agent:       │     │ Agent:       │     │ Agent:       │
│  Bloodhound  │     │ Planning Agt │     │ Pack Leader  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                     ┌──────────────────────────┘
                     │
              ┌──────▼───────┐     ┌──────────────┐
              │   SPRINT     │────→│   DELIVERY   │
              │  (Selected & │     │  (Merged &   │
              │   Assigned)  │     │   Deployed)  │
              │              │     │              │
              │ Label:       │     │ Label:       │
              │  sprint-N    │     │  delivered   │
              │ Agent:       │     │ Agent:       │
              │  Pack Leader │     │  Retriever   │
              └──────────────┘     └──────────────┘
```

---

## Stage 1: Stakeholder Request

### Entry Criteria
- New requirement identified by stakeholder or through research

### bd Actions
```bash
# Bloodhound creates intake issue
bd create "Request: [description]" \
  -d "## Stakeholder Request
**Source:** [stakeholder/research/incident]
**Priority:** [P1-P3]
**Description:** [what is needed and why]
**Business Value:** [expected outcome]" \
  --label stakeholder
```

### Exit Criteria
- Issue exists in bd with `stakeholder` label
- Priority assigned
- Description clear enough for analysis

### Agent Handoff
- **From:** External (stakeholder) or Web Puppy (research)
- **To:** Planning Agent (analysis)

---

## Stage 2: BRD (Business Requirements Document)

### Entry Criteria
- Stakeholder request exists in bd
- Planning Agent has reviewed and accepted

### bd Actions
```bash
# Planning Agent updates issue
bd update <id> --label brd

# Planning Agent adds analysis
bd comment <id> "## BRD Analysis
**Scope:** [in/out of scope items]
**Dependencies:** [external dependencies]
**Risks:** [identified risks]
**Estimated effort:** [S/M/L/XL]
**Recommended approach:** [brief technical approach]"

# Create dependency links
bd dep add <id> blocks:<downstream-id>
```

### Exit Criteria
- Issue has `brd` label
- Scope defined (in/out)
- Dependencies identified
- Effort estimated
- Risks documented

### Agent Handoff
- **From:** Planning Agent (analysis)
- **To:** Architects (technical specification) + Pack Leader (prioritization)

---

## Stage 3: User Stories

### Entry Criteria
- BRD analysis complete
- Technical approach defined by architects

### bd Actions
```bash
# Pack Leader refines into user stories
bd create "US: As a [role], I want [feature], so that [benefit]" \
  -d "## User Story
**Epic:** [parent requirement]
**Acceptance Criteria:**
- [ ] AC1: [criteria]
- [ ] AC2: [criteria]
- [ ] AC3: [criteria]

**Technical Notes:** [from architects]
**TRACEABILITY:** REQ-[XXX]" \
  --label story --deps "blocks:<parent-id>"

# Link to TRACEABILITY_MATRIX
# REQ-XXX → Agent → Reviewer → Test → Sign-off
```

### Exit Criteria
- User stories exist with clear acceptance criteria
- Stories linked to parent BRD issue
- TRACEABILITY_MATRIX entry created
- Architect review complete

### Agent Handoff
- **From:** Pack Leader (story creation)
- **To:** Pack Leader (sprint selection)

---

## Stage 4: Sprint Selection

### Entry Criteria
- User stories refined and estimated
- Dependencies resolved or mapped

### bd Actions
```bash
# Pack Leader selects for sprint
bd update <id> --label sprint-N
bd update <id> --status in_progress

# Pack Leader declares base branch
# "Working from base branch: feature/sprint-N-[name]"

# Terrier creates worktrees for each task
# Husky executes tasks
```

### Exit Criteria
- Issues labeled with `sprint-N`
- Base branch declared
- Worktrees created for active tasks
- Huskies dispatched

### Agent Handoff
- **From:** Pack Leader (selection)
- **To:** Terrier (worktree) → Husky (execution) → Critics (review)

---

## Stage 5: Delivery

### Entry Criteria
- Husky completed implementation
- Shepherd code review: APPROVE
- Watchdog QA: APPROVE

### bd Actions
```bash
# After critic approval
bd comment <id> "Shepherd: APPROVE - [review notes]"
bd comment <id> "Watchdog: APPROVE - [QA notes]"

# Retriever merges to base branch
# git checkout base-branch
# git merge feature/bd-N-slug --no-ff

# Close and label
bd update <id> --label delivered
bd close <id>

# Update roadmap
python scripts/sync_roadmap.py --update --task X.Y.Z
```

### Exit Criteria
- Branch merged to base
- Issue closed with `delivered` label
- Worktree cleaned up
- Roadmap updated

### Agent Handoff
- **From:** Retriever (merge)
- **To:** Bloodhound (close) → Planning Agent (roadmap update)

---

## Label State Machine

```
stakeholder → brd → story → sprint-N → delivered
     │                          │
     │         (rejected)       │ (failed)
     └─→ wont-fix              └─→ blocked → sprint-N (retry)
```

### Complete Label Set

| Label | Stage | Applied By |
|-------|-------|-----------|
| `stakeholder` | Intake | Bloodhound |
| `brd` | Analysis | Planning Agent |
| `story` | Refinement | Pack Leader |
| `sprint-N` | Execution | Pack Leader |
| `in-review` | Critic gates | Shepherd/Watchdog |
| `delivered` | Complete | Retriever |
| `blocked` | Dependency wait | Automatic (bd) |
| `wont-fix` | Rejected | Pack Leader |

---

## Automated Transitions

### bd Query Patterns

```bash
# Find items needing analysis (stakeholder → brd)
bd list --label stakeholder    # What needs BRD analysis?

# Find items ready for sprint (story, not in sprint)
bd list --label story          # Refined stories
bd ready --json                # Unblocked items

# Track sprint progress
bd list --label sprint-1 --status open    # In progress
bd list --label sprint-1 --status closed  # Done

# Find delivered items
bd list --label delivered      # All delivered work
```

### Reporting

```bash
# Requirements flow metrics
echo "=== REQUIREMENTS PIPELINE ==="
echo "Intake:    $(bd list --label stakeholder 2>/dev/null | wc -l) items"
echo "Analysis:  $(bd list --label brd 2>/dev/null | wc -l) items"
echo "Stories:   $(bd list --label story 2>/dev/null | wc -l) items"
echo "Sprint:    $(bd list --label sprint-1 2>/dev/null | wc -l) items"
echo "Delivered: $(bd list --label delivered 2>/dev/null | wc -l) items"
```

---

## Integration Points

### TRACEABILITY_MATRIX.md
Every user story gets a row in the traceability matrix:
```
| REQ-XXX | [Description] | [Owner Agent] | [Reviewer] | [Test] | [Sign-off] |
```

### WIGGUM_ROADMAP.md
Large-scale requirements map to roadmap tasks:
```
- [ ] X.Y.Z: [task] — bd issue: azure-governance-platform-xxx
```

### 13-Step Testing Methodology
Test requirements flow through testing templates (docs/testing/templates/).

---

## References

- docs/process/requirements-flow.md — 9-role mapping
- docs/testing/templates/README.md — Testing issue templates
- TRACEABILITY_MATRIX.md — Requirements traceability

---

*bd workflow configuration for requirements chain. Owner: Bloodhound 🐕‍🦺, Sign-off: Planning Agent 📋.*
