"""Remove is_active column from users table.

Revision ID: 2025_05_24_0217_remove_is_active_from_users
Revises: a85d9305d869
Create Date: 2025-05-24 02:17:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2025_05_24_0217_remove_is_active_from_users'
down_revision: Union[str, None] = 'a85d9305d869'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove is_active column from users table."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_active')


def downgrade() -> None:
    """Add back is_active column to users table."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_active', 
                sa.BOOLEAN(), 
                server_default=sa.text('true'), 
                nullable=False
            )
        )
