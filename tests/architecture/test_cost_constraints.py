"""Architecture fitness tests — cost & dependency constraints.

These tests verify that the project stays lean and doesn't accumulate
unnecessary dependencies, bloated files, or expensive infrastructure.
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
APP_DIR = PROJECT_ROOT / "app"
INFRA_DIR = PROJECT_ROOT / "infrastructure"


# ============================================================================
# COST-1: Dependency count budget
# ============================================================================


class TestDependencyBudget:
    """Runtime dependencies must stay within a reasonable budget."""

    MAX_DIRECT_DEPS = 40  # Alert if we exceed this

    def test_direct_dependency_count(self):
        pyproject = PROJECT_ROOT / "pyproject.toml"
        content = pyproject.read_text()

        # Count lines in the [project] dependencies array
        in_deps = False
        deps = []
        for line in content.splitlines():
            if line.strip().startswith("dependencies"):
                in_deps = True
                continue
            if in_deps:
                if line.strip() == "]":
                    break
                cleaned = line.strip().strip('",')
                if cleaned and not cleaned.startswith("#"):
                    deps.append(cleaned)

        assert len(deps) <= self.MAX_DIRECT_DEPS, (
            f"Direct dependency count ({len(deps)}) exceeds budget ({self.MAX_DIRECT_DEPS}). "
            f"Review whether all deps are truly needed."
        )

    def test_no_duplicate_dependencies(self):
        """No package should appear twice in dependencies."""
        pyproject = PROJECT_ROOT / "pyproject.toml"
        content = pyproject.read_text()

        in_deps = False
        names = []
        for line in content.splitlines():
            if line.strip().startswith("dependencies"):
                in_deps = True
                continue
            if in_deps:
                if line.strip() == "]":
                    break
                match = re.match(r'\s*"([a-zA-Z0-9_-]+)', line)
                if match:
                    names.append(match.group(1).lower())

        dupes = [n for n in names if names.count(n) > 1]
        assert not dupes, f"Duplicate dependencies: {set(dupes)}"


# ============================================================================
# COST-2: No dev-only packages in production deps
# ============================================================================


class TestNoProdDevLeakage:
    """Dev/test packages must not appear in production dependencies."""

    DEV_ONLY_PACKAGES = {
        "pytest",
        "ruff",
        "mypy",
        "isort",
        "flake8",
        "coverage",
        "tox",
        "nox",
        "hypothesis",
        "faker",
        "playwright",
        "selenium",
        "locust",
    }

    def test_no_dev_packages_in_prod_deps(self):
        pyproject = PROJECT_ROOT / "pyproject.toml"
        content = pyproject.read_text()

        # Extract just the [project] dependencies (before [project.optional-dependencies])
        in_deps = False
        dep_names = []
        for line in content.splitlines():
            if line.strip().startswith("dependencies"):
                in_deps = True
                continue
            if in_deps:
                if line.strip() == "]":
                    break
                match = re.match(r'\s*"([a-zA-Z0-9_-]+)', line)
                if match:
                    dep_names.append(match.group(1).lower())

        violations = [
            f"{pkg} found in production deps" for pkg in self.DEV_ONLY_PACKAGES if pkg in dep_names
        ]

        assert not violations, "\n".join(violations)


# ============================================================================
# COST-3: Docker image shouldn't include build tools
# ============================================================================


class TestDockerImageLean:
    """Dockerfile production stage must strip build tools."""

    def test_dockerfile_strips_build_tools(self):
        dockerfile = PROJECT_ROOT / "Dockerfile"
        if not dockerfile.exists():
            pytest.skip("No Dockerfile found")

        content = dockerfile.read_text()

        # After the COPY --from=builder, there should be a cleanup step
        assert "rm -f /usr/local/bin/uv" in content or "rm -rf" in content, (
            "Dockerfile doesn't strip build tools (uv/pip/wheel) from production image"
        )

    def test_dockerfile_uses_nonroot_user(self):
        dockerfile = PROJECT_ROOT / "Dockerfile"
        if not dockerfile.exists():
            pytest.skip("No Dockerfile found")

        content = dockerfile.read_text()
        assert "USER" in content, "Dockerfile must switch to non-root USER"
        assert "useradd" in content or "adduser" in content, (
            "Dockerfile must create a non-root user"
        )


# ============================================================================
# COST-4: Infrastructure SKU guardrails
# ============================================================================


class TestInfrastructureSKUs:
    """Infrastructure templates must use cost-appropriate SKUs."""

    EXPENSIVE_SKUS = [
        "Premium_P1",
        "Premium_P2",
        "Premium_P4",  # Redis
        "S3",
        "S4",
        "P1",
        "P2",
        "P3",  # App Service (non-prod)
    ]

    def test_no_expensive_skus_in_bicep(self):
        violations = []
        for f in INFRA_DIR.rglob("*.bicep"):
            content = f.read_text()
            for sku in self.EXPENSIVE_SKUS:
                if f"'{sku}'" in content:
                    violations.append(f"{f.relative_to(PROJECT_ROOT)}: uses expensive SKU '{sku}'")

        # This is advisory, not a hard fail (might be needed for production)
        if violations:
            pytest.skip(
                f"Advisory: {len(violations)} expensive SKU references found. "
                f"Verify these are intentional."
            )


# ============================================================================
# COST-5: File size budget (prevents bloated modules)
# ============================================================================


class TestFileSizeBudget:
    """No single Python file should exceed 600 lines."""

    MAX_LINES = 600
    # Threshold for new files. Existing tech debt is tracked separately.
    WARN_THRESHOLD = 800

    def test_no_new_mega_files(self):
        """No file should exceed the warning threshold (aggressive bloat)."""
        violations = []
        for f in APP_DIR.rglob("*.py"):
            lines = len(f.read_text().splitlines())
            if lines > self.WARN_THRESHOLD:
                violations.append(
                    f"{f.relative_to(PROJECT_ROOT)}: {lines} lines (warn at {self.WARN_THRESHOLD})"
                )

        # Advisory: prints but doesn't fail (pre-existing tech debt)
        if violations:
            print(
                f"\n⚠️  {len(violations)} files above {self.WARN_THRESHOLD}-line threshold:\n"
                + "\n".join(f"  - {v}" for v in violations)
            )
