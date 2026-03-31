#!/bin/bash
# =============================================================================
# Git Hooks Setup Script
# =============================================================================
# Configures git to use the .githooks/ directory for hooks.
# Must be run after cloning the repository.
#
# Usage:
#   ./.githooks/setup.sh           # Install hooks
#   ./.githooks/setup.sh --remove  # Remove hooks
# =============================================================================

set -e

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")

if [ -z "$REPO_ROOT" ]; then
    echo "❌ Not a git repository"
    exit 1
fi

cd "$REPO_ROOT"

HOOKS_DIR="$REPO_ROOT/.githooks"
GIT_DIR=$(git rev-parse --git-dir)

# Check for --remove flag
if [ "$1" = "--remove" ] || [ "$1" = "-r" ]; then
    echo "Removing custom git hooks..."
    git config --local --unset core.hooksPath 2>/dev/null || true
    echo "✅ Hooks removed. Git will use default .git/hooks/"
    exit 0
fi

# Check if hooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ Hooks directory not found: $HOOKS_DIR"
    exit 1
fi

# Make hooks executable
echo "Making hooks executable..."
chmod +x "$HOOKS_DIR"/* 2>/dev/null || true

# Configure git to use our hooks directory
echo "Configuring git core.hooksPath..."
git config --local core.hooksPath "$HOOKS_DIR"

# Verify
current_path=$(git config --local core.hooksPath)
if [ "$current_path" = "$HOOKS_DIR" ]; then
    echo ""
    echo "✅ Git hooks installed successfully!"
    echo ""
    echo "Installed hooks:"
    for hook in "$HOOKS_DIR"/*; do
        if [ -f "$hook" ] && [ -x "$hook" ]; then
            hook_name=$(basename "$hook")
            if [ "$hook_name" != "setup.sh" ] && [ "$hook_name" != "README.md" ]; then
                echo "  ✓ $hook_name"
            fi
        fi
    done
    echo ""
    echo "To remove: ./.githooks/setup.sh --remove"
else
    echo "❌ Failed to configure hooks"
    exit 1
fi
