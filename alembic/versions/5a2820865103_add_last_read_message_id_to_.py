"""add last_read_message_id to conversation participants

Revision ID: 5a2820865103
Revises: 42a0d4b941a5
Create Date: 2026-05-15 14:30:21.944366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a2820865103'
down_revision: Union[str, Sequence[str], None] = '42a0d4b941a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('conversation_participants', sa.Column('last_read_message_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_cp_last_read_message_id',
        'conversation_participants', 'messages',
        ['last_read_message_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_cp_last_read_message_id', 'conversation_participants', type_='foreignkey')
    op.drop_column('conversation_participants', 'last_read_message_id')
