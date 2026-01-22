"""add leads_score column to reddit_posts table

Revision ID: a1b2c3d4e5f6
Revises: 11faf0623962
Create Date: 2025-09-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '11faf0623962'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add leads_score column to reddit_posts table."""
    op.add_column(
        'reddit_posts',
        sa.Column('leads_score', sa.Float, nullable=False, default=0.0, server_default='0.0')
    )


def downgrade() -> None:
    """Remove leads_score column from reddit_posts table."""
    op.drop_column('reddit_posts', 'leads_score')
