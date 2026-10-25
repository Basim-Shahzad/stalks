"""index portfolio transaction history

Revision ID: ce8420c5bd13
Revises: a3c1d9e5b7f2
Create Date: 2026-10-26 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ce8420c5bd13"
down_revision: Union[str, Sequence[str], None] = "a3c1d9e5b7f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_transactions_portfolio_date_created",
        "transactions",
        ["portfolio_id", "transaction_date", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transactions_portfolio_date_created", table_name="transactions"
    )
