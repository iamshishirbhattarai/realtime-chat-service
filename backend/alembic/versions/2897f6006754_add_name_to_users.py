"""add name to users

Revision ID: 2897f6006754
Revises: d98689bb53e2
Create Date: 2026-05-09 21:00:21.694262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2897f6006754'
down_revision: Union[str, Sequence[str], None] = 'd98689bb53e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('name', sa.String(), nullable=True))
    op.execute("UPDATE users SET name = split_part(email, '@', 1) WHERE name IS NULL")
    op.alter_column('users', 'name', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'name')
