"""increase_current_reduction_pct_precision

Revision ID: bb59ec217272
Revises: 135bec871877
Create Date: 2026-01-14 10:12:52.801718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb59ec217272'
down_revision: Union[str, None] = '135bec871877'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only change the column precision - no index changes needed
    # Deduplication logic works at application level via content_hash queries
    op.alter_column('reduction_targets', 'current_reduction_pct',
               existing_type=sa.NUMERIC(precision=5, scale=2),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('reduction_targets', 'current_reduction_pct',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.NUMERIC(precision=5, scale=2),
               existing_nullable=True)
