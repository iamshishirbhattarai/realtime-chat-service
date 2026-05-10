"""add attachments table

Revision ID: 681ced3b8b58
Revises: 2897f6006754
Create Date: 2026-05-10 15:48:38.307956

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '681ced3b8b58'
down_revision: Union[str, Sequence[str], None] = '2897f6006754'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.String(), nullable=True))

    op.create_table(
        "attachments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("uploader_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"], ["messages.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["uploader_id"], ["users.id"]
        ),
    )


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_column("users", "avatar_url")
