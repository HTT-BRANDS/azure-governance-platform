# CrewAI Framework Documentation - Raw Findings

**Source**: https://docs.crewai.com
**Date Accessed**: 2025-03-06
**Source Tier**: Tier 1 (Official Documentation)

## Agent Role Separation Patterns in CrewAI

### Core Concepts

A crew in CrewAI represents a collaborative group of agents working together to achieve a set of tasks. Each crew defines the strategy for task execution, agent collaboration, and the overall workflow.

### Agent Attributes (Key for Role Definition)

CrewAI agents can be configured with the following key attributes that enable role separation:

| Attribute | Purpose | Relevance to Role Separation |
|-----------|---------|------------------------------|
| `role` | Defines the agent's function within the crew | **Primary separator** - e.g., "Researcher", "Writer", "Reviewer" |
| `goal` | The objective the agent aims to achieve | Drives behavior based on role |
| `backstory` | Context and personality for the agent | Helps differentiate agent approaches |
| `tools` | Capabilities/functions available to the agent | Role-specific tool access |
| `allow_delegation` | Whether agent can delegate to others | Critical for orchestration patterns |
| `max_iter` | Maximum iterations before giving best answer | Prevents infinite loops |
| `max_rpm` | Maximum requests per minute | Rate limiting per agent |
| `verbose` | Enable detailed execution logging | **Traceability** |
| `memory` | Enable memory for context across executions | State management |
| `function_calling_llm` | Specific LLM for tool calling | Role-specific model selection |
| `step_callback` | Function called after each step | **Audit trail hook** |

### Creating Agents with YAML Configuration

CrewAI supports YAML configuration for cleaner, more maintainable agent definitions:

```yaml
# Example from official docs
researcher:
  role: Senior Data Researcher
  goal: Uncover cutting-edge developments in {topic}
  backstory: |
    You're a seasoned researcher with a knack for uncovering the latest
    developments in {topic}. Known for your ability to find the most relevant
    information and present it in a clear and concise manner.
  allow_delegation: false  # Control delegation per role
  verbose: true            # Enable traceability
  tools:
    - search_tool
    - web_scraper

reporting_analyst:
  role: Reporting Analyst
  goal: Create detailed reports based on {topic} data analysis and research findings
  backstory: |
    You're a meticulous analyst with a keen eye for detail. You're known for
    your ability to turn complex data into clear and concise reports, making
    it easy for others to understand and act on the information you provide.
  allow_delegation: true   # Can delegate to researcher
  verbose: true
```

### Example: Basic Research Agent (Planner Pattern)

```python
researcher = Agent(
    role="Research Analyst",
    goal="Uncover the latest information about specific topics",
    backstory="""You are an experienced researcher with attention to detail.""",
    verbose=True  # Enable traceability
)
```

### Example: Code Development Agent (Executor Pattern)

```python
code_agent = Agent(
    role="Python Developer",
    goal="Write clean, efficient Python code",
    backstory="""You are an expert Python developer with 10 years of experience.
    You write clean, well-documented code following best practices.""",
    allow_code_execution=True,  # Can execute code
    max_iterations=5,           # Limit iterations
    verbose=True
)
```

### Example: Long-Running Analysis Agent (Critic Pattern)

```python
analysis_agent = Agent(
    role="Senior Data Analyst",
    goal="Comprehensive analysis of large datasets",
    backstory="""Specialized in big data analysis and pattern recognition.
    You carefully review all findings before drawing conclusions.""",
    respect_context_window=True,  # Manage token limits
    max_rpm=10,                   # Rate limiting for analysis
    verbose=True
)
```

### Crew Attributes for Orchestration

| Attribute | Description | Multi-Agent Pattern Support |
|-----------|-------------|----------------------------|
| `tasks` | List of tasks assigned to the crew | Work distribution |
| `agents` | List of agents that are part of the crew | Team composition |
| `process` | Execution strategy (sequential/hierarchical) | **Orchestration pattern** |
| `memory` | Enable memory for context across executions | Shared state |
| `manager_llm` | LLM used by manager agent | Manager agent capability |
| `manager_agent` | Custom manager agent for hierarchical process | **Manager/worker pattern** |
| `planning` | Enable planning before execution | **Planner pattern** |
| `planning_llm` | LLM used by the agentPlanner | Dedicated planning capability |
| `output_log_file` | Save logs to file | **Audit trail** |
| `step_callback` | Callback after each agent step | **Traceability** |
| `task_callback` | Callback after each task | **Traceability** |

### Process Types for Agent Orchestration

1. **Sequential Process**: Tasks execute in order, one after another
2. **Hierarchical Process**: Manager agent coordinates workers (requires `manager_llm` or `manager_agent`)

### Decorators for Agent Management

CrewAI provides decorators for organizing crew structure:

- `@CrewBase`: Marks class as a crew base class
- `@agent`: Denotes method returning an Agent object
- `@task`: Denotes method returning a Task object
- `@crew`: Denotes method returning a Crew object
- `@before_kickoff`: Marks method to execute before crew starts
- `@after_kickoff`: Marks method to execute after crew finishes

### Crew Output and Traceability

The CrewOutput class provides:
- `raw`: Raw text output
- `pydantic`: Structured Pydantic model output
- `json_dict`: Dictionary output
- `tasks_output`: List of TaskOutput objects
- `token_usage`: Summary of token usage

## Process Implementations - Detailed

### Hierarchical Process (Planner/Executor/Critic Pattern)
**Source**: https://docs.crewai.com/concepts/processes

CrewAI's hierarchical process explicitly implements the manager/worker pattern:

**Manager Agent Responsibilities**:
- Oversees task execution
- **Planning**: Plans task execution strategy
- **Delegation**: Allocates tasks to agents based on their capabilities
- **Validation**: Reviews outputs and assesses task completion
- Tasks are **NOT pre-assigned** - manager dynamically assigns

**Code Example**:
```python
from crewai import Crew, Process

crew = Crew(
    agents=my_agents,  # Worker agents
    tasks=my_tasks,
    process=Process.hierarchical,
    manager_llm="gpt-4o",  # OR manager_agent=my_manager_agent
    planning=True  # Adds planning ability
)
```

**Key Attributes for Hierarchical Mode**:
- `manager_llm`: Language model used by manager agent in hierarchical process
- `manager_agent`: Custom manager agent (alternative to manager_llm)
- `planning`: Adds planning ability to the crew (AgentPlanner)
- `planning_llm`: Language model used by the AgentPlanner

### Sequential Process
- Executes tasks sequentially in predefined order
- Output of one task serves as context for the next
- No dynamic delegation - tasks execute in order

### Consensual Process (Future/Planned)
- Democratic approach to task management
- Planned for future development
- Not currently implemented

## Key Findings for Multi-Agent Architecture

### 1. Agent Role Separation
- **Role attribute** is the primary separator
- **Tools** can be role-specific
- **allow_delegation** controls orchestration capability
- **backstory** provides personality differentiation

### 2. Accountability & Traceability
- `verbose=True` enables detailed logging
- `output_log_file` saves logs to disk
- `step_callback` and `task_callback` for custom audit trails
- `token_usage` tracks resource consumption
- Memory system: short-term, long-term, entity memory

### 3. Agent Delegation Patterns
- **Hierarchical process**: Manager agent coordinates workers with dynamic task allocation
- `allow_delegation`: Controls delegation permissions per agent
- Manager capabilities: planning, delegation, validation, output review

### 4. Critic/Review Patterns
- **Built into Hierarchical Process**: Manager reviews outputs and assesses completion
- Can implement additional critics via role definition and task sequencing
- Sequential process enables review-before-proceed patterns
- `max_iter` limits iterations, forcing "best answer" delivery

### 5. Planner/Executor/Critic Implementation
CrewAI implements this pattern through:
- **Planner**: `manager_llm` or `manager_agent` in hierarchical mode
- **Executor**: Worker agents (defined in `agents` list)
- **Critic**: Manager reviews outputs and can request revisions

## Source Evaluation

**Authority**: Official CrewAI documentation (v1.10.1) - Tier 1
**Currency**: Current as of 2025-03-06, version actively maintained
**Validation**: Cross-reference with GitHub repo (45,294 stars)
**Bias**: Vendor documentation, may emphasize strengths
**Primary Source**: Yes - official framework documentation
