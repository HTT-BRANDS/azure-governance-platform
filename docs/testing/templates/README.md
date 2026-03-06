# bd Issue Templates for Testing Phases

**Date:** 2026-03-06
**Owner:** Bloodhound 🐕‍🦺
**Sign-off:** Planning Agent 📋
**Task:** 3.1.2 / REQ-308

---

## Overview

These templates standardize bd issue creation for each of the 5 testing phases defined in the 13-step methodology. Each template includes required fields, labels, and acceptance criteria.

## Usage

Copy the appropriate template when creating a bd issue for testing work:

```bash
# Use the template structure when creating issues:
bd create "Test Prep: [feature]" -d "[paste template body]" --label test-prep --label phase-N
```

---

## Template 1: Test Preparation (Steps 1–4)

### bd create command
```bash
bd create "Test Prep: [feature name]" \
  -d "## Test Preparation
**Feature:** [feature name]
**Sprint:** [sprint number]
**Owner:** QA Expert 🐾

### Checklist
- [ ] Step 1: Review user stories and acceptance criteria
- [ ] Step 2: Draft test cases (positive, negative, edge)
- [ ] Step 3: Set up test environment
- [ ] Step 4: Automate test setup (CI config)

### Acceptance Criteria
- AC coverage report exists mapping every REQ to tests
- Test cases cover positive, negative, boundary conditions
- Test environment boots clean and reproducible
- CI pipeline runs tests via single command

### Artifacts
- [ ] AC coverage report
- [ ] Test case specifications
- [ ] Environment configuration
- [ ] CI workflow file (.github/workflows/)

### Sign-off
- [ ] QA Expert 🐾 confirms test design
- [ ] Shepherd 🐕 reviews test quality
- [ ] Watchdog 🐕‍🦺 verifies environment" \
  --label test-prep --label sprint-N
```

---

## Template 2: Test Execution (Steps 5–7)

### bd create command
```bash
bd create "Execute: [test suite name]" \
  -d "## Test Execution
**Suite:** [test suite name]
**Sprint:** [sprint number]
**Owner:** Watchdog 🐕‍🦺 (automated) / QA Kitten 🐱 (manual web) / Terminal QA 🖥️ (manual CLI)

### Checklist
- [ ] Step 5: Manual testing complete
- [ ] Step 6: Automated testing complete
- [ ] Step 7: All planned tests executed

### Acceptance Criteria
- All manual test cases executed and logged
- All automated tests pass (pytest exit 0)
- Coverage report meets threshold (≥80%)
- Full test report produced

### Results
| Test Type | Total | Pass | Fail | Skip |
|-----------|-------|------|------|------|
| Manual    |       |      |      |      |
| Unit      |       |      |      |      |
| Integration|      |      |      |      |
| E2E       |       |      |      |      |

### Artifacts
- [ ] Manual test execution log
- [ ] Automated test results
- [ ] Coverage report
- [ ] Combined test report

### Sign-off
- [ ] QA Expert 🐾 reviews all results
- [ ] Pack Leader 🐺 approves combined report" \
  --label test-exec --label sprint-N
```

---

## Template 3: Issue Management (Steps 8–9)

### bd create command
```bash
bd create "Defect: [bug description]" \
  -d "## Defect Report
**Severity:** [P0-Critical | P1-High | P2-Medium | P3-Low]
**Found in:** [test phase/step]
**Reporter:** [agent name]

### Description
[Brief description of the defect]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Environment
- Branch: [branch name]
- Worktree: [worktree path]
- Python: [version]
- OS: [os info]

### Evidence
- [ ] Screenshots/logs attached
- [ ] Minimal reproduction case

### Fix Verification (Step 9)
- [ ] Fix committed by Husky 🐺
- [ ] Code reviewed by Shepherd 🐕
- [ ] Regression tests pass (Watchdog 🐕‍🦺)
- [ ] Original test case now passes

### Sign-off
- [ ] QA Expert 🐾 verifies fix" \
  --label defect --label severity-[P0-P3]
```

---

## Template 4: Performance & Security (Steps 10–11)

### bd create command
```bash
bd create "Perf/Sec: [component name]" \
  -d "## Performance & Security Testing
**Component:** [component name]
**Owner:** QA Expert 🐾 (perf) / Security Auditor 🛡️ (security)

### Performance Testing (Step 10)
- [ ] Response time benchmarks
- [ ] Throughput testing
- [ ] Resource usage profiling
- [ ] Load testing (if applicable)

#### Performance Results
| Metric | Baseline | Actual | Threshold | Status |
|--------|----------|--------|-----------|--------|
| Response time (p95) | | | <200ms | |
| Throughput | | | >100 rps | |
| Memory usage | | | <512MB | |
| CPU usage | | | <70% | |

### Security Testing (Step 11)
- [ ] STRIDE analysis review (docs/security/stride-analysis.md)
- [ ] OWASP ASVS checklist
- [ ] Dependency vulnerability scan
- [ ] Static analysis (bandit)

#### Security Results
| Check | Tool | Result | Issues |
|-------|------|--------|--------|
| STRIDE coverage | Manual | | |
| Dependency scan | safety | | |
| Static analysis | bandit | | |
| Secret detection | detect-secrets | | |

### Acceptance Criteria
- No P0/P1 performance regressions
- No critical/high security vulnerabilities
- STRIDE rows complete for component

### Sign-off
- [ ] Solutions Architect 🏛️ reviews performance
- [ ] Pack Leader 🐺 reviews security" \
  --label perf-security --label sprint-N
```

---

## Template 5: Documentation & Closure (Steps 12–13)

### bd create command
```bash
bd create "Closure: [feature/sprint name]" \
  -d "## Documentation & Closure
**Feature/Sprint:** [name]
**Owner:** Planning Agent 📋

### Documentation Updates (Step 12)
- [ ] README.md updated
- [ ] TRACEABILITY_MATRIX.md updated
- [ ] WIGGUM_ROADMAP.md updated (sync_roadmap.py)
- [ ] API documentation updated
- [ ] Architecture decisions recorded (ADRs)

### Stakeholder Feedback (Step 13)
- [ ] Test results presented
- [ ] Demo completed (if applicable)
- [ ] Feedback captured in bd comments
- [ ] Sign-off recorded

### Acceptance Criteria
- All documentation reflects current state
- TRACEABILITY_MATRIX.md has no gaps
- Roadmap updated via sync_roadmap.py
- Stakeholder approval recorded

### Closure Checklist
- [ ] All bd issues for feature/sprint closed
- [ ] All worktrees cleaned up
- [ ] All branches merged to base
- [ ] git push completed
- [ ] Next session handoff documented

### Sign-off
- [ ] Code Reviewer 🛡️ reviews documentation
- [ ] Pack Leader 🐺 + Planning Agent 📋 final approval" \
  --label documentation --label closure
```

---

## Quick Reference

| Phase | Template | Labels | Owner |
|-------|----------|--------|-------|
| Test Preparation | Template 1 | `test-prep` | QA Expert 🐾 |
| Test Execution | Template 2 | `test-exec` | Watchdog 🐕‍🦺ᅵ |
| Issue Management | Template 3 | `defect` | Bloodhound 🐕‍🦺 |
| Perf & Security | Template 4 | `perf-security` | QA Expert 🐾 / Security Auditor 🛡️ |
| Doc & Closure | Template 5 | `documentation`, `closure` | Planning Agent 📋 |

---

## References

- docs/testing/13-step-methodology.md — Full methodology with agent assignments
- TRACEABILITY_MATRIX.md — REQ-308

---

*bd issue templates for testing phases. Owner: Bloodhound 🐕‍🦺, Sign-off: Planning Agent 📋.*
