"""transaction rate precision and indexes

Revision ID: a3c1d9e5b7f2
Revises: 2fa60f91a2c2
Create Date: 2026-10-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3c1d9e5b7f2'
down_revision: Union[str, Sequence[str], None] = '2fa60f91a2c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Sub-paisa prices (ETFs, funds) were being rounded to 2 dp.
    op.alter_column(
        'transactions',
        'rate',
        existing_type=sa.Numeric(precision=18, scale=2),
        type_=sa.Numeric(precision=18, scale=4),
        existing_nullable=False,
    )
    op.create_index(op.f('ix_transactions_symbol'), 'transactions', ['symbol'], unique=False)
    op.create_index(op.f('ix_portfolios_user_id'), 'portfolios', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_portfolios_user_id'), table_name='portfolios')
    op.drop_index(op.f('ix_transactions_symbol'), table_name='transactions')
    op.alter_column(
        'transactions',
        'rate',
        existing_type=sa.Numeric(precision=18, scale=4),
        type_=sa.Numeric(precision=18, scale=2),
        existing_nullable=False,
    )
