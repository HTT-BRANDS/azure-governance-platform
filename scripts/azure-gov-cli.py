#!/usr/bin/env python3
"""
Azure Governance Platform CLI Tool

A unified command-line interface for common platform operations.
Provides colorized output, structured logging, and intuitive subcommands.

Usage:
    python scripts/azure-gov-cli.py --help
    python scripts/azure-gov-cli.py sync --tenant riverside
    python scripts/azure-gov-cli.py status
    python scripts/azure-gov-cli.py health --verbose

Author: Code Puppy (Richard) 🐶
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Color codes for terminal output
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
}


class Colors:
    """Namespace for color functions to keep code clean."""

    @staticmethod
    def success(text: str) -> str:
        return f"{COLORS['green']}✓ {text}{COLORS['reset']}"

    @staticmethod
    def error(text: str) -> str:
        return f"{COLORS['red']}✗ {text}{COLORS['reset']}"

    @staticmethod
    def warning(text: str) -> str:
        return f"{COLORS['yellow']}⚠ {text}{COLORS['reset']}"

    @staticmethod
    def info(text: str) -> str:
        return f"{COLORS['blue']}ℹ {text}{COLORS['reset']}"

    @staticmethod
    def header(text: str) -> str:
        return f"\n{COLORS['bold']}{COLORS['cyan']}{text}{COLORS['reset']}"

    @staticmethod
    def dim(text: str) -> str:
        return f"{COLORS['dim']}{text}{COLORS['reset']}"


@dataclass
class CLIContext:
    """Context passed to command handlers."""

    verbose: bool
    dry_run: bool
    env_file: str | None


def print_banner() -> None:
    """Print the Azure Gov CLI banner."""
    # Use raw string to avoid escape sequence issues
    cyan_bold = COLORS["cyan"] + COLORS["bold"]
    reset = COLORS["reset"]
    dim = COLORS["dim"]

    print(f"""
{cyan_bold}    ___                            _____                     {reset}
{cyan_bold}   /   |   ____   ____ _   _____ / ___/  ____    ____   ___ {reset}
{cyan_bold}  / /| |  / __ \\ / __ `| / ___/ \\__ \\  / __ \\  / __ \\ / _ \\{reset}
{cyan_bold} / ___ | / /_/ // /_/ // /    ___/ / / /_/ / / / / //  __/{reset}
{cyan_bold}/_/  |_|/ .___/ \\__,_//_/    /____/  \\____/ /_/ /_/ \\___/ {reset}
{cyan_bold}       /_/                                                  {reset}

{dim}Azure Governance Platform CLI v1.0.0 | Code Puppy 🐶{reset}
""")


def run_command(
    cmd: list[str],
    cwd: str | None = None,
    capture: bool = True,
    shell: bool = False,
) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture,
            text=True,
            shell=shell,
            timeout=300,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 300 seconds"
    except Exception as e:
        return -1, "", str(e)


def load_env_vars(env_file: str | None = None) -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars: dict[str, str] = {}

    # Determine which env file to use
    if env_file:
        target_file = env_file
    elif os.getenv("ENVIRONMENT") == "production":
        target_file = ".env.production"
    else:
        target_file = ".env"

    env_path = Path(target_file)
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env_vars[key] = value.strip("\"'")

    return env_vars


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND: SYNC
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_sync(args: argparse.Namespace, ctx: CLIContext) -> int:
    """Run sync operations for tenants."""
    print(Colors.header("🔄 SYNC OPERATION"))

    load_env_vars(ctx.env_file)  # Loads and validates env
    project_root = Path(__file__).parent.parent

    tenants: list[str] = []
    if args.tenant:
        tenants = [args.tenant]
    elif args.all:
        # Get all tenants from config
        tenants = ["riverside", "hub"]  # Default tenants
        tenants_config = project_root / "config" / "tenants.yaml"
        if tenants_config.exists() and ctx.verbose:
            print(Colors.info(f"Found tenants config: {tenants_config}"))
    else:
        print(Colors.error("Specify --tenant <name> or --all"))
        return 1

    sync_types = (
        args.type.split(",") if args.type else ["resources", "identity", "compliance", "costs"]
    )

    for tenant in tenants:
        print(f"\n{COLORS['bold']}Tenant: {tenant}{COLORS['reset']}")

        for sync_type in sync_types:
            if ctx.verbose:
                print(Colors.dim(f"  → Syncing {sync_type}..."))

            if ctx.dry_run:
                print(Colors.info(f"  [DRY RUN] Would sync {sync_type} for {tenant}"))
                continue

            # Run the appropriate sync script
            sync_script = project_root / "scripts" / "manual_sync.py"
            if sync_script.exists():
                cmd = [
                    "python",
                    str(sync_script),
                    "--tenant",
                    tenant,
                    "--resource",
                    sync_type,
                ]
                if args.full:
                    cmd.append("--full")

                exit_code, stdout, stderr = run_command(cmd)

                if exit_code == 0:
                    print(f"  {Colors.success(f'{sync_type}: synced')}")
                else:
                    print(f"  {Colors.error(f'{sync_type}: failed')}")
                    if ctx.verbose and stderr:
                        print(Colors.dim(f"    {stderr[:200]}"))
            else:
                print(f"  {Colors.warning(f'{sync_type}: sync script not found')}")

    print(f"\n{Colors.success('Sync operation complete')}")
    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND: STATUS
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_status(args: argparse.Namespace, ctx: CLIContext) -> int:
    """Show platform status overview."""
    print(Colors.header("📊 PLATFORM STATUS"))

    env = load_env_vars(ctx.env_file)
    project_root = Path(__file__).parent.parent

    # Environment info
    print(f"\n{COLORS['bold']}Environment:{COLORS['reset']}")
    env_name = env.get("ENVIRONMENT", "development")
    env_color = COLORS["green"] if env_name == "production" else COLORS["yellow"]
    print(f"  Environment: {env_color}{env_name}{COLORS['reset']}")
    print(f"  Database: {env.get('DATABASE_URL', 'Not configured')[:50]}...")
    print(f"  Key Vault: {env.get('AZURE_KEY_VAULT_NAME', 'Not configured')}")

    # Check git status
    print(f"\n{COLORS['bold']}Git Status:{COLORS['reset']}")
    exit_code, stdout, _ = run_command(
        ["git", "describe", "--tags", "--always"], cwd=str(project_root)
    )
    if exit_code == 0:
        print(f"  Version: {COLORS['cyan']}{stdout.strip()}{COLORS['reset']}")

    exit_code, stdout, _ = run_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(project_root)
    )
    if exit_code == 0:
        branch = stdout.strip()
        branch_color = COLORS["green"] if branch == "main" else COLORS["yellow"]
        print(f"  Branch: {branch_color}{branch}{COLORS['reset']}")

    # Check for uncommitted changes
    exit_code, stdout, _ = run_command(["git", "status", "--porcelain"], cwd=str(project_root))
    if stdout.strip():
        print(f"  Working tree: {COLORS['yellow']}has uncommitted changes{COLORS['reset']}")
    else:
        print(f"  Working tree: {COLORS['green']}clean{COLORS['reset']}")

    # Container registry status
    print(f"\n{COLORS['bold']}Container Registry:{COLORS['reset']}")
    registry = env.get("CONTAINER_REGISTRY", "ghcr.io")
    image = env.get("CONTAINER_IMAGE_NAME", "azure-governance-platform")
    print(f"  Registry: {registry}")
    print(f"  Image: {image}")

    # Check for latest image tag
    if args.verbose:
        print(Colors.dim("  Checking for latest image..."))
        # Try to get image info from ghcr or acr
        if "ghcr.io" in registry:
            cmd = [
                "gh",
                "api",
                f"/user/packages/container/{image}/versions",
                "--jq",
                ".[0].metadata.container.tags[0]",
            ]
            exit_code, stdout, _ = run_command(cmd)
            if exit_code == 0 and stdout.strip():
                print(f"  Latest tag: {COLORS['cyan']}{stdout.strip()}{COLORS['reset']}")

    # Database migrations status
    print(f"\n{COLORS['bold']}Database:{COLORS['reset']}")
    migrations_dir = project_root / "alembic" / "versions"
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob("*.py"))
        print(f"  Migrations: {len(migration_files)} files")

        # Check current migration
        result = run_command(["python", "-m", "alembic", "current"], cwd=str(project_root))
        if result[0] == 0:
            current = result[1].strip().split()[0] if result[1] else "unknown"
            print(f"  Current: {COLORS['cyan']}{current}{COLORS['reset']}")

    # Tenant status
    print(f"\n{COLORS['bold']}Tenants:{COLORS['reset']}")
    tenants = ["riverside", "hub"]  # Default
    for tenant in tenants:
        status_icon = COLORS["green"] + "●" + COLORS["reset"]
        print(f"  {status_icon} {tenant}")

    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND: HEALTH
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_health(args: argparse.Namespace, ctx: CLIContext) -> int:
    """Check health of platform components."""
    print(Colors.header("🏥 HEALTH CHECK"))

    env = load_env_vars(ctx.env_file)
    project_root = Path(__file__).parent.parent
    all_healthy = True

    checks: list[tuple[str, list[str], int]] = [
        ("Database", ["python", "-c", "from app.db.session import engine; engine.connect()"], 10),
        (
            "Redis",
            ["python", "-c", "from app.core.cache import redis_client; redis_client.ping()"],
            5,
        ),
        (
            "Key Vault",
            ["python", "-c", "from app.core.config import settings; settings.AZURE_KEY_VAULT_NAME"],
            5,
        ),
    ]

    # Run health checks
    for name, cmd, timeout in checks:
        print(f"\n  Checking {COLORS['bold']}{name}{COLORS['reset']}...", end=" ")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONPATH": str(project_root)},
            )

            if result.returncode == 0:
                print(Colors.success("healthy"))
            else:
                print(Colors.error("unhealthy"))
                all_healthy = False
                if ctx.verbose and result.stderr:
                    print(Colors.dim(f"    {result.stderr[:150]}"))
        except Exception as e:
            print(Colors.error(f"error: {e}"))
            all_healthy = False

    # API health check
    api_url = env.get("API_BASE_URL", "http://localhost:8000")
    print(f"\n  Checking {COLORS['bold']}API ({api_url}){COLORS['reset']}...", end=" ")

    try:
        import urllib.request

        req = urllib.request.Request(
            f"{api_url}/health", headers={"Accept": "application/json"}, method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print(Colors.success("healthy"))
                if ctx.verbose:
                    data = json.loads(resp.read().decode())
                    print(Colors.dim(f"    Status: {data.get('status', 'unknown')}"))
            else:
                print(Colors.warning(f"status {resp.status}"))
    except Exception as e:
        print(Colors.error(f"unreachable ({e})"))
        all_healthy = False

    # Azure connectivity
    print(f"\n  Checking {COLORS['bold']}Azure Connectivity{COLORS['reset']}...", end=" ")
    result = run_command(["az", "account", "show", "--query", "name", "-o", "tsv"], capture=True)
    if result[0] == 0:
        subscription = result[1].strip()
        print(Colors.success(f"connected ({subscription})"))
    else:
        print(Colors.warning("not authenticated"))

    # Summary
    print(f"\n{COLORS['bold']}{'─' * 50}{COLORS['reset']}")
    if all_healthy:
        print(f"{Colors.success('All systems healthy! 🎉')}")
        return 0
    else:
        print(f"{Colors.warning('Some systems need attention')}")
        return 1


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND: BACKUP
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_backup(args: argparse.Namespace, ctx: CLIContext) -> int:
    """Create database backup."""
    print(Colors.header("💾 DATABASE BACKUP"))

    load_env_vars(ctx.env_file)
    project_root = Path(__file__).parent.parent

    # Use the existing backup script
    backup_script = project_root / "scripts" / "backup_database.py"

    # Use the existing backup script
    backup_script = project_root / "scripts" / "backup_database.py"

    if not backup_script.exists():
        print(Colors.error(f"Backup script not found: {backup_script}"))
        return 1

    cmd: list[str] = ["python", str(backup_script)]

    if args.output:
        cmd.extend(["--output", args.output])
    if args.upload and not ctx.dry_run:
        cmd.append("--upload")

    print(f"\n{Colors.info('Running backup...')}")

    if ctx.dry_run:
        print(Colors.info(f"[DRY RUN] Would execute: {' '.join(cmd)}"))
        return 0

    exit_code, stdout, stderr = run_command(cmd, cwd=str(project_root))

    if exit_code == 0:
        print(f"{Colors.success('Backup completed successfully')}")
        if ctx.verbose and stdout:
            print(Colors.dim(stdout[-500:]))  # Last 500 chars
    else:
        print(f"{Colors.error('Backup failed')}")
        if stderr:
            print(Colors.dim(stderr[:500]))
        return 1

    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND: DEPLOY
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_deploy(args: argparse.Namespace, ctx: CLIContext) -> int:
    """Deploy the application."""
    print(Colors.header("🚀 DEPLOYMENT"))

    env = load_env_vars(ctx.env_file)
    project_root = Path(__file__).parent.parent

    environment = args.environment or env.get("ENVIRONMENT", "staging")

    print(f"\n  Environment: {COLORS['cyan']}{environment}{COLORS['reset']}")

    if environment == "production" and not args.force:
        print(Colors.warning("\n⚠️  Production deployment requires --force flag"))
        return 1

    # Pre-deployment checks
    print(f"\n{COLORS['bold']}Pre-deployment checks:{COLORS['reset']}")

    # Check git status
    exit_code, stdout, _ = run_command(["git", "status", "--porcelain"], cwd=str(project_root))
    if stdout.strip():
        print(f"  {Colors.warning('Uncommitted changes detected')}")
        if not args.skip_checks:
            return 1
    else:
        print(f"  {Colors.success('Git status clean')}")

    # Select deployment script
    if environment == "staging":
        deploy_script = project_root / "scripts" / "deploy-dev.sh"
    elif environment == "production":
        deploy_script = project_root / "scripts" / "gh-deploy-dev.sh"
    else:
        print(Colors.error(f"Unknown environment: {environment}"))
        return 1

    if not deploy_script.exists():
        print(Colors.error(f"Deploy script not found: {deploy_script}"))
        return 1

    cmd = ["bash", str(deploy_script)]

    if ctx.dry_run:
        print(Colors.info(f"\n[DRY RUN] Would execute: {' '.join(cmd)}"))
        return 0

    print(f"\n{Colors.info('Starting deployment...')}")

    # Run deployment
    exit_code, stdout, stderr = run_command(cmd, cwd=str(project_root))

    if exit_code == 0:
        print(f"\n{Colors.success('Deployment completed successfully! 🎉')}")
    else:
        print(f"\n{Colors.error('Deployment failed')}")
        if ctx.verbose and stderr:
            print(Colors.dim(stderr[-1000:]))
        return 1

    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND: CONFIG
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_config(args: argparse.Namespace, ctx: CLIContext) -> int:
    """Manage configuration."""
    print(Colors.header("⚙️  CONFIGURATION"))

    env = load_env_vars(ctx.env_file)

    if args.action == "show":
        print(f"\n{COLORS['bold']}Current Configuration:{COLORS['reset']}")

        # Show non-sensitive config
        safe_keys = [
            "ENVIRONMENT",
            "API_BASE_URL",
            "CONTAINER_REGISTRY",
            "CONTAINER_IMAGE_NAME",
            "DATABASE_URL",
            "AZURE_KEY_VAULT_NAME",
            "AZURE_TENANT_ID",
            "AZURE_SUBSCRIPTION_ID",
            "REDIS_URL",
        ]

        for key in sorted(safe_keys):
            value = env.get(key, "<not set>")
            if "password" in key.lower() or "secret" in key.lower() or "key" in key.lower():
                value = "***" if value != "<not set>" else value
            print(f"  {key:30} = {value}")

    elif args.action == "validate":
        print(f"\n{COLORS['bold']}Validating Configuration:{COLORS['reset']}")

        required_keys = [
            "ENVIRONMENT",
            "DATABASE_URL",
            "JWT_SECRET_KEY",
        ]

        all_valid = True
        for key in required_keys:
            value = env.get(key)
            if value:
                print(f"  {Colors.success(key)}")
            else:
                print(f"  {Colors.error(key + ' (missing)')}")
                all_valid = False

        if all_valid:
            print(f"\n{Colors.success('Configuration is valid')}")
            return 0
        else:
            print(f"\n{Colors.error('Configuration has errors')}")
            return 1

    elif args.action == "env":
        # Generate env file template
        template = """# Azure Governance Platform Environment Configuration
# Generated by azure-gov-cli config env

# Environment
ENVIRONMENT=development
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/governance  # pragma: allowlist secret

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-here  # pragma: allowlist secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Azure
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_KEY_VAULT_NAME=your-keyvault

# Container Registry
CONTAINER_REGISTRY=ghcr.io
CONTAINER_IMAGE_NAME=azure-governance-platform
"""
        print(template)

    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CLI SETUP
# ═══════════════════════════════════════════════════════════════════════════════


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="azure-gov-cli",
        description="Azure Governance Platform CLI - Unified operations tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s sync --tenant riverside --type resources,identity
  %(prog)s status --verbose
  %(prog)s health
  %(prog)s backup --upload
  %(prog)s deploy --environment staging
  %(prog)s config validate

For more help: %(prog)s <command> --help
        """,
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without executing"
    )
    parser.add_argument("--env-file", help="Path to environment file (.env)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # SYNC command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Run sync operations for tenants",
        description="Synchronize Azure data (resources, identity, compliance, costs)",
    )
    sync_parser.add_argument("--tenant", help="Sync specific tenant")
    sync_parser.add_argument("--all", action="store_true", help="Sync all tenants")
    sync_parser.add_argument(
        "--type", help="Sync types (comma-separated: resources,identity,compliance,costs)"
    )
    sync_parser.add_argument("--full", action="store_true", help="Full sync instead of incremental")
    sync_parser.set_defaults(func=cmd_sync)

    # STATUS command
    status_parser = subparsers.add_parser(
        "status",
        help="Show platform status overview",
        description="Display environment, git, database, and tenant status",
    )
    status_parser.set_defaults(func=cmd_status)

    # HEALTH command
    health_parser = subparsers.add_parser(
        "health",
        help="Check health of platform components",
        description="Verify database, Redis, Key Vault, API, and Azure connectivity",
    )
    health_parser.add_argument("--timeout", type=int, default=30, help="Health check timeout")
    health_parser.set_defaults(func=cmd_health)

    # BACKUP command
    backup_parser = subparsers.add_parser(
        "backup",
        help="Create database backup",
        description="Backup database with optional Azure Blob upload",
    )
    backup_parser.add_argument("--output", help="Output file path")
    backup_parser.add_argument("--upload", action="store_true", help="Upload to Azure Blob Storage")
    backup_parser.set_defaults(func=cmd_backup)

    # DEPLOY command
    deploy_parser = subparsers.add_parser(
        "deploy",
        help="Deploy the application",
        description="Deploy to staging or production environment",
    )
    deploy_parser.add_argument(
        "--environment", choices=["staging", "production"], help="Deployment environment"
    )
    deploy_parser.add_argument("--force", action="store_true", help="Force production deployment")
    deploy_parser.add_argument(
        "--skip-checks", action="store_true", help="Skip pre-deployment checks"
    )
    deploy_parser.set_defaults(func=cmd_deploy)

    # CONFIG command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration",
        description="View, validate, and generate configuration",
    )
    config_parser.add_argument(
        "action",
        choices=["show", "validate", "env"],
        help="Config action: show (display), validate (check), env (generate template)",
    )
    config_parser.set_defaults(func=cmd_config)

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Print banner unless in quiet mode
    if not hasattr(args, "func") or args.command != "config":
        print_banner()

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    ctx = CLIContext(
        verbose=args.verbose,
        dry_run=args.dry_run,
        env_file=args.env_file,
    )

    try:
        return args.func(args, ctx)
    except KeyboardInterrupt:
        print(f"\n{Colors.warning('Operation cancelled by user')}")
        return 130
    except Exception as e:
        print(f"\n{Colors.error(f'Error: {e}')}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
