"""add_scopes_column_to_tokens

Revision ID: "9a2fd69560c9"
Revises: 38483a79b768
Create Date: 2025-06-04 11:16:06.699070

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a2fd69560c9"
down_revision: Union[str, None] = "38483a79b768"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add scopes column to tokens table
    op.add_column(
        "tokens",
        sa.Column(
            "scopes",
            sa.Text(),
            nullable=True,
            comment="Comma-separated list of token scopes",
        ),
    )


def downgrade() -> None:
    # Remove scopes column from tokens table
    op.drop_column("tokens", "scopes")
