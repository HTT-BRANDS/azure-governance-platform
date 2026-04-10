"""Widen policy_name column from 255 to 1000 characters.

Revision ID: 009
Revises: 008
Create Date: 2026-04-04 00:00:00.000000

Widens policy_name in policy_states from NVARCHAR(255) to NVARCHAR(1000)
to accommodate long Azure Policy names that were causing DataError overflow,
poisoning the SQLAlchemy session and cascading to kill ALL sync jobs.

This is a metadata-only operation on Azure SQL (sub-millisecond, no data rewrite).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Widen policy_name to 1000 characters (idempotent)."""
    op.alter_column(
        "policy_states",
        "policy_name",
        existing_type=sa.String(255),
        type_=sa.String(1000),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Narrow policy_name back to 255 characters.

    WARNING: This may cause data loss if any policy_name values exceed 255
    characters. Review data before running this downgrade.
    """
    op.alter_column(
        "policy_states",
        "policy_name",
        existing_type=sa.String(1000),
        type_=sa.String(255),
        existing_nullable=False,
    )
