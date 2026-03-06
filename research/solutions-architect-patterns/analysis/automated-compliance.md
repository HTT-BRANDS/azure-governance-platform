# Analysis: Automated Architecture Compliance

## Overview

Automated architecture compliance ensures that implementation matches architectural intent through automated checks. This analysis covers tools and patterns for validating architecture decisions in code.

## Leading Tools (2024-2025)

### 1. Fitness Functions (Evolutionary Architecture)

**Concept:** Objective automated checks written in code that verify architecture decisions are maintained.

**How it Works:**
- A decision record documents the decision
- A fitness function assures the decision
- Functions run on every commit/build

**Example Pattern:**
```python
# Decision: "We use event sourcing for audit requirements"
# Fitness Function: "All state changes must produce events"

def test_all_state_changes_produce_events():
    """Fitness function for event sourcing decision."""
    violations = analyze_code_for_state_changes_without_events()
    assert len(violations) == 0, f"State changes without events: {violations}"
```

**Benefits:**
- ✅ Objective measurements (pass/fail)
- ✅ Continuous validation
- ✅ Confidence to refactor
- ✅ Scalable governance

### 2. ArchUnit (Java Architecture Testing)

**Status:** Industry standard for Java architecture testing

**Capabilities:**
- Specify architecture rules in plain Java
- Enforce layer dependencies
- Check package structure
- Validate naming conventions

**Example:**
```java
// Enforce layered architecture
@Test
void layer_dependencies_should_be_respected() {
    layeredArchitecture()
        .layer("Controller").definedBy("..controller..")
        .layer("Service").definedBy("..service..")
        .layer("Repository").definedBy("..repository..")
        .whereLayer("Controller").mayNotBeAccessedByAnyLayer()
        .whereLayer("Service").mayOnlyBeAccessedByLayers("Controller")
        .whereLayer("Repository").mayOnlyBeAccessedByLayers("Service")
        .check(classes);
}
```

**Python Equivalent:**
- No direct equivalent to ArchUnit for Python
- Alternatives: `import-linter`, custom pytest rules

### 3. ArchUnitTS (TypeScript)

**Purpose:** TypeScript/JavaScript architecture testing

**Integration:** Works with Jest, Vitest, Jasmine

**Status:** Active development, growing adoption

### 4. Decision Guardian

**Purpose:** ADR integration with pull requests

**How it Works:**
- Automatically surfaces relevant ADRs on PRs
- Context appears directly in PR review
- Works with any CI system

**Status:** Open source, MIT license, actively developed (2025)

**Integration:**
```yaml
# .github/workflows/decision-guardian.yml
name: Decision Guardian
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: DecispherHQ/decision-guardian@v1
        with:
          decisions-path: 'docs/decisions/'
```

### 5. Spectral (API Compliance)

**Purpose:** API design governance and compliance

**Key Features:**
- JSON/YAML linter for OpenAPI, AsyncAPI, Arazzo
- Custom rulesets
- CI/CD integration
- VS Code extension

**Usage:**
```bash
# Install
npm install -g @stoplight/spectral-cli

# Create ruleset
echo 'extends: ["spectral:oas", "spectral:asyncapi"]' > .spectral.yaml

# Lint API spec
spectral lint openapi.yaml
```

## Patterns for Automated Compliance

### Pattern 1: CI Pipeline Gates

**Structure:**
```
Code Change → Build → Architecture Tests → Unit Tests → Integration → Deploy
                 ↓
           [Fitness Functions]
           [ArchUnit Rules]
           [Import Linter]
```

**Implementation:**
```yaml
# .github/workflows/architecture-compliance.yml
name: Architecture Compliance
on: [push, pull_request]
jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Fitness Functions
        run: pytest tests/architecture/
      - name: Check Architecture Rules
        run: python scripts/check_architecture.py
      - name: Lint API Specs
        run: spectral lint '**/*.openapi.yaml'
```

### Pattern 2: Pre-Commit Hooks

**Tools:**
- `pre-commit` framework
- Custom git hooks
- Local linting

**Configuration:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: fitness-functions
        name: Run Fitness Functions
        entry: pytest tests/architecture/
        language: system
        pass_filenames: false
```

### Pattern 3: IDE Integration

**Benefits:**
- Immediate feedback
- Reduced CI failures
- Developer education

**Tools:**
- ArchUnit: IntelliJ plugin
- Spectral: VS Code extension
- Pylint/Pyright: Architecture rules

### Pattern 4: Decision-to-Code Mapping

**Approach:** Link ADRs to code via:
- Comments referencing ADR numbers
- Directory structure reflecting ADR categories
- File naming conventions

**Example:**
```python
# ADR-0012: Use Azure Lighthouse for multi-tenant access
# See: docs/decisions/0012-use-azure-lighthouse.md

class AzureLighthouseClient:
    """Client implementing ADR-0012 pattern."""
    pass
```

## Multi-Dimensional Analysis

### Security
- **Rating:** ⭐⭐⭐⭐☆ (High)
- Automated compliance prevents security drift
- Spectral includes OWASP security rules
- Can enforce security patterns (e.g., no hardcoded secrets)

### Cost
- **Rating:** ⭐⭐⭐⭐⭐ (Very Low)
- Most tools open source
- Minimal infrastructure
- Prevents costly architecture violations

### Implementation Complexity
- **Rating:** ⭐⭐⭐☆☆ (Medium)
- Fitness functions: Low complexity
- ArchUnit integration: Medium (Java only)
- Full compliance suite: Medium-High

### Stability
- **Rating:** ⭐⭐⭐⭐⭐ (High)
- ArchUnit: Stable, widely used
- Spectral: Active development, production-ready
- Fitness functions: Pattern-based, stable

### Optimization
- **Rating:** ⭐⭐⭐⭐☆ (Good)
- Fast feedback loops
- Caching supported
- Parallel execution possible

### Compatibility
- **Rating:** ⭐⭐⭐⭐☆ (Good)
- Language-specific tools
- CI system agnostic
- IDE integration varies

### Maintenance
- **Rating:** ⭐⭐⭐☆☆ (Medium)
- Rules must evolve with architecture
- Periodic review required
- Test maintenance overhead

## Recommendations for Azure Governance Platform

### Immediate Implementation (Week 1)

1. **Fitness Functions (Python)**
   ```python
   # tests/architecture/test_layering.py
   def test_api_routes_only_in_routes_directory():
       """ADR-0003: All API routes in app/api/routes/"""
       route_files = list(Path('app/api/routes').rglob('*.py'))
       for file in Path('app').rglob('*.py'):
           if 'api' in file.read_text() and 'routes' not in str(file):
               if 'FastAPI' in file.read_text():
                   assert False, f"API routes found outside routes dir: {file}"
   ```

2. **API Compliance with Spectral**
   ```yaml
   # .spectral.yaml
   extends: ["spectral:oas"]
   rules:
     operation-operationId: error
     operation-description: warn
     info-contact: error
   ```

### Short-term (Month 1)

1. **Import Linter Setup**
   ```ini
   # .importlinter
   [importlinter]
   root_package = app
   
   [importlinter:contract:layers]
   name = Layered architecture
   type = layers
   layers =
       app.api.routes
       app.services
       app.models
   ```

2. **Pre-commit Integration**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: fitness-functions
           name: Fitness Functions
           entry: pytest tests/architecture/ -v
           language: system
           pass_filenames: false
           always_run: true
   ```

### Medium-term (Quarter 1)

1. **Decision Guardian Integration**
   - Install Decision Guardian GitHub App
   - Configure to surface ADRs on PRs
   - Train team on review workflow

2. **Custom Fitness Functions**
   - Azure SDK usage patterns
   - Security-related patterns
   - Performance patterns

## Python-Specific Tooling

### Recommended Stack

| Purpose | Tool | Status |
|---------|------|--------|
| Import Linting | `import-linter` | Active |
| Architecture Tests | Custom pytest | N/A |
| API Compliance | Spectral | Excellent |
| Code Analysis | `ast`, `inspect` | Standard lib |
| Pre-commit | `pre-commit` | Industry standard |

### Example Python Fitness Function

```python
# tests/architecture/test_azure_patterns.py
import ast
from pathlib import Path

def test_no_hardcoded_azure_secrets():
    """Check for hardcoded Azure secrets in code."""
    violations = []
    
    for pyfile in Path('app').rglob('*.py'):
        tree = ast.parse(pyfile.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Str):
                if looks_like_azure_secret(node.s):
                    violations.append(f"{pyfile}:{node.lineno}")
    
    assert not violations, f"Hardcoded secrets found: {violations}"

def test_all_external_calls_use_retry_pattern():
    """ADR-0008: All Azure API calls use retry logic."""
    # Implementation using AST analysis
    pass
```

---

## References

- ArchUnit: https://www.archunit.org/
- ArchUnitTS: https://github.com/LukasNiessen/ArchUnitTS
- Spectral: https://meta.stoplight.io/docs/spectral
- Decision Guardian: https://github.com/DecispherHQ/decision-guardian
- Import Linter: https://import-linter.readthedocs.io/
