"""add user token version

Revision ID: fd2a8c719c4b
Revises: ce8420c5bd13
Create Date: 2026-10-29 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fd2a8c719c4b"
down_revision: Union[str, Sequence[str], None] = "ce8420c5bd13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("users", "token_version", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "token_version")
