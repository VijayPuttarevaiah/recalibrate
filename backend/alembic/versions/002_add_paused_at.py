"""Add paused_at column to goals

Revision ID: 002_add_paused_at
Revises: 001_initial_schema
Create Date: 2026-04-03 20:32:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_paused_at'
down_revision: Union[str, Sequence[str], None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add paused_at column to goals table."""
    op.add_column('goals', sa.Column('paused_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove paused_at column from goals table."""
    op.drop_column('goals', 'paused_at')
