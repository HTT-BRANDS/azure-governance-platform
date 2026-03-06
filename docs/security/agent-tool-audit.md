# Agent Tool Permission Audit — Least-Privilege Compliance

| Field | Value |
|---|---|
| **Audit ID** | ATPA-2026-001 |
| **Auditor** | Security Auditor 🛡️ (`security-auditor-06e3ba`) |
| **Date** | 2026-03-06 |
| **Scope** | All 29 registered agents — 26 built-in Python + 3 custom JSON |
| **Standard** | OWASP ASVS v4 §1.4 (Access Control Architecture), NIST AC-6 (Least Privilege), ISO 27001 A.9.4 |
| **Task** | 1.1.3 / REQ-103 / bd `azure-governance-platform-ivd` |
| **Verdict** | **Needs Fixes** — 4 agents over-privileged relative to stated role |

---

## Executive Summary

The Code Puppy agent platform implements a **per-agent tool allow-list** that controls which capabilities each agent can invoke. This is a sound least-privilege mechanism — the platform defaults to denying tools not explicitly listed.

**Good news:** 22 of 29 agents (76%) have tool sets properly scoped to their roles. The 8 code-reviewer variants and 6 pack agents consistently follow minimal-permission patterns. This is excellent and deserves recognition.

**Bad news:** 4 agents have permissions that exceed their documented roles. Three of these are custom JSON agents (`web-puppy`, `solutions-architect`, `experience-architect`) and one is the `helios` built-in. The most critical concern is `web-puppy` — a research agent with `delete_file`, `agent_run_shell_command`, and `universal_constructor` access.

---

## Findings Summary

| ID | Severity | Agent | Finding | CVSS v4.0 Est. |
|---|---|---|---|---|
| F-001 | **Critical** | web-puppy | Universal constructor + delete + shell on a research agent | 8.5 |
| F-002 | **High** | solutions-architect | `edit_file` contradicts "NOT an implementer" mandate | 6.8 |
| F-003 | **High** | experience-architect | `edit_file` on an architect role; no scoped path restriction | 6.8 |
| F-004 | **High** | web-puppy | `delete_file` unjustified for research role | 7.2 |
| F-005 | **Medium** | helios | Full toolkit + `universal_constructor` — documented but no guardrails artifact | 5.5 |
| F-006 | **Medium** | agent-creator | Can write agent JSON → indirect privilege escalation path | 5.0 |
| F-007 | **Medium** | scheduler-agent | `scheduler_run_task` is a persistence/execution mechanism | 4.5 |
| F-008 | **Medium** | (platform) | No path-scoped file access — `edit_file` can write anywhere the process reaches | 5.5 |
| F-009 | **Low** | terminal-qa | `terminal_run_command` ≈ shell access (by design for TUI testing) | 3.5 |
| F-010 | **Low** | all reviewers | `agent_run_shell_command` on read-only roles — needed for linters, but adds surface | 3.0 |
| F-011 | **Observation** | 8 agents | `invoke_agent`/`list_agents` creates lateral movement trust boundary | — |

---

## Tool Legend

| Tool | Capability | Trust Level | Risk Profile |
|---|---|---|---|
| `list_files` | Directory listing | Low | Read-only reconnaissance |
| `read_file` | File content access | Low | Information disclosure |
| `grep` | Pattern search across files | Low | Read-only reconnaissance |
| `edit_file` | Create/modify any file | **High** | Arbitrary write, code injection, config tampering |
| `delete_file` | Remove any file | **High** | Data destruction, availability impact |
| `agent_run_shell_command` | Execute OS commands | **Critical** | Full system access within process permissions |
| `agent_share_your_reasoning` | Emit reasoning to user | Minimal | Transparency tool, no side effects |
| `invoke_agent` | Delegate to another agent | **Medium** | Trust boundary crossing, lateral movement |
| `list_agents` | Enumerate available agents | Low | Agent discovery |
| `universal_constructor` | Generate and execute arbitrary Python | **Critical** | Equivalent to RCE within process context |

---

## Per-Agent Audit

### Category 1: Primary Agent

#### 1. code-puppy (Code-Puppy 🐶)
- **Source**: `code_puppy/agents/agent_code_puppy.py`
- **Role**: General-purpose coding assistant — the "main" agent users interact with
- **Tools**: `list_agents`, `invoke_agent`, `list_files`, `read_file`, `grep`, `edit_file`, `delete_file`, `agent_run_shell_command`, `agent_share_your_reasoning`, `ask_user_question`, `activate_skill`, `list_or_search_skills`, `load_image_for_analysis`
- **Verdict**: ✅ **PASS** — Full toolkit justified. This is the primary interactive agent; users expect it to read, write, execute, and coordinate.
- **Notes**: Has `load_image_for_analysis` for vision tasks. All tools match the "do anything the user asks" mandate.

---

### Category 2: Code Reviewers (×8) — Consistent Read-Only Pattern 🏆

All 8 reviewer agents share an identical, well-scoped tool set:

```
agent_share_your_reasoning, agent_run_shell_command,
list_files, read_file, grep, invoke_agent, list_agents
```

| # | Agent | Slug | Source |
|---|---|---|---|
| 2 | Code Reviewer 🛡️ | `code-reviewer` | `agent_code_reviewer.py` |
| 3 | C Reviewer 🧵 | `c-reviewer` | `agent_c_reviewer.py` |
| 4 | C++ Reviewer 🛠️ | `cpp-reviewer` | `agent_cpp_reviewer.py` |
| 5 | Golang Reviewer 🦴 | `golang-reviewer` | `agent_golang_reviewer.py` |
| 6 | JavaScript Reviewer ⚡ | `javascript-reviewer` | `agent_javascript_reviewer.py` |
| 7 | Python Reviewer 🐍 | `python-reviewer` | `agent_python_reviewer.py` |
| 8 | TypeScript Reviewer 🦾 | `typescript-reviewer` | `agent_typescript_reviewer.py` |
| 9 | Security Auditor 🛡️ | `security-auditor` | `agent_security_auditor.py` |

**Justification per tool:**
| Tool | Justified? | Rationale |
|---|---|---|
| `list_files` | ✅ | Navigate project structure to find relevant files |
| `read_file` | ✅ | Read code for review |
| `grep` | ✅ | Search for patterns, anti-patterns, vulnerabilities |
| `agent_run_shell_command` | ✅ | Run linters, type checkers, SAST tools (`ruff`, `mypy`, `semgrep`, etc.) |
| `agent_share_your_reasoning` | ✅ | Document review rationale |
| `invoke_agent` | ✅ | Collaborate with other reviewers for cross-language concerns |
| `list_agents` | ✅ | Discover available specialist agents |
| `edit_file` | ✅ **ABSENT** | Correctly excluded — reviewers should not modify code |
| `delete_file` | ✅ **ABSENT** | Correctly excluded |

**Verdict**: ✅ **PASS** — Exemplary least-privilege. No write capabilities. Shell access is justified for static analysis tooling. This is the gold-standard pattern.

> **🦴 Good boy treat**: The consistent tool set across all 8 reviewers shows disciplined design. Zero drift.

---

### Category 3: QA & Testing Agents

#### 10. QA Expert 🐾 (`qa-expert`)
- **Source**: `code_puppy/agents/agent_qa_expert.py`
- **Tools**: `agent_share_your_reasoning`, `agent_run_shell_command`, `list_files`, `read_file`, `grep`, `invoke_agent`, `list_agents`
- **Verdict**: ✅ **PASS** — Same read-only + shell pattern as reviewers. Appropriate for a QA planning role.

#### 11. Quality Assurance Kitten 🐱 (`qa-kitten`)
- **Source**: `code_puppy/agents/agent_qa_kitten.py`
- **Tools**: `agent_share_your_reasoning`, 20+ `browser_*` tools, `load_image_for_analysis`, `browser_save_workflow`, `browser_list_workflows`, `browser_read_workflow`
- **Notable**: Has `browser_execute_js` (can run JavaScript in browser context)
- **Verdict**: ✅ **PASS** — Scoped exclusively to browser automation. No `list_files`, `read_file`, `edit_file`, `delete_file`, or `agent_run_shell_command`. Clean boundary.
- **Note**: `browser_execute_js` is needed for advanced QA scenarios but is a trust boundary within the browser context.

#### 12. Terminal QA Agent 🖥️ (`terminal-qa`)
- **Source**: `code_puppy/agents/agent_terminal_qa.py`
- **Tools**: `agent_share_your_reasoning`, `start_api_server`, `terminal_check_server`, `terminal_open`, `terminal_close`, `terminal_run_command`, `terminal_send_keys`, `terminal_wait_output`, `terminal_screenshot_analyze`, `terminal_read_output`, `terminal_compare_mockup`, `load_image_for_analysis`
- **Verdict**: ⚠️ **CONDITIONAL PASS** (Finding F-009)
- **Note**: `terminal_run_command` and `terminal_send_keys` can execute arbitrary commands. `start_api_server` spawns a process. This is **by design** for TUI testing, but the risk should be documented. No file read/write tools, which limits blast radius.

#### 13. Watchdog 🐕‍🦺 (`watchdog`)
- **Source**: `code_puppy/agents/pack/watchdog.py`
- **Tools**: `list_files`, `read_file`, `grep`, `agent_run_shell_command`, `agent_share_your_reasoning`
- **Verdict**: ✅ **PASS** — Read-only + shell for running tests. No edit/delete, no agent invocation. Minimal.

---

### Category 4: Orchestrators & Planners

#### 14. Planning Agent 📋 (`planning-agent`)
- **Source**: `code_puppy/agents/agent_planning.py`
- **Tools**: `list_files`, `read_file`, `grep`, `agent_share_your_reasoning`, `ask_user_question`, `list_agents`, `invoke_agent`, `list_or_search_skills`
- **Verdict**: ✅ **PASS** — Pure read-only orchestrator. No shell, no edit, no delete. Clean.

> **🦴 Good boy treat**: Planning Agent is the cleanest orchestrator pattern — all brain, no hands.

#### 15. Pack Leader 🐺 (`pack-leader`)
- **Source**: `code_puppy/agents/agent_pack_leader.py`
- **Tools**: `list_files`, `read_file`, `grep`, `agent_run_shell_command`, `agent_share_your_reasoning`, `list_agents`, `invoke_agent`, `list_or_search_skills`
- **Verdict**: ✅ **PASS** — Orchestrator with shell (for `bd` and `git` commands). No edit/delete. Properly delegates implementation to Husky.

---

### Category 5: Implementation Agents (Full Toolkit — Justified)

#### 16. Python Programmer 🐍 (`python-programmer`)
- **Source**: `code_puppy/agents/agent_python_programmer.py`
- **Tools**: `list_agents`, `invoke_agent`, `list_files`, `read_file`, `grep`, `edit_file`, `delete_file`, `agent_run_shell_command`, `agent_share_your_reasoning`, `activate_skill`, `list_or_search_skills`
- **Verdict**: ✅ **PASS** — Full development toolkit. Implementer role justifies write + shell + delete.

#### 17. Husky 🐺 (`husky`)
- **Source**: `code_puppy/agents/pack/husky.py`
- **Tools**: `list_files`, `read_file`, `grep`, `edit_file`, `delete_file`, `agent_run_shell_command`, `agent_share_your_reasoning`, `activate_skill`, `list_or_search_skills`
- **Verdict**: ✅ **PASS** — The designated implementation sled dog. Full toolkit, no agent invocation (receives work, doesn't delegate). Clean.

> **🦴 Good boy treat**: Husky has no `invoke_agent`/`list_agents` — correctly cannot spawn other agents. Segregation of duties between orchestration (Pack Leader) and execution (Husky) is well enforced.

---

### Category 6: Pack Specialists (Minimal Toolkits)

#### 18. Bloodhound 🐕‍🦺 (`bloodhound`)
- **Source**: `code_puppy/agents/pack/bloodhound.py`
- **Tools**: `agent_run_shell_command`, `agent_share_your_reasoning`, `read_file`
- **Verdict**: ✅ **PASS** — Only 3 tools. Shell for `bd` commands, `read_file` for issue context. Leanest agent in the pack.

#### 19. Retriever 🦮 (`retriever`)
- **Source**: `code_puppy/agents/pack/retriever.py`
- **Tools**: `agent_run_shell_command`, `agent_share_your_reasoning`, `read_file`, `grep`, `list_files`
- **Verdict**: ✅ **PASS** — Read-only + shell for git merge operations. No write capabilities.

#### 20. Shepherd 🐕 (`shepherd`)
- **Source**: `code_puppy/agents/pack/shepherd.py`
- **Tools**: `list_files`, `read_file`, `grep`, `agent_run_shell_command`, `agent_share_your_reasoning`
- **Verdict**: ✅ **PASS** — Code review critic with read-only access. No edit/delete, no agent invocation.

#### 21. Terrier 🐕 (`terrier`)
- **Source**: `code_puppy/agents/pack/terrier.py`
- **Tools**: `agent_run_shell_command`, `agent_share_your_reasoning`, `list_files`
- **Verdict**: ✅ **PASS** — Only 3 tools. Shell for `git worktree` commands. No read_file even — maximum constraint.

---

### Category 7: Specialized Utility Agents

#### 22. Agent Creator 🏗️ (`agent-creator`)
- **Source**: `code_puppy/agents/agent_creator_agent.py`
- **Tools**: `list_files`, `read_file`, `edit_file`, `agent_share_your_reasoning`, `ask_user_question`, `list_agents`, `invoke_agent`, (+ `universal_constructor` if enabled)
- **Verdict**: ⚠️ **CONDITIONAL PASS** (Finding F-006)
- **Justification**: `edit_file` is required — this agent's entire purpose is writing agent JSON files to `~/.code_puppy/agents/`.
- **Concern**: Agent-creator writes tool permission lists for new agents. This is an **indirect privilege escalation path**: it can create agents with broader tool access than itself. Should be paired with schema validation (currently implemented) and review gates.
- **Positive**: No `delete_file`, no `agent_run_shell_command`. Well-constrained relative to its power.

#### 23. Prompt Reviewer 📝 (`prompt-reviewer`)
- **Source**: `code_puppy/agents/prompt_reviewer.py`
- **Tools**: `list_files`, `read_file`, `grep`, `agent_share_your_reasoning`, `agent_run_shell_command`
- **Verdict**: ✅ **PASS** — Minimal. No edit/delete, no agent invocation. Read-only + shell for analysis.

#### 24. Scheduler Agent 📅 (`scheduler-agent`)
- **Source**: `code_puppy/agents/agent_scheduler.py`
- **Tools**: `list_files`, `read_file`, `grep`, `agent_share_your_reasoning`, `ask_user_question`, `scheduler_list_tasks`, `scheduler_create_task`, `scheduler_delete_task`, `scheduler_toggle_task`, `scheduler_daemon_status`, `scheduler_start_daemon`, `scheduler_stop_daemon`, `scheduler_run_task`, `scheduler_view_log`
- **Verdict**: ⚠️ **CONDITIONAL PASS** (Finding F-007)
- **Note**: `scheduler_create_task` + `scheduler_run_task` constitute a **persistence mechanism** — tasks survive sessions and run automatically. `scheduler_start_daemon` spawns a background process. These are by design, but represent a notable attack surface if an adversary can inject prompts.

#### 25. Helios ☀️ (`helios`)
- **Source**: `code_puppy/agents/agent_helios.py`
- **Tools**: `universal_constructor`, `list_files`, `read_file`, `grep`, `edit_file`, `delete_file`, `agent_run_shell_command`, `agent_share_your_reasoning`
- **Verdict**: ⚠️ **CONDITIONAL PASS** (Finding F-005)
- **Note**: Maximum power by design. `universal_constructor` can synthesize and execute arbitrary Python code. Combined with `edit_file`, `delete_file`, and `agent_run_shell_command`, this agent has full system access within process permissions.
- **Compensating control**: User must explicitly switch to Helios via `/agent helios`. Not the default agent.
- **Missing**: No formal guardrails artifact or threat model documenting acceptable use boundaries.

---

### Category 8: Custom JSON Agents (⚠️ Findings Here)

#### 26. Solutions Architect 🏛️ (`solutions-architect`)
- **Source**: `~/.code_puppy/agents/solutions-architect.json`
- **Tools**: `list_files`, `read_file`, `grep`, `edit_file`, `agent_share_your_reasoning`, `invoke_agent`, `list_agents`, `agent_run_shell_command`
- **Verdict**: ❌ **FAIL** (Finding F-002)
- **Issue**: System prompt explicitly states: *"NOT an implementer — you design, Husky implements"* and *"NOT a code reviewer — Shepherd handles that."* Yet the agent has `edit_file` and `agent_run_shell_command`.
- **Justification claimed**: Saving ADRs and research to `./research/` and `docs/decisions/`.
- **Risk**: An architect agent with write + shell access can modify production code, IaC, or pipeline configs — violating segregation of duties.
- **Recommendation**: Remove `edit_file` and `agent_run_shell_command`. If ADR writing is needed, delegate to Husky via `invoke_agent`, or scope edit access to specific paths only (requires platform feature).

#### 27. Experience Architect 🎨 (`experience-architect`)
- **Source**: `~/.code_puppy/agents/experience-architect.json`
- **Tools**: `list_files`, `read_file`, `grep`, `edit_file`, `agent_share_your_reasoning`, `invoke_agent`, `list_agents`, `agent_run_shell_command`
- **Verdict**: ❌ **FAIL** (Finding F-003)
- **Issue**: Same over-privilege as Solutions Architect. Has `edit_file` and `agent_run_shell_command` despite being a design/analysis role.
- **Justification claimed**: Saving research and producing manual audit checklists.
- **Risk**: Can modify any file in the project — CSS, HTML templates, privacy configs, accessibility configs — without going through the Husky → Shepherd review pipeline.
- **Recommendation**: Remove `edit_file` and `agent_run_shell_command`. Delegate file creation to Husky.

#### 28. Web-Puppy 🕵️‍♂️ (`web-puppy`)
- **Source**: `~/.code_puppy/agents/web-puppy.json`
- **Tools**: 20+ `browser_*` tools, `list_files`, `read_file`, `edit_file`, `delete_file`, `agent_run_shell_command`, `agent_share_your_reasoning`, `universal_constructor`
- **Verdict**: ❌ **FAIL — CRITICAL** (Findings F-001, F-004)
- **Issue**: This is a **research agent** with the tool surface of a **god-mode agent**.
  - `universal_constructor`: Can generate and execute arbitrary Python. Unjustified for web research.
  - `delete_file`: Can destroy any file. Unjustified for research.
  - `agent_run_shell_command`: Can execute OS commands. Unjustified for research.
  - `edit_file`: Marginally justified for saving research to `./research/` directories, but unscoped.
- **Blast radius**: If web-puppy is compromised via malicious web content (e.g., prompt injection via scraped page), the attacker gains: arbitrary code execution (`universal_constructor`), file system write/delete, and OS shell access.
- **Recommendation**:
  - **Immediate**: Remove `universal_constructor` and `delete_file`.
  - **Short-term**: Remove `agent_run_shell_command`.
  - **Medium-term**: Scope `edit_file` to `./research/` paths only (requires platform feature).

---

## Findings Detail

### F-001 — CRITICAL: Web-Puppy Has Universal Constructor + Shell + Delete

| Field | Value |
|---|---|
| **Severity** | Critical |
| **CVSS v4.0** | 8.5 (AV:N/AC:L/AT:N/PR:N/UI:P/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N) |
| **Agent** | `web-puppy` (`~/.code_puppy/agents/web-puppy.json`) |
| **Control** | OWASP ASVS 1.4.1 — Verify least privilege access controls |
| **Standard** | NIST AC-6 Least Privilege, ISO 27001 A.9.4.1 |

**Description**: The web-puppy research agent has `universal_constructor`, `delete_file`, and `agent_run_shell_command` — capabilities that together constitute full system access. This agent regularly processes untrusted web content (scraped pages), making it the most exposed agent to prompt injection attacks.

**Business Impact**: A prompt injection attack via malicious web content could escalate to arbitrary code execution, data destruction, or lateral movement to other systems.

**Remediation**:
- **Immediate (Day 1)**: Remove `universal_constructor` and `delete_file` from `web-puppy.json`.
- **Short-term (Week 1)**: Remove `agent_run_shell_command`.
- **Long-term**: Implement path-scoped `edit_file` at the platform level.
- **Owner**: Agent Creator / Platform team
- **Verification**: Re-audit tool list; confirm web-puppy can still save research files.

---

### F-002 — HIGH: Solutions Architect Has edit_file (Segregation of Duties Violation)

| Field | Value |
|---|---|
| **Severity** | High |
| **CVSS v4.0** | 6.8 |
| **Agent** | `solutions-architect` (`~/.code_puppy/agents/solutions-architect.json`) |
| **Control** | OWASP ASVS 1.4.2 — Enforce separation of privilege |

**Description**: The Solutions Architect's own system prompt states it is *"NOT an implementer"* — yet it has `edit_file` and `agent_run_shell_command`. This violates the separation of duties between architect (design) and implementer (Husky).

**Business Impact**: Architectural decisions bypass the implementation → review → merge pipeline. Changes made directly by the architect skip Shepherd's code review and Watchdog's QA checks.

**Remediation**:
- **Immediate**: Remove `edit_file` and `agent_run_shell_command` from `solutions-architect.json`.
- **Alternative**: If ADR file writing is essential, delegate to Husky via `invoke_agent` with the ADR content.
- **Owner**: Agent Creator
- **Verification**: Confirm Solutions Architect can still produce ADRs via delegation.

---

### F-003 — HIGH: Experience Architect Has edit_file (Same Violation)

| Field | Value |
|---|---|
| **Severity** | High |
| **CVSS v4.0** | 6.8 |
| **Agent** | `experience-architect` (`~/.code_puppy/agents/experience-architect.json`) |
| **Control** | OWASP ASVS 1.4.2, NIST AC-5 Separation of Duties |

**Description**: Same issue as F-002. The Experience Architect has write + shell capabilities that exceed its analysis/design role.

**Remediation**: Same as F-002 — remove `edit_file` and `agent_run_shell_command`.

---

### F-004 — HIGH: Web-Puppy delete_file Access

Subsumed under F-001 but tracked separately for remediation tracking. `delete_file` has zero justification for a research agent.

---

### F-005 — MEDIUM: Helios Lacks Guardrails Documentation

| Field | Value |
|---|---|
| **Severity** | Medium |
| **CVSS v4.0** | 5.5 |
| **Agent** | `helios` (`code_puppy/agents/agent_helios.py`) |
| **Control** | ISO 27001 A.12.1.1 Documented Operating Procedures |

**Description**: Helios intentionally has maximum capabilities including `universal_constructor`. However, there is no threat model, acceptable-use policy, or guardrails artifact documenting the expected boundaries and risk acceptance for this agent.

**Remediation**: Create `docs/security/helios-threat-model.md` documenting: accepted risks, usage guidelines, monitoring recommendations, and the fact that `universal_constructor` execution is equivalent to arbitrary code execution.

---

### F-006 — MEDIUM: Agent-Creator Indirect Privilege Escalation Path

| Field | Value |
|---|---|
| **Severity** | Medium |
| **CVSS v4.0** | 5.0 |
| **Agent** | `agent-creator` (`code_puppy/agents/agent_creator_agent.py`) |
| **Control** | NIST AC-6(1) Authorize Access to Security Functions |

**Description**: `agent-creator` writes agent JSON files that define tool permissions for new agents. It can create an agent with `universal_constructor` + `agent_run_shell_command` + `delete_file` — tools that `agent-creator` itself doesn't have. This is an indirect privilege escalation: create an agent with more power, then switch to it.

**Compensating Control**: Schema validation exists in the `validate_agent_json` method.

**Remediation**: Add a maximum-tool-set policy: new agents created by `agent-creator` should not be able to include `universal_constructor` unless explicitly approved. Consider a "tool ceiling" config.

---

### F-007 — MEDIUM: Scheduler Agent Persistence Mechanism

| Field | Value |
|---|---|
| **Severity** | Medium |
| **CVSS v4.0** | 4.5 |
| **Agent** | `scheduler-agent` (`code_puppy/agents/agent_scheduler.py`) |
| **Control** | MITRE ATT&CK T1053 (Scheduled Task/Job) |

**Description**: `scheduler_create_task` + `scheduler_start_daemon` + `scheduler_run_task` allow creating persistent automated tasks that survive session boundaries. If an attacker achieves prompt injection, they could create a scheduled task that runs malicious prompts periodically.

**Compensating Control**: User must explicitly switch to scheduler agent; `ask_user_question` tool provides human-in-the-loop confirmation.

**Remediation**: Ensure scheduled tasks are logged with full audit trail. Consider requiring user confirmation for each new scheduled task.

---

### F-008 — MEDIUM: No Path-Scoped File Access (Platform Gap)

| Field | Value |
|---|---|
| **Severity** | Medium |
| **CVSS v4.0** | 5.5 |
| **Affected** | All agents with `edit_file` or `delete_file` |
| **Control** | NIST AC-6(3) Network Access to Privileged Commands |

**Description**: The `edit_file` and `delete_file` tools have no path restrictions. Any agent with these tools can write to or delete any file the process owner can access — including `~/.code_puppy/agents/` (agent definitions), `~/.ssh/` (SSH keys), or project CI/CD configs.

**Remediation**: Implement path-scoped file access at the platform level:
- Research agents: `./research/**` only
- Architect agents: `./docs/**` only (if write access is retained)
- Implementation agents: project directory only, excluding `.git/`, `~/.code_puppy/`

---

## Trust Boundary Analysis: invoke_agent / list_agents

**11 agents** have `invoke_agent` + `list_agents` access, enabling agent-to-agent delegation:

| Agent | Can Invoke Others | Can Be Invoked |
|---|---|---|
| code-puppy | ✅ | ✅ |
| code-reviewer | ✅ | ✅ |
| c-reviewer | ✅ | ✅ |
| cpp-reviewer | ✅ | ✅ |
| golang-reviewer | ✅ | ✅ |
| javascript-reviewer | ✅ | ✅ |
| python-reviewer | ✅ | ✅ |
| typescript-reviewer | ✅ | ✅ |
| security-auditor | ✅ | ✅ |
| qa-expert | ✅ | ✅ |
| planning-agent | ✅ | ✅ |
| pack-leader | ✅ | ✅ |
| agent-creator | ✅ | ✅ |
| solutions-architect | ✅ | ✅ |
| experience-architect | ✅ | ✅ |
| python-programmer | ✅ | ✅ |

**Agents WITHOUT invoke_agent** (cannot delegate — good isolation):
- prompt-reviewer, scheduler-agent, helios, qa-kitten, terminal-qa, bloodhound, husky, retriever, shepherd, terrier, watchdog, web-puppy

**Security Observation**: When Agent A invokes Agent B, Agent B operates with **its own tool permissions**, not Agent A's. This means a read-only reviewer could invoke `code-puppy` (which has `edit_file`) and request file modifications. The invoked agent's independent permission set is the trust boundary.

**Recommendation**: Document the invoke chain trust model. Consider whether certain agents should be non-invocable (e.g., helios should not be invocable by other agents to prevent indirect access to `universal_constructor`).

---

## Aggregate Permission Matrix

| Agent | list_files | read_file | grep | edit_file | delete_file | shell | reasoning | invoke | list_agents | Other |
|---|---|---|---|---|---|---|---|---|---|---|
| code-puppy | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ask_user, skills, image |
| code-reviewer | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| c-reviewer | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| cpp-reviewer | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| golang-reviewer | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| javascript-reviewer | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| python-reviewer | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| typescript-reviewer | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| security-auditor | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| qa-expert | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — |
| planning-agent | ✅ | ✅ | ✅ | — | — | — | ✅ | ✅ | ✅ | ask_user, skills |
| pack-leader | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | skills |
| agent-creator | ✅ | ✅ | — | ✅ | — | — | ✅ | ✅ | ✅ | ask_user, (UC) |
| python-programmer | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | skills |
| helios | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | universal_constructor |
| prompt-reviewer | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — |
| scheduler-agent | ✅ | ✅ | ✅ | — | — | — | ✅ | — | — | ask_user, scheduler_* |
| qa-kitten | — | — | — | — | — | — | ✅ | — | — | browser_*, image |
| terminal-qa | — | — | — | — | — | — | ✅ | — | — | terminal_*, image |
| bloodhound | — | ✅ | — | — | — | ✅ | ✅ | — | — | — |
| husky | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | skills |
| retriever | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — |
| shepherd | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — |
| terrier | ✅ | — | — | — | — | ✅ | ✅ | — | — | — |
| watchdog | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — |
| solutions-architect | ✅ | ✅ | ✅ | ❌ | — | ❌ | ✅ | ✅ | ✅ | — |
| experience-architect | ✅ | ✅ | ✅ | ❌ | — | ❌ | ✅ | ✅ | ✅ | — |
| web-puppy | ✅ | ✅ | — | ❌ | ❌ | ❌ | ✅ | — | — | browser_*, ❌UC |

*Legend: ✅ = Justified, ❌ = Over-privileged (finding), — = Absent (correct)*

---

## Remediation Roadmap

### Phase 1 — Immediate Quick Wins (Day 1-3)

| Action | Finding | Owner | Effort |
|---|---|---|---|
| Remove `universal_constructor` from `web-puppy.json` | F-001 | Agent Creator | 1 line |
| Remove `delete_file` from `web-puppy.json` | F-001/F-004 | Agent Creator | 1 line |
| Remove `agent_run_shell_command` from `web-puppy.json` | F-001 | Agent Creator | 1 line |
| Remove `edit_file` from `solutions-architect.json` | F-002 | Agent Creator | 1 line |
| Remove `agent_run_shell_command` from `solutions-architect.json` | F-002 | Agent Creator | 1 line |
| Remove `edit_file` from `experience-architect.json` | F-003 | Agent Creator | 1 line |
| Remove `agent_run_shell_command` from `experience-architect.json` | F-003 | Agent Creator | 1 line |

### Phase 2 — Short-Term Hardening (Week 1-2)

| Action | Finding | Owner | Effort |
|---|---|---|---|
| Create `docs/security/helios-threat-model.md` | F-005 | Security Auditor | Half-day |
| Add tool ceiling policy to agent-creator validation | F-006 | Platform team | 1 day |
| Document scheduler audit trail requirements | F-007 | Platform team | Half-day |
| Document invoke_agent trust model | F-011 | Security Auditor | Half-day |

### Phase 3 — Strategic Platform Guardrails (Month 1-3)

| Action | Finding | Owner | Effort |
|---|---|---|---|
| Implement path-scoped `edit_file` restrictions | F-008 | Platform team | 1-2 weeks |
| Add invocability controls (non-invocable agents) | F-011 | Platform team | 1 week |
| Create agent permission change review process | All | Security + Platform | 1 week |

---

## Positive Controls Observed 🏆

1. **Consistent reviewer pattern**: All 8 reviewer agents have identical, well-scoped tool sets with zero write capabilities. Zero drift across the fleet.
2. **Pack agent isolation**: Husky (implementer) has no `invoke_agent` — it can't spawn other agents. Bloodhound and Terrier have only 3 tools each.
3. **QA-Kitten browser isolation**: No file system or shell access at all. Pure browser tooling.
4. **Planning Agent purity**: No shell, no edit, no delete. Read-only orchestration.
5. **Tool allow-list default deny**: The platform denies tools not explicitly listed. This is the right default.
6. **Agent-creator schema validation**: Validates new agent JSON configs, providing a basic guardrail.

---

## Compliance Posture Summary

| Framework | Control | Status |
|---|---|---|
| OWASP ASVS 1.4.1 | Least privilege access controls | ⚠️ 4 agents non-compliant |
| OWASP ASVS 1.4.2 | Separation of privilege | ❌ Architect agents violate SoD |
| NIST AC-6 | Least Privilege | ⚠️ Partial — 86% compliant (25/29 agents) |
| NIST AC-5 | Separation of Duties | ❌ Architect agents have implementer tools |
| ISO 27001 A.9.4.1 | Information access restriction | ⚠️ No path-scoped file access |
| ISO 27001 A.12.1.1 | Documented procedures | ❌ Helios missing threat model |
| CIS Control 6 | Access Control Management | ⚠️ Partial — agent-creator escalation path |

---

## Verification & Retest Requirements

After remediation:
1. Re-run `list_agents` and verify tool lists for all 3 JSON agents
2. Confirm web-puppy can still save research files with retained `edit_file` (scoped) or via delegation
3. Confirm Solutions Architect can produce ADRs via `invoke_agent` → Husky delegation
4. Run integration tests to verify no broken workflows
5. Schedule 90-day re-audit cycle for agent permissions

---

*Audit complete. 🐾 Stay safe, stay least-privilege, and remember: a good puppy only chews what it's supposed to.*
