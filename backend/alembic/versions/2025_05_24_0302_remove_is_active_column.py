"""Remove is_active column from users table

Revision ID: 2025_05_24_0302_remove_is_active_column
Revises: 9750ed829daf  # This should be the revision ID of the last applied migration
Create Date: 2025-05-24 03:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025_05_24_0302_remove_is_active_column'
down_revision: str = '9750ed829daf'  # Update this to match your last migration ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a no-op since we already removed the column manually
    # The command to drop the column is commented out to avoid errors
    pass


def downgrade() -> None:
    # Add back the is_active column with the same properties it had before
    op.add_column(
        'users',
        sa.Column(
            'is_active',
            sa.BOOLEAN(),
            server_default=sa.text('true'),
            nullable=True
        )
    )
