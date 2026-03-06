---
status: accepted
date: 2026-03-06
decision-makers: Tyler Granlund (Pack Leader), Planning Agent, Solutions Architect
consulted: Security Auditor, Experience Architect, Web Puppy (research)
informed: All Code Puppy agents, development team
---

# Use multi-agent architecture for Code Puppy

## Context and Problem Statement

The Azure Governance Platform requires an AI-powered development assistant to help with architecture decisions, code implementation, testing, security audits, and UX design. A key decision was whether to build this as a single monolithic agent or as a specialized multi-agent system. Given the diverse skill sets required (backend development, frontend design, security analysis, testing, documentation), how should we structure the AI assistant to maximize effectiveness while maintaining code quality and security?

## Decision Drivers

- **Specialization**: Different tasks require different expertise (e.g., Python development vs accessibility testing)
- **Parallel work**: Need ability for multiple agents to work simultaneously on different issues
- **Clear accountability**: Each task should have a clearly responsible agent
- **Security**: Need to limit tool access per agent (least privilege principle)
- **Code quality**: Specialized reviewers for different domains (Python, security, UX)
- **Scalability**: System should scale to handle complex projects with many simultaneous tasks
- **Traceability**: Need clear audit trail of which agent made which decisions
- **Context management**: Single agent would have excessive context switching between vastly different tasks

## Considered Options

1. **Monolithic agent** - Single general-purpose agent handles all tasks
2. **Multi-agent system (29 specialized agents)** - Each agent has specific expertise and limited tool access
3. **Hybrid approach** - Small number of "specialist" agents (5-10) with broader capabilities
4. **Tool-based specialization** - Single agent with different "modes" activated by tooling

## Decision Outcome

Chosen option: **"Multi-agent system (29 specialized agents)"**, because it provides the best balance of specialization, security, accountability, and parallel work capabilities.

### Agent Roster

The system includes 29 specialized agents organized by domain:

**Planning & Coordination** (3 agents):
- Pack Leader 🐺 - Strategic oversight, prioritization, final approval
- Planning Agent 📋 - Traceability, requirements decomposition, roadmap management
- Bloodhound 🐕‍🦸 - Issue tracking (bd), backlog management

**Architecture & Design** (2 agents):
- Solutions Architect 🏛️ - Backend architecture, ADRs, technical decisions
- Experience Architect 🎨 - UX/UI design, accessibility, privacy patterns

**Development** (5 agents):
- Husky 🐺 - Main coding executor (pulls the sled!)
- Python Programmer 🐍 - Python-specific implementation
- Terrier 🐕 - Infrastructure, DevOps, deployment
- Agent Creator 🏭️ - Creates/modifies agent JSON files
- Web Puppy 🕵️‍♂️ - Research, web scraping, evidence gathering

**Quality Assurance** (6 agents):
- QA Expert 🐾 - Test strategy, 13-step methodology
- Watchdog 🐕‍🦺 - Automated testing, CI/CD gates
- QA Kitten 🐱 - Manual web UI testing
- Terminal QA 🖥️ - CLI and smoke testing
- Shepherd 🐕 - Code review coordinator, PR workflow
- Code Reviewer 🛡️ - Security-focused code review

**Security & Compliance** (2 agents):
- Security Auditor 🛡️ - STRIDE analysis, threat modeling
- Prompt Reviewer 📝 - Reviews agent prompts for security issues

**Review Specialists** (2 agents):
- Python Reviewer 🐍 - Python code quality, PEP compliance
- Documentation Reviewer 📖 - Documentation quality

### Consequences

- **Good**, because each agent can focus on their domain expertise without context switching
- **Good**, because multiple agents can work in parallel on different worktrees/issues
- **Good**, because tool access is limited per agent (security via least privilege)
- **Good**, because accountability is clear (TRACEABILITY_MATRIX.md tracks agent ownership)
- **Good**, because specialized reviewers catch domain-specific issues (Python reviewer for Python, Security Auditor for STRIDE)
- **Good**, because prompts are shorter and more focused (no "jack of all trades" mega-prompt)
- **Bad**, because coordination overhead requires Pack Leader and Planning Agent orchestration
- **Bad**, because agents must use `invoke_agent` for cross-domain collaboration (communication overhead)
- **Neutral**, because 29 agents seems like a lot, but each has a clear, specific role

### Confirmation

This decision is validated by:

1. All 29 agent JSON files exist in `~/.code_puppy/agents/`
2. Agent tool audit (docs/security/agent-tool-audit.md) confirms each agent has minimal necessary tools
3. TRACEABILITY_MATRIX.md maps every requirement to a specific agent
4. Parallel worktree workflow allows multiple agents to work simultaneously

## STRIDE Security Analysis

| Threat Category | Risk Level | Mitigation |
|-----------------|-----------|------------|
| **Spoofing** | Low | Each agent has unique identifier (e.g., husky-51d43f); all actions logged with agent ID |
| **Tampering** | Medium | Per-agent tool filtering prevents unauthorized file modifications; only Agent Creator can modify agents dir |
| **Repudiation** | Low | All agent actions logged to bd issues with timestamps; git commits show agent authorship |
| **Information Disclosure** | Medium | Agents only access files/tools necessary for their role; no shared secrets between agents |
| **Denial of Service** | Low | Agent resource limits prevent single agent from monopolizing system; timeout protections |
| **Elevation of Privilege** | Medium | Tool allow-lists enforce least privilege; agents cannot grant themselves new capabilities |

**Overall Security Posture:** Multi-agent architecture significantly improves security posture by:
1. **Reducing blast radius** - Compromised agent only has access to their limited toolset
2. **Clear audit trail** - Every action traceable to specific agent
3. **Least privilege by default** - Each agent only gets tools they need
4. **Defense in depth** - Multiple review agents create security checkpoints

Compared to a monolithic agent with all tools, this architecture reduces risk from High to Medium for tampering and elevation of privilege.

## Pros and Cons of the Options

### Monolithic agent (rejected)

*Single general-purpose agent handles all tasks*

- Good, because simpler coordination (no inter-agent communication)
- Good, because single prompt, easier to maintain initially
- Good, because no context handoff between agents
- Bad, because **massive security risk** - single compromised agent has access to all tools
- Bad, because context window pollution (must know Python + UX + security + testing simultaneously)
- Bad, because no specialization - "jack of all trades, master of none"
- Bad, because no parallel work - single agent can only do one thing at a time
- Bad, because unclear accountability - who reviews the reviewer?
- Bad, because prompt becomes unwieldy (100+ KB of "you are a Python expert AND a security expert AND...")

### Multi-agent system (29 specialized agents) (accepted)

*Current decision - see above for full analysis*

- Good, because specialization improves quality
- Good, because parallel work scales better
- Good, because security via least privilege
- Good, because clear accountability and traceability
- Good, because focused prompts are easier to maintain
- Bad, because coordination overhead
- Bad, because requires orchestration layer (Pack Leader + Planning Agent)
- Neutral, because agent count seems high but each has distinct role

### Hybrid approach (5-10 specialist agents) (rejected)

*Fewer agents with broader responsibilities*

- Good, because simpler coordination than 29 agents
- Good, because some specialization benefits
- Neutral, because moderate parallel work capability
- Bad, because still requires broad tool access per agent (higher security risk)
- Bad, because agents still have multiple responsibilities (e.g., "Backend Agent" does Python + infrastructure + security)
- Bad, because less clear accountability (who owns what?)
- Bad, because less effective specialization

### Tool-based specialization (single agent with modes) (rejected)

*Single agent switches "modes" based on task type*

- Good, because single prompt to maintain
- Good, because no inter-agent communication
- Neutral, because could use tooling to enforce access control per mode
- Bad, because **no parallel work** - single agent can't work on multiple tasks simultaneously
- Bad, because mode switching adds complexity and potential errors
- Bad, because all tools must be accessible to single agent (security risk if mode system fails)
- Bad, because accountability is unclear (agent in "Python mode" vs "Security mode"?)

## More Information

**Related Requirements:**
- REQ-101: Create Solutions Architect JSON agent
- REQ-102: Create Experience Architect JSON agent  
- REQ-103: Audit all agent tool permissions
- REQ-601: STRIDE analysis for all agents
- REQ-604: Self-modification protections

**Related Documents:**
- [Agent Instructions](../../AGENTS.md)
- [Agent Tool Audit](../security/agent-tool-audit.md)
- [Traceability Matrix](../../TRACEABILITY_MATRIX.md)
- [Research: Multi-Agent Architecture](../../research/multi-agent-architecture/)

**Validation:**
- ✅ All 29 agents created and functional
- ✅ Agent tool audit completed (docs/security/agent-tool-audit.md)
- ✅ TRACEABILITY_MATRIX.md maps all requirements to agents
- ✅ Parallel worktree workflow tested and documented

**Review History:**
- 2026-03-06: Initial decision documented (retroactive ADR)
- Reviewed by: Security Auditor 🛡️, Solutions Architect 🏛️
- Signed off by: Pack Leader 🐺, Planning Agent 📋

---

**ADR Status:** Accepted  
**Implementation Status:** ✅ Complete  
**Last Updated:** March 6, 2026
