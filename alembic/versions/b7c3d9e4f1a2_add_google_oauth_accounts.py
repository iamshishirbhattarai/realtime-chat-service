"""add google oauth accounts

Revision ID: b7c3d9e4f1a2
Revises: 0342fc12b3d1
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c3d9e4f1a2"
down_revision: Union[str, Sequence[str], None] = "0342fc12b3d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "hashed_password", nullable=True)

    op.create_table(
        "user_oauth_accounts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_user_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "provider", "provider_user_id", name="uq_provider_user"
        ),
    )


def downgrade() -> None:
    op.drop_table("user_oauth_accounts")
    op.alter_column("users", "hashed_password", nullable=False)
