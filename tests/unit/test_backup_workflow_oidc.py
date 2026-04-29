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
