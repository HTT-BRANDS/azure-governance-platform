"""Contract checks for the Database Backup GitHub Actions workflow."""

from pathlib import Path

BACKUP_WORKFLOW = Path(".github/workflows/backup.yml")


def test_backup_workflow_grants_oidc_token_permission_for_azure_login():
    """azure/login@v2 needs id-token: write when using OIDC federation."""
    workflow = BACKUP_WORKFLOW.read_text()

    assert "uses: azure/login@v2" in workflow
    assert "permissions:" in workflow
    assert "contents: read" in workflow
    assert "id-token: write" in workflow


def test_production_backup_uses_approval_free_environment_without_changing_target():
    """Production backup auth is separated from deploy-production approvals."""
    workflow = BACKUP_WORKFLOW.read_text()

    assert "environment: production" not in workflow
    assert "production-backup" in workflow
    assert "BACKUP_ENVIRONMENT: ${{ github.event.inputs.environment || 'production' }}" in workflow
    assert "repo:HTT-BRANDS/control-tower:environment:production-backup" in workflow


def test_backup_workflow_does_not_use_repo_level_secret_fallbacks():
    """Backup remains environment-scoped for secrets; production deploy stays guarded."""
    workflow = BACKUP_WORKFLOW.read_text()

    assert "secrets.AZURE_CLIENT_ID" in workflow
    assert "secrets.DATABASE_URL" in workflow
    assert "secrets.PRODUCTION_TEAMS_WEBHOOK" in workflow
