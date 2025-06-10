"""add_meta_column_to_tokens

Revision ID: 8f49697cde7f
Revises: 2e8024eeb4ae
Create Date: 2025-06-11 00:37:24.316947

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f49697cde7f"
down_revision: Union[str, None] = "2e8024eeb4ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add meta column to tokens table
    op.add_column(
        "tokens",
        sa.Column(
            "meta",
            sa.JSON(none_as_null=True),
            nullable=True,
            comment="Additional metadata for the token",
            server_default="{}",
        ),
    )
    # Create an index on the meta column if needed for querying
    # op.create_index(
    #     'ix_tokens_meta',
    #     'tokens',
    #     ['meta'],
    #     unique=False,
    #     postgresql_using='gin',
    # )


def downgrade() -> None:
    # Remove the meta column
    op.drop_column("tokens", "meta")
