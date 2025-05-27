"""Remove is_active column from users table

Revision ID: 2025_05_24_0300_remove_is_active_column
Revises: 9750ed829daf
Create Date: 2025-05-24 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025_05_24_0300_remove_is_active_column'
down_revision: str = '9750ed829daf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a no-op since we already removed the column manually
    # The command to drop the column is commented out to avoid errors
    # op.drop_column('users', 'is_active')
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
