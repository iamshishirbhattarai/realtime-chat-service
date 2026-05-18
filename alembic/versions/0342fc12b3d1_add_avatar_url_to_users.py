"""add avatar_url to users

Revision ID: 0342fc12b3d1
Revises: 681ced3b8b58
Create Date: 2026-05-10 16:19:22.031478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0342fc12b3d1'
down_revision: Union[str, Sequence[str], None] = '681ced3b8b58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass  # avatar_url already added by 681ced3b8b58_add_attachments_table


def downgrade() -> None:
    pass
