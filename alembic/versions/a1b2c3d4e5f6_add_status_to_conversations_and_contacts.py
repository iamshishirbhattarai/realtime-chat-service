"""add status to conversations and contacts/blocked_contacts tables

Revision ID: a1b2c3d4e5f6
Revises: 5a2820865103
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5a2820865103'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

conversation_status = sa.Enum('pending', 'accepted', name='conversationstatus')


def upgrade() -> None:
    conversation_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'conversations',
        sa.Column(
            'status',
            conversation_status,
            nullable=False,
            server_default='accepted',
        ),
    )

    op.create_table(
        'contacts',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('contact_id', sa.UUID(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'contact_id'),
    )

    op.create_table(
        'blocked_contacts',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('blocked_user_id', sa.UUID(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['blocked_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'blocked_user_id'),
    )


def downgrade() -> None:
    op.drop_table('blocked_contacts')
    op.drop_table('contacts')
    op.drop_column('conversations', 'status')
    conversation_status.drop(op.get_bind(), checkfirst=True)
