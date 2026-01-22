"""Add is_lead and lead_tag columns to reddit_posts

Revision ID: 63df3406803b
Revises: a1b2c3d4e5f6
Create Date: 2025-09-11 17:32:51.049512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63df3406803b'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_lead column (boolean, default False)
    op.add_column('reddit_posts', sa.Column('is_lead', sa.Boolean(), nullable=False, default=False, server_default='0'))
    
    # Add lead_tag column (string, default NULL)
    op.add_column('reddit_posts', sa.Column('lead_tag', sa.String(), nullable=True, default=None))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added columns
    op.drop_column('reddit_posts', 'lead_tag')
    op.drop_column('reddit_posts', 'is_lead')
