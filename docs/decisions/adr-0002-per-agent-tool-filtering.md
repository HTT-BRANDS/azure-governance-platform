---
status: accepted
date: 2026-03-06
decision-makers: Security Auditor, Solutions Architect, Pack Leader
consulted: Code Reviewer, Agent Creator, Planning Agent
informed: All Code Puppy agents, development team
---

# Implement per-agent tool filtering

## Context and Problem Statement

With 29 specialized agents in the Code Puppy multi-agent system (see ADR-0001), each agent needs access to different tools to perform their role. For example, Husky needs `cp_edit_file` to modify code, while QA Kitten needs browser automation tools for web testing. A critical security decision is whether to grant all agents access to all tools (simpler) or implement per-agent allow-lists that enforce least privilege (more secure). The key question: How do we balance convenience with security when managing tool access for 29 agents?

## Decision Drivers

- **Security (Least Privilege)**: Each agent should only have access to tools necessary for their role
- **Blast Radius**: Compromised agent should have minimal impact on system
- **Accountability**: Clear mapping of which agents can perform which actions
- **Auditability**: Ability to review and justify every agent's tool access
- **Maintainability**: Tool access should be easy to review and update
- **Performance**: Tool filtering should not significantly impact agent response time
- **Regulatory Compliance**: Azure governance platform must demonstrate security controls
- **Defense in Depth**: Multiple security layers to protect the codebase

## Considered Options

1. **All agents get all tools** - Every agent has access to the complete toolset
2. **Per-agent allow-lists (explicit)** - Each agent JSON defines exactly which tools they can use
3. **Role-based tool groups** - Tools organized into groups (read-only, write, execute, etc.), agents assigned to groups
4. **Runtime filtering** - All agents have all tools, but runtime checks prevent usage based on agent identity

## Decision Outcome

Chosen option: **"Per-agent allow-lists (explicit)"**, because it provides the strongest security guarantees with clear auditability and maintainability.

### Implementation Details

Each agent's JSON file (`~/.code_puppy/agents/{agent-name}.json`) includes a `tool_filter` section:

```json
{
  "name": "husky",
  "description": "Main coding executor",
  "tool_filter": {
    "allowed_tools": [
      "cp_list_files",
      "cp_read_file",
      "cp_grep",
      "cp_edit_file",
      "cp_delete_file",
      "cp_agent_run_shell_command"
    ]
  },
  ...
}
```

**Key Principles:**
1. **Deny by default** - If a tool isn't in the allow-list, agent cannot use it
2. **Explicit over implicit** - Every tool must be explicitly listed (no wildcards)
3. **Documented justification** - Tool audit document explains why each agent needs each tool
4. **Regular review** - Tool access reviewed during security audits (quarterly)

### Examples by Agent Type

**Read-Only Agents** (QA Expert, Planning Agent):
- Allow: `cp_list_files`, `cp_read_file`, `cp_grep`
- Deny: `cp_edit_file`, `cp_delete_file`
- Rationale: These agents analyze and plan but don't modify code

**Code Executors** (Husky, Python Programmer):
- Allow: All file operations + `cp_agent_run_shell_command`
- Deny: `invoke_agent` (orchestration reserved for Pack Leader)
- Rationale: Need full file access for implementation

**Specialized Writers** (Agent Creator):
- Allow: File operations but restricted to `~/.code_puppy/agents/` directory
- Deny: Modification of application code
- Rationale: Self-modification limited to agent definitions only

**Orchestrators** (Pack Leader):
- Allow: `invoke_agent`, read-only file access
- Deny: Direct file modification (must delegate to Husky)
- Rationale: Coordination role, not implementation role

### Consequences

- **Good**, because compromised agent has minimal blast radius (can't access unauthorized tools)
- **Good**, because clear audit trail - tool access documented and reviewable
- **Good**, because enforces separation of concerns (readers vs writers vs executors)
- **Good**, because meets principle of least privilege (security best practice)
- **Good**, because agents can't accidentally use wrong tools (prevented at runtime)
- **Good**, because regulatory compliance - demonstrable security controls
- **Bad**, because requires initial setup effort (defining allow-lists for 29 agents)
- **Bad**, because tool changes require updating multiple agent JSONs
- **Neutral**, because performance impact is negligible (filter check is fast)

### Confirmation

This decision is validated by:

1. Tool audit document exists: `docs/security/agent-tool-audit.md`
2. Every agent JSON file has `tool_filter.allowed_tools` defined
3. Runtime enforcement: Agent attempting to use disallowed tool receives error
4. Security Auditor review confirms no excessive permissions
5. Quarterly audit process documents tool access justification

## STRIDE Security Analysis

| Threat Category | Risk Level | Mitigation |
|-----------------|-----------|------------|
| **Spoofing** | Low | Agent identity verified before tool access granted; agent ID logged with every tool invocation |
| **Tampering** | Low (reduced from High) | Per-agent filtering prevents unauthorized file modifications; only agents with `cp_edit_file` permission can modify code |
| **Repudiation** | Low | All tool invocations logged with agent ID, timestamp, tool name, and parameters; comprehensive audit trail |
| **Information Disclosure** | Low (reduced from Medium) | Read access limited to agents that need it; prevents casual browsing of sensitive files |
| **Denial of Service** | Low | Shell command access limited to specific agents; prevents accidental or malicious resource exhaustion |
| **Elevation of Privilege** | Low (reduced from High) | Agents cannot grant themselves new tools; tool list is immutable without Agent Creator involvement |

**Overall Security Posture:** Per-agent tool filtering is a **critical security control** that reduces multiple threat categories:

1. **Tampering**: Without filtering, any compromised agent could modify any file. With filtering, damage is contained.
2. **Elevation of Privilege**: Agents can't escalate their own permissions - tool list is defined in JSON, not runtime.
3. **Information Disclosure**: Read-only agents can't accidentally execute or modify files.

**Risk Reduction:** This control moves tampering and elevation of privilege risks from **High → Low**, a two-level improvement.

## Pros and Cons of the Options

### All agents get all tools (rejected)

*Every agent has access to complete toolset*

- Good, because simplest to implement (no filtering logic)
- Good, because no maintenance overhead for tool lists
- Good, because agents can adapt to unexpected needs
- Bad, because **massive security risk** - any compromised agent can do anything
- Bad, because violates least privilege principle
- Bad, because unclear accountability (every agent can modify files)
- Bad, because no blast radius containment
- Bad, because difficult to audit ("everyone can do everything")
- Bad, because agents might use wrong tools accidentally
- **Critical flaw**: Single compromised agent (e.g., via prompt injection) could delete entire codebase

### Per-agent allow-lists (explicit) (accepted)

*Current decision - see above for full analysis*

- Good, because strongest security (least privilege enforced)
- Good, because clear accountability and audit trail
- Good, because blast radius containment
- Good, because prevents accidental misuse
- Good, because regulatory compliance friendly
- Bad, because initial setup effort
- Bad, because maintenance overhead when tools change
- Neutral, because performance impact is negligible

### Role-based tool groups (rejected)

*Tools organized into groups, agents assigned to groups*

- Good, because easier maintenance than per-agent lists (update group, all agents inherit)
- Good, because some security benefit (better than "all tools")
- Neutral, because moderate setup complexity
- Bad, because less granular than per-agent (e.g., "Writers" group might be too broad)
- Bad, because agents might get tools they don't need (group has more than agent needs)
- Bad, because role definitions become complex ("Writer" vs "Privileged Writer" vs "Limited Writer"?)
- Bad, because less clear accountability ("some agent in the Writers group did this")

### Runtime filtering (rejected)

*All agents have all tools, runtime checks prevent usage*

- Good, because flexible (can change filtering without updating agents)
- Neutral, because security depends on correct runtime implementation
- Bad, because tools still "visible" to agent (temptation to bypass)
- Bad, because runtime checks can be bypassed if implementation has bugs
- Bad, because no clear declaration of agent capabilities (must read runtime code)
- Bad, because auditability is harder (filtering logic scattered across codebase)
- Bad, because "allow all, filter later" is opposite of secure design

## More Information

**Related Requirements:**
- REQ-103: Audit all agent tool permissions
- REQ-604: Self-modification protections (Agent Creator only)
- REQ-601: STRIDE analysis for all agents
- ADR-0001: Multi-agent architecture (establishes 29 agents)

**Related Documents:**
- [Agent Tool Audit](../security/agent-tool-audit.md) - Comprehensive audit of all 29 agents' tool access
- [TRACEABILITY_MATRIX.md](../../TRACEABILITY_MATRIX.md) - Maps security requirements to agents
- [SECURITY_IMPLEMENTATION.md](../../SECURITY_IMPLEMENTATION.md) - Overall security architecture

**Tool Categories:**

| Category | Tools | Risk Level |
|----------|-------|------------|
| **Read** | `cp_list_files`, `cp_read_file`, `cp_grep` | Low |
| **Write** | `cp_edit_file`, `cp_delete_file` | High |
| **Execute** | `cp_agent_run_shell_command` | Critical |
| **Orchestrate** | `invoke_agent`, `cp_activate_skill` | Medium |
| **Search** | `cp_list_or_search_skills` | Low |

**Audit Process:**

1. **Quarterly Review** - Security Auditor reviews all agent tool lists
2. **New Agent Review** - Agent Creator submits tool list for review before agent activation
3. **Tool Change Review** - Any tool addition requires Security Auditor sign-off
4. **Incident Response** - If agent is compromised, tool list immediately reviewed and potentially reduced

**Validation:**
- ✅ All 29 agents have `tool_filter.allowed_tools` defined
- ✅ Tool audit document completed (Jan 2026, reviewed March 2026)
- ✅ Runtime enforcement tested and confirmed
- ✅ No agent has excessive permissions (per Security Auditor review)

**Review History:**
- 2026-03-06: Initial decision documented (retroactive ADR)
- Reviewed by: Security Auditor 🛡️, Code Reviewer 🛡️, Solutions Architect 🏛️
- Signed off by: Pack Leader 🐺

**When to Revisit:**
- If new tool types are added to Code Puppy
- If agent roles significantly change
- After any security incident involving agent tool usage
- During annual security architecture review

---

**ADR Status:** Accepted  
**Implementation Status:** ✅ Complete (agent-tool-audit.md documents all 29 agents)  
**Last Updated:** March 6, 2026
