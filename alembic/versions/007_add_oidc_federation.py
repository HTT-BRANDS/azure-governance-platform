"""Add use_oidc column to tenants table for OIDC Workload Identity Federation.

Revision ID: 007
Revises: 006
Create Date: 2026-05-01 00:00:00.000000

Adds the use_oidc boolean column so individual Tenant records can opt in to
OIDC federated credential auth instead of client secrets. Migration is
idempotent — it checks whether the column already exists before adding it.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_exists(table: str, column: str) -> bool:
    """Return True if the column already exists in the table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [col["name"] for col in insp.get_columns(table)]
    return column in columns


def upgrade() -> None:
    """Add use_oidc to the tenants table (idempotent)."""
    if not _column_exists("tenants", "use_oidc"):
        op.add_column(
            "tenants",
            sa.Column(
                "use_oidc",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )


def downgrade() -> None:
    """Drop use_oidc from the tenants table."""
    if _column_exists("tenants", "use_oidc"):
        op.drop_column("tenants", "use_oidc")
