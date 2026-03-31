# 🔗 Git Hooks

Custom git hooks for the Azure Governance Platform.

## Quick Start

```bash
# Install hooks (run after cloning)
./.githooks/setup.sh
```

## Installed Hooks

### 1. `commit-msg` — Conventional Commits

Enforces [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Allowed types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `style` — Code style (formatting)
- `refactor` — Code refactoring
- `perf` — Performance improvements
- `test` — Test changes
- `build` — Build system changes
- `ci` — CI/CD changes
- `chore` — Other changes
- `revert` — Revert commit

**Examples:**
```bash
git commit -m "feat(auth): add Azure AD integration"
git commit -m "fix(api): resolve rate limiting issue"
git commit -m "docs: update deployment instructions"
git commit -m "perf(cache): reduce DB queries by 50%"
```

### 2. `pre-push` — Test Runner

Runs tests before allowing push to remote:
- ✅ Lint checks (ruff)
- ✅ Format checks (ruff format)
- ✅ Type checks (mypy)
- ✅ Unit and integration tests

**Environment variables:**
```bash
# Skip tests (not recommended!)
SKIP_PRE_PUSH_TESTS=1 git push

# Quick mode (unit tests only)
PRE_PUSH_QUICK=1 git push

# Bypass all hooks
git push --no-verify
```

### 3. `prepare-commit-msg` — Issue Linking

Automatically:
- Extracts issue numbers from branch names (`feature/123-description` → refs #123)
- Suggests commit types based on changed files
- Prepends templates to commit messages

**Supported branch patterns:**
- `feature/123-my-feature` → refs #123
- `fix/456-bug-fix` → fixes #456
- `issue/789-something` → refs #789
- `123-description` → refs #123

## Configuration

### Install
```bash
./.githooks/setup.sh
```

### Remove
```bash
./.githooks/setup.sh --remove
```

### Check Status
```bash
git config --local core.hooksPath
```

## Bypassing Hooks

In case of emergencies:

```bash
# Skip commit-msg hook
git commit -m "emergency fix" --no-verify

# Skip pre-push tests
git push --no-verify

# Skip specific tests with env vars
SKIP_PRE_PUSH_TESTS=1 git push
```

⚠️ **Note:** Bypassing hooks should be rare. Fix the underlying issue instead.

## Troubleshooting

### Hooks not running
```bash
# Check if hooks are configured
git config --local core.hooksPath

# Re-install
./.githooks/setup.sh

# Check file permissions
ls -la .githooks/
```

### Conventional commits failing
```bash
# Check your commit message format
git log -1 --pretty=%B

# Amend the last commit
git commit --amend -m "fix: correct message format"
```

### Tests failing on push
```bash
# Run tests locally to debug
uv run pytest tests/unit/ tests/integration/ -v

# Check lint errors
uv run ruff check .

# Fix formatting
uv run ruff format .
```
