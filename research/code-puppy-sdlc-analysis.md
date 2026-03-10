# Code Puppy and Agile SDLC: complete technical and methodological analysis

**Code Puppy is an open-source, MIT-licensed CLI AI coding agent built on Pydantic AI that positions itself as a privacy-first, lightweight alternative to Windsurf and Cursor.** Created by Michael Pfaffenberger in May 2025, it offers 15+ specialized agents, support for 65+ LLM providers and over 1,000 models, a dual-mode agent system (Python and JSON), MCP integration, and verified zero telemetry — enforced through automated MITM integration tests rather than policy promises alone. The accompanying Agile SDLC presentation by Tyler Granlund provides a comprehensive framework for streamlining e-commerce development through structured communication, a 13-step testing methodology, traceability matrices, and dual-scale project management. This report exhaustively documents both systems.

---

## Code Puppy's architecture and technical foundation

Code Puppy (**324+ stars, 80+ forks, 1,264+ commits, 170k+ PyPI downloads**) is built on the **Pydantic AI** framework and requires Python 3.11+. The project uses modern Python packaging exclusively — `pyproject.toml` with UV as the recommended package manager and no legacy `setup.py`. The mascot is named "Snoopers" 🐕.

### Repository structure

```
code_puppy/                         (repository root)
├── .github/workflows/              CI/CD pipeline (GitHub Actions)
├── code_puppy/                     Main Python package
│   ├── __init__.py                 Package initialization (version info)
│   ├── __main__.py                 Module entry point
│   ├── cli.py                      CLI entry point and slash command parsing
│   ├── agents/                     Agent implementations
│   │   ├── base_agent.py           BaseAgent abstract class
│   │   ├── json_agent.py           JSONAgent class for JSON-defined agents
│   │   ├── agent_manager.py        Unified registry, discovery, switching
│   │   ├── code_puppy_agent.py     Default "code-puppy" agent
│   │   ├── agent_creator.py        Agent creation wizard
│   │   └── [15+ other agents]      Planning, security, QA, etc.
│   ├── tools/                      Tool implementations
│   ├── mcp/                        MCP server integration
│   ├── models/                     Model/provider configurations
│   └── [prompts, config, etc.]     Additional modules
├── docs/                           Documentation (includes CEREBRAS.md)
├── tests/                          Test suite (including MITM telemetry tests)
├── .env.example                    Example environment variables
├── .gitattributes
├── .gitignore
├── LICENSE                         MIT License
├── README.md                       Comprehensive documentation (~2000+ lines)
├── code_puppy.gif                  Demo animation
├── code_puppy.png                  Logo
├── lefthook.yml                    Git hooks (pre-commit) configuration
├── pyproject.toml                  Build config, dependencies (UV/hatchling)
└── uv.lock                         UV lockfile for reproducible builds
```

### CLI startup and runtime flow

The CLI entry point is `code_puppy.cli:main`, invoked via `code-puppy` or `uvx code-puppy`. The startup flow proceeds through model configuration resolution (environment variables → config files → CLI `/set` commands), agent discovery (scanning both `code_puppy/agents/` for Python agents and `~/.code_puppy/agents/` for JSON agents), optional DBOS durable execution wrapping, and MCP server initialization from `~/.code_puppy/mcp_servers.json`. The `-i` flag launches an interactive setup wizard for first-time configuration.

The interactive REPL processes user input and slash commands. **Natural language input** routes to the active agent's LLM with its system prompt and available tools. **Slash commands** are handled directly by the CLI layer. Custom slash commands from `.claude/commands/`, `.github/prompts/`, or `.agents/commands/` directories inject markdown file content as prompts — the filename becomes the command name.

---

## The dual-mode agent system in depth

Code Puppy's most distinctive architectural feature is its **dual-mode agent system** — a unified registry serving both built-in Python agents and user-created JSON agents through a common `BaseAgent` interface.

### BaseAgent abstract class

Every agent implements this interface regardless of whether it's defined in Python or JSON:

```python
from .base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    @property
    def name(self) -> str:              # Unique kebab-case identifier
        return "my-agent"

    @property
    def display_name(self) -> str:      # Pretty name with emoji
        return "My Custom Agent ✨"

    @property
    def description(self) -> str:       # Brief purpose description
        return "A custom agent for specialized tasks"

    def get_system_prompt(self) -> str:  # LLM system instructions
        return "Your custom system prompt here..."

    def get_available_tools(self) -> list[str]:  # Permitted tool names
        return ["list_files", "read_file", "grep", "edit_file",
                "delete_file", "agent_run_shell_command",
                "agent_share_your_reasoning"]
```

The `JSONAgent` class (`code_puppy/agents/json_agent.py`) inherits from `BaseAgent`, loading configuration from JSON files with schema validation, cross-platform directory support, and built-in error handling.

### JSON agent schema

```json
{
    "name": "agent-name",              // REQUIRED: kebab-case unique identifier
    "display_name": "Agent Name 🤖",   // OPTIONAL: defaults to title-cased name + 🤖
    "description": "What this agent does", // REQUIRED
    "system_prompt": "Instructions...",    // REQUIRED: string or array of strings
    "tools": ["tool1", "tool2"],          // REQUIRED: tool name array
    "user_prompt": "How can I help?",     // OPTIONAL: custom greeting
    "tools_config": { "timeout": 60 }     // OPTIONAL: tool configuration
}
```

System prompts accept arrays (joined with newlines) for readability. JSON agents are stored in `~/.code_puppy/agents/` as `*-agent.json` files and auto-discovered on startup.

### All 15+ built-in agents

| Agent | Slug | Tool Access | Purpose |
|---|---|---|---|
| 🐶 Code Puppy | `code-puppy` | **Full** (all 7 tools) | Default agent — full-stack code generation with sassy, playful persona enforcing YAGNI/SRP/DRY and max 600-line files |
| 📋 Planning Agent | `planning-agent` | Multi-agent orchestration | **Multi-agent orchestrator** that plans AND executes by delegating to specialist agents |
| 🛡️ Code Reviewer | `code-reviewer` | Read-only (`list_files`, `read_file`, `grep`, `agent_share_your_reasoning`) | Holistic code review for bugs, vulnerabilities, and design debt |
| 🔐 Security Auditor | `security-auditor` | Security-focused subset | Risk-based security auditing with compliance focus |
| 🐾 QA Kitten | `qa-kitten` | Browser automation (Playwright) | Automated browser testing and QA |
| 🎨 Agent Creator | `agent-creator` | File operations + reasoning | Interactive wizard for building custom JSON agents with schema validation |
| ⚙️ DevOps Helper | `devops-helper` | `list_files`, `read_file`, `edit_file`, `agent_run_shell_command`, `agent_share_your_reasoning` | Docker, CI/CD, and deployment tasks |
| 🐍 Python Tutor | `python-tutor` | `read_file`, `edit_file`, `agent_share_your_reasoning` | Python learning assistant |

Additional agents bring the total above 15, covering domains like architecture, documentation writing, and specialized language support.

### Agent manager architecture

The `agent_manager.py` module provides a **unified registry** handling: automatic discovery of Python agents (class scanning in `code_puppy/agents/`) and JSON agents (glob scanning `~/.code_puppy/agents/*-agent.json`); seamless switching via `/agent <name>`; per-agent model pinning via `/pin_model`; automatic DBOS wrapping when durable execution is enabled; configuration persistence across sessions; and performance caching.

---

## The complete tool system and permission model

### Seven core tools

| Tool | Risk Level | Description |
|---|---|---|
| `list_files` | Low | Directory and file listing |
| `read_file` | Medium | Read arbitrary file contents accessible to the process |
| `grep` | Low | Pattern search across files |
| `edit_file` | **High** | Create and modify files — no visible path restrictions |
| `delete_file` | **High** | Delete files accessible to the process |
| `agent_run_shell_command` | **Critical** | Arbitrary shell command execution with user's full permissions |
| `agent_share_your_reasoning` | Low | Expose agent reasoning/thinking to the user |

Browser tools (Playwright-based) are additionally available to the `qa-kitten` agent for automated web testing.

### Per-agent tool filtering

Each agent explicitly declares which tools it can access. This creates a **least-privilege pattern** where read-only agents like `code-reviewer` cannot execute shell commands or modify files. Common patterns include read-only (`list_files`, `read_file`, `grep`), file-editing (`list_files`, `read_file`, `edit_file`), and full access (all tools). Tool configuration accepts optional `tools_config` with parameters like `timeout` and `max_retries`.

### YOLO_MODE security toggle

Setting `YOLO_MODE=true` bypasses safety confirmation prompts for shell commands. When disabled (the default), shell commands require explicit user confirmation before execution. This is the primary guardrail against LLM-directed arbitrary command execution.

---

## All configuration options and environment variables

### Provider API keys

| Variable | Provider |
|---|---|
| `OPENAI_API_KEY` | OpenAI (GPT-5, GPT-5.2-Codex) |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) |
| `GEMINI_API_KEY` | Google Gemini |
| `CEREBRAS_API_KEY` | Cerebras (GLM 4.7, Qwen) |
| `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` | Azure OpenAI |
| `XAI_API_KEY` | xAI (Grok) |
| `GROQ_API_KEY` | Groq |
| `MISTRAL_API_KEY` | Mistral |
| `TOGETHER_API_KEY` | Together AI |
| `PERPLEXITY_API_KEY` | Perplexity |
| `DEEPINFRA_API_KEY` | DeepInfra |
| `COHERE_API_KEY` | Cohere |
| `AIHUBMIX_API_KEY` | AIHubMix |

Plus **39+ additional providers** with OpenAI-compatible APIs via the models.dev integration.

### DBOS durable execution variables

| Variable | Default | Description |
|---|---|---|
| `DBOS_CONDUCTOR_KEY` | None | Connects to DBOS Management Console (register app `dbos-code-puppy`) |
| `DBOS_LOG_LEVEL` | ERROR | CRITICAL/ERROR/WARNING/INFO/DEBUG |
| `DBOS_SYSTEM_DATABASE_URL` | `dbos_store.sqlite` | SQLite or PostgreSQL (e.g., `postgresql://postgres:dbos@localhost:5432/postgres`) | <!-- pragma: allowlist secret -->
| `DBOS_APP_VERSION` | version + Unix timestamp ms | App version for workflow recovery |

### Runtime configuration

| Variable | Purpose |
|---|---|
| `MODEL_NAME` | Default model (e.g., `gpt-5`) |
| `YOLO_MODE` | `true` to bypass shell command confirmation |
| `UV_MANAGED_PYTHON` | `1` recommended for UV installations |

### Configuration file locations

| Path | Purpose |
|---|---|
| `~/.code_puppy/extra_models.json` | Custom model definitions, round-robin configs, custom endpoints |
| `~/.code_puppy/agents/*-agent.json` | User-created JSON agent definitions |
| `~/.code_puppy/mcp_servers.json` | MCP server configurations |
| `AGENT.md` (project root) | Coding standards via agent.md standard |
| `.claude/commands/*.md` | Custom slash commands (Claude Code compatible) |
| `.github/prompts/*.md` | Custom slash commands (GitHub Copilot compatible) |
| `.agents/commands/*.md` | Custom slash commands |

### Configuration hierarchy

Environment variables are lowest priority, `~/.code_puppy/` config files override them, and CLI `/set` commands have highest priority and persist across sessions.

---

## Model provider handling and round-robin distribution

The `/add_model` command opens an interactive TUI browsing **65+ providers** and **1,000+ models** via the models.dev API, with offline fallback to a bundled database. Providers with OpenAI-compatible APIs are automatically configured with correct endpoints. Amazon Bedrock and Google Vertex are flagged as unsupported due to special authentication requirements. Models without tool-calling support display warnings since they cannot use Code Puppy's file/shell tools.

### Custom model configuration with round-robin

The `~/.code_puppy/extra_models.json` file supports custom endpoints, environment variable interpolation (`$CEREBRAS_API_KEY1`), context length settings, and **round-robin model distribution** for rate limit management:

```json
{
    "qwen1": {
        "type": "cerebras", "name": "qwen-3-coder-480b",
        "custom_endpoint": { "url": "https://api.cerebras.ai/v1", "api_key": "$CEREBRAS_API_KEY1" },
        "context_length": 131072
    },
    "cerebras_round_robin": {
        "type": "round_robin",
        "models": ["qwen1", "qwen2", "qwen3"],
        "rotate_every": 5
    }
}
```

The `rotate_every` parameter controls requests per model before cycling, automatically distributing load across multiple API keys to overcome rate limits.

---

## MCP integration and slash commands

### MCP server management

Code Puppy acts as an **MCP client** connecting to external MCP servers for additional tool capabilities. Configuration lives in `~/.code_puppy/mcp_servers.json`:

```json
{
    "mcp_servers": {
        "context7": { "url": "https://mcp.context7.com/sse" }
    }
}
```

The `/mcp` command provides full lifecycle management: `list` (show configured servers), `start` (launch server), `stop` (terminate server), and `status` (check health). MCP servers use SSE transport and support simultaneous connections. Context7 integration enables deep documentation lookups and code search. MCP calls are checkpointed by DBOS when durable execution is active.

### Complete slash command reference

| Command | Description |
|---|---|
| `/help` | Show help and available commands |
| `/agent <name>` | Switch to a different agent |
| `/model <name>` | Switch AI model |
| `/tools` | Show available tools for current agent |
| `/mcp list\|start\|stop\|status` | Manage MCP servers |
| `/add_model` | Browse/add models via models.dev TUI |
| `/set <key> <value>` | Persistent configuration (e.g., `/set enable_dbos false`) |
| `/pin_model` | Pin a model to a specific sub-agent |
| `/claude-code-auth` | Enable Claude Code model authentication |
| `/truncate <N>` | Keep system message + N most recent messages, remove older history |

The `/truncate` command protects the system prompt (first message) while trimming conversation history for context window management.

---

## Extension points and customization mechanisms

Code Puppy offers **six distinct extension pathways**:

1. **JSON agents** — No code required. Create `*-agent.json` in `~/.code_puppy/agents/` with name, description, system_prompt, and tools. Auto-discovered on startup.
2. **Python agents** — Full power. Subclass `BaseAgent` in `code_puppy/agents/`, implement required properties/methods. Auto-discovered via class scanning.
3. **Agent Creator wizard** — Guided interactive flow via `/agent agent-creator` that validates schemas and writes JSON files.
4. **Custom slash commands** — Markdown files in `.claude/commands/`, `.github/prompts/`, or `.agents/commands/`. Filename becomes command name, content runs as prompt.
5. **MCP servers** — External tool integration via JSON configuration. No code changes needed.
6. **AGENT.md files** — Define project-level coding standards injected into agent context, compatible with the agent.md standard.

Future planned extensions include hot reloading, an agent marketplace, visual editor, enhanced validation, and community-contributed agent templates.

---

## Security considerations and risk assessment

### Critical risks

**Unrestricted shell execution** is the primary attack surface. The `agent_run_shell_command` tool provides full shell access with the user's permissions. The LLM decides what commands to run, creating prompt injection exposure. The only guardrail is YOLO_MODE — when disabled (default), commands require user confirmation. When enabled, commands execute without approval.

**Unrestricted file operations** allow `edit_file` and `delete_file` to operate on any path accessible to the process. No documented path sandboxing, allowlisting, or confirmation prompts exist for file operations specifically.

### High risks

**Self-modification is possible.** The agent can modify its own configuration files at `~/.code_puppy/agents/`, rewrite JSON agent definitions, or create new agents. The `agent-creator` agent is specifically designed to write to this directory.

**Custom command injection** presents a risk if command directories (`.claude/commands/`, `.github/prompts/`, `.agents/commands/`) are writable by untrusted parties, since markdown files are loaded and executed as prompts.

**MCP server integration** expands the attack surface with third-party tool execution from potentially untrusted servers.

### Mitigations

Per-agent tool filtering enables least-privilege patterns (read-only agents cannot execute shell commands). The privacy-by-design architecture includes zero telemetry verified by automated MITM integration tests. DBOS durable execution provides an audit trail of all tool calls, LLM responses, and MCP interactions. Complete air-gapped operation is possible via local VLLM/SGLang/Llama.cpp servers. API keys use environment variable interpolation, never hardcoded in configuration files. The project has no corporate backing or investor pressure to compromise on privacy.

---

## The code-puppy.dev documentation portal

The documentation site is a comprehensive multi-page static site with this navigation structure:

- **Home**: Introduction, "Vibe Code Cheaply" guide for ~$31/month access to premium models
- **Getting Started**: Installation, Quick Start, Configuration
- **Commands**: All Commands, Core Commands, Config Commands, Session Commands
- **Agents**: All Agents, Custom Agents, Agent Creator
- **Tools**: All Tools, File Operations, Browser Tools
- **Integrations**: MCP Integration, Plugins, Model Providers
- **Advanced**: Architecture, Session Management, Advanced Features

The site emphasizes Code Puppy's philosophy: **DRY**, **YAGNI**, **SOLID**, **Zen of Python**, and a hard **600-line file limit**. The tagline positions it as "Your loyal AI code agent" that makes "IDEs look outdated."

### KittyLog changelog

The changelog at `https://kittylog.app/c/mpfaffenberger/code_puppy` serves as the project's release notes platform. KittyLog is a dedicated changelog hosting service (distinct from unrelated projects sharing similar names). The site is not indexed by search engines and appears to be a JavaScript SPA, making external access difficult. The README links to it as the canonical changelog location.

---

## Tyler Granlund's Agile SDLC methodology for e-commerce

The second major component of this analysis is the Adobe Experience Makers "Learn From Your Peers" presentation by **Tyler Granlund** (Adobe Commerce Champion, Outdoor Cap Company), delivered February 22, 2024. The presentation establishes a structured framework for e-commerce development around three pillars: **communication**, **requirements**, and **testing**.

### Why Agile SDLC matters for e-commerce

Granlund frames Agile SDLC as essential for two reasons: **scalability and performance** (architecture that caters to growing demands and increased user activity) and **market adaptability** (rapid response to changing customer demands). He identifies five significance pillars of efficient e-commerce development: customer-centricity, rapid iterations, enhanced usability, alignment with Agile SDLC, and market adaptability.

---

## Seven communication best practices for product-driven growth

1. **Cross-department collaboration** — Encourage diverse perspectives across departments; break down silos deliberately.
2. **Clear communication channels** — Whether Slack, Teams, Google Chat, or Zoom, every channel must ensure alignment. Ambiguity kills velocity.
3. **Customer feedback integration** — Systematically incorporate user preferences into development priorities; grow products based on actual customer needs.
4. **Data-driven decision-making** — "Data never lies." Use analytics to inform priorities and understand market trends.
5. **Regular review and adaptation** — Stay current with product evolution; iterate continuously as circumstances change.
6. **Agile methodology** — Facilitate rapid response cycles; foster a culture of continuous improvement across the organization.
7. **Training and development** — Granlund calls this critical: "It is going to be detrimental to the success of your business if you don't invest in your team and development," particularly regarding e-commerce trends.

### Internal and external feedback frameworks

Granlund distinguishes between **internal feedback** (team collaboration through defined channels, regular review meetings, stakeholder input during testing cycles) and **external feedback** collected through targeted email surveys and interactive website sections. The Eco Home Goods scenario demonstrates how external feedback revealed strong customer interest in understanding the environmental impact of purchases — insight that directly shaped development priorities.

---

## Product development dashboard and feature request platforms

### Internal dashboard for organizational transparency

Granlund recommends a dedicated internal product development dashboard with six components: a **bug/feature request submission form** that funnels into a live backlog; **release notes** (monthly or quarterly); **priority level classifications** with expected turnaround times; **team display** ("put a face to a name"); an **embedded active backlog** showing approved items and work in progress; and a **sprint timeline** showing expected release dates. Hosting options include Adobe Experience Manager, SharePoint, or custom WordPress pages.

### External feature request platforms

For external transparency, Granlund recommends embedding platforms like **Canny**, **Pendo**, or **ProductBoard** on the e-commerce website. These allow customers to view trending feature requests, see previously submitted items (reducing redundancy), submit new feedback, upvote and comment on submissions, and view product roadmaps. Granlund calls this "absolute gold" for ensuring correct prioritization through customer inclusion.

---

## Requirements gathering from backlog to sprint

Granlund outlines a complete requirements flow: **Stakeholder Input** → **User Feedback Analysis** → **Market and Competitor Analysis** → **Technical Feasibility Assessment** → **Priority Setting** → **Requirements Documentation** → **Continuous Review and Adaptation**.

### Implementation chain roles

The process involves nine linked roles: the **backlog** (incoming data from customer requests, analytics, identified initiatives), the **business analyst** (gathering, analyzing, prioritizing, documenting, facilitating), **subject matter experts** (nominated stakeholders from each department), **external contributors** (customers, suppliers, partners), the **product owner** (reviewing, refining, prioritizing), **sprint/development goals**, **team collaboration** (direct conversations with technical members and stakeholders), **implementation requirements** (UI/UX specs, technical scope, engineering contributions), and the **product manager** (strategic oversight, cross-functional coordination, market insight, performance monitoring, resource allocation).

### Documentation hierarchy

Requirements documentation flows through three levels: **Business Requirements Documents (BRDs)** capture the essence of needed changes with technical specifications; **user stories** are crafted from BRDs with clear acceptance criteria; and **technical scope** documents specify dev and engineering details. The Eco Home Goods example shows BAs organizing workshops with product teams, marketing, and external stakeholders (suppliers, eco-certification agencies), then compiling a BRD with technical specs for displaying certifications and an interactive "product journey" module.

---

## The 13-step testing methodology

Granlund presents a structured testing sequence spanning five phases:

**Test Preparation** (Steps 1–4): Review user stories and acceptance criteria to understand expected user experience; draft test cases addressing new features specifically; set up the testing environment; automate testing setup with configured scripts.

**Test Execution** (Steps 5–7): Execute manual testing; run automated tests; execute all planned test cases systematically.

**Issue Management** (Steps 8–9): Log all defects discovered during execution; verify that defect fixes work properly.

**Performance and Security** (Steps 10–11): Conduct performance testing to evaluate system metrics; perform security testing to validate security posture.

**Documentation and Closure** (Steps 12–13): Update documentation continuously throughout the process; gather stakeholder feedback as the final verification step.

In the Eco Home Goods application, this meant reviewing user stories about eco information and certifications, drafting test cases for eco-friendly product page attributes, setting up the testing environment, running both manual and automated executions, and monitoring results against all acceptance criteria before release.

---

## Traceability matrix for large-scale upgrades

Granlund calls the traceability matrix "one of the most helpful and effective ways to navigate an upgrade." It serves as a central repository mapping requirements through testing to resolution.

| Column | Example |
|---|---|
| Requirement ID | REQ-101 |
| User Story | "As a user, I want product pages to load faster so I can quickly view items" |
| Acceptance Criteria | "Product pages shall load within 2 seconds" |
| Frontend Test Cases | F-TC-101 (Verify product page load time) |
| Backend Test Cases | B-TC-101 (Test database query optimizations) |
| Integration Test Cases | I-TC-101 (Test CDN performance) |
| Defects Logged | DEF-101 |
| Status | Passed / In Progress / Resolved |

**Key benefits**: eliminates ambiguity, enables immediate action on issues, allows direct ticket creation into project management software, and creates reusable templates that improve with each upgrade cycle.

---

## Dual-scale project management and synchronization

Granlund's most sophisticated framework addresses running **regular sprint releases alongside large-scale implementations** (like Adobe Commerce engine upgrades) simultaneously.

### Five optimizations for dual-scale streams

Clear prioritization (allocate resources without overburdening), distinct communication strategies (transparent updates and feedback loops), stakeholder engagement (meeting requirements with appropriate urgency), risk management (tailored mitigation for each stream's unique challenges), and structured change management (formal for large-scale, agile for small-scale).

### Small-scale sprint cycle (5 steps)

Sprint planning → development with dedicated team allocation → continuous testing and integration → stakeholder updates via sprint reviews/demos → release readiness after all tests pass.

### Large-scale upgrade process (5 steps)

Project kickoff defining scope and milestones → **separate upgrade team formation** (critically, NOT drawn from regular sprint personnel) → phased approach (initial setup → data migration → functionality testing) → risk and change management isolated from sprint activities → clear documentation and communication channels.

### Synchronizing both tracks (5 elements)

**Dual track leadership** assigns a dedicated manager overseeing alignment. **Resource allocation and scheduling** identifies critical tasks to prevent unnecessary overlap. **Inter-track communication** establishes regular cross-stream meetings for dependencies and conflicts. **Priority reevaluation** determines whether sprint items can be deferred or whether external resources (agencies) are needed. **Feedback loops** gather input from both sides for continuous improvement.

---

## The Eco Home Goods scenario as practical demonstration

Granlund threads a fictional "Eco Home Goods" company throughout the presentation to demonstrate every framework in context. The company sells sustainable, eco-friendly home products.

**The problem**: The sales team highlighted customer queries about eco-friendliness, customer support received sustainability certification questions, and **high bounce rates** appeared on product detail pages lacking environmental information. Website traffic data confirmed that pages with detailed eco-certifications and product origin stories saw significantly higher engagement and conversion rates.

**Communication applied**: The product development dashboard surfaced the issue, Adobe Workfront managed tasks, and a prioritized list focused on material transparency. Targeted email surveys and interactive website sections revealed strong customer demand for environmental impact information.

**Requirements gathered**: Business analysts organized workshops with product teams, marketing, suppliers, and eco-certification agencies. A BRD specified technical requirements for certification display and an interactive "product journey" module. User stories were crafted (e.g., "customer views product journey timeline showing environmental impact from creation to delivery") and prioritized for the next sprint.

**Testing executed**: The 13-step sequence was applied specifically to eco-friendly attributes and customer engagement features, with test cases targeting certification display accuracy, product journey module functionality, and engagement metrics.

**Expected outcomes**: Decreased customer sustainability inquiries, reduced page bounce rates, significant conversion increases — validating the communication-centric approach.

---

## Conclusion: architectural patterns and methodological synergies

Code Puppy represents a well-architected, privacy-conscious approach to CLI-based AI coding assistance. Its **dual-mode agent system** (Python + JSON) with unified discovery and per-agent tool filtering provides both extensibility and security boundaries. The **round-robin model distribution** across 65+ providers solves real-world rate limiting challenges. The most significant security surface remains unrestricted shell execution and file operations — mitigated primarily by user confirmation prompts rather than sandboxing.

The DBOS durable execution layer, which checkpoints all agent inputs, LLM responses, MCP calls, and tool invocations, addresses production reliability while also creating a potential audit trail for security review. The MCP integration extends capabilities infinitely but also extends the trust boundary to third-party servers.

Granlund's Agile SDLC framework offers complementary value for teams building on platforms like Adobe Commerce. The **traceability matrix** brings systematic accountability to upgrade cycles. The **dual-scale project management** approach — with its insistence on separate upgrade teams isolated from sprint resources — prevents the resource conflicts that derail parallel workstreams. The **13-step testing methodology** provides a repeatable, phase-gated quality process that maps directly to user stories and acceptance criteria. Together, these frameworks form an integrated system where communication drives requirements, requirements drive testing, and testing drives confidence in production releases.